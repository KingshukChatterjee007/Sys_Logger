'use client'

import React, { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuth } from '../components/AuthContext'
import { apiFetch } from '../components/hooks/apiUtils'
import DashboardView from '../DashboardView'
import Link from 'next/link'
import {
    Activity, Server, CreditCard, LogOut, Clock, Shield,
    Building2, ChevronRight, Layers
} from 'lucide-react'

export default function OrgDashboardPage() {
    const params = useParams()
    const orgSlug = params.orgSlug as string
    const { user, logout, isAdmin, isOrg } = useAuth()
    const [currentTime, setCurrentTime] = useState('')
    const [activeTab, setActiveTab] = useState<'dashboard' | 'nodes' | 'billing'>('dashboard')

    useEffect(() => {
        const interval = setInterval(() => setCurrentTime(new Date().toLocaleTimeString()), 1000)
        return () => clearInterval(interval)
    }, [])

    // Check access: admin can view any org, org user can only view their own
    const hasAccess = isAdmin || (isOrg && user?.org_slug === orgSlug)

    if (!hasAccess) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[#FAFAFA]">
                <div className="text-center">
                    <Shield className="w-12 h-12 text-zinc-300 mx-auto mb-3" />
                    <p className="text-zinc-500 font-bold">Access Denied</p>
                    <p className="text-xs text-zinc-400 mt-1">You don&apos;t have permission to view this organization.</p>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-zinc-900 font-sans flex flex-col">
            {/* Org Header */}
            <header className="bg-white ring-1 ring-zinc-200/50 shadow-sm px-4 lg:px-6 py-3 flex justify-between items-center z-20 shrink-0">
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-3">
                        {isAdmin && (
                            <Link href="/admin" className="p-2 bg-zinc-100 text-zinc-600 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors">
                                <ChevronRight className="w-4 h-4 rotate-180" />
                            </Link>
                        )}
                        <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center shadow-lg shadow-orange-500/20">
                            <Building2 className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h1 className="text-lg font-black tracking-tight uppercase">{orgSlug}</h1>
                            <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Organization Dashboard</p>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {/* Tab Buttons */}
                    <div className="hidden sm:flex bg-zinc-100/50 p-1 rounded-lg ring-1 ring-zinc-200/80">
                        <button onClick={() => setActiveTab('dashboard')} className={`px-3 lg:px-4 py-1.5 rounded-md text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'dashboard' ? 'bg-white text-orange-600 shadow-sm' : 'text-zinc-500 hover:text-zinc-800'}`}>
                            <span className="flex items-center gap-1.5"><Activity className="w-3.5 h-3.5" /> Dashboard</span>
                        </button>
                        <button onClick={() => setActiveTab('nodes')} className={`px-3 lg:px-4 py-1.5 rounded-md text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'nodes' ? 'bg-white text-orange-600 shadow-sm' : 'text-zinc-500 hover:text-zinc-800'}`}>
                            <span className="flex items-center gap-1.5"><Layers className="w-3.5 h-3.5" /> Nodes</span>
                        </button>
                        <button onClick={() => setActiveTab('billing')} className={`px-3 lg:px-4 py-1.5 rounded-md text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'billing' ? 'bg-white text-orange-600 shadow-sm' : 'text-zinc-500 hover:text-zinc-800'}`}>
                            <span className="flex items-center gap-1.5"><CreditCard className="w-3.5 h-3.5" /> Billing</span>
                        </button>
                    </div>

                    <div className="hidden lg:flex items-center gap-2 text-zinc-500 font-mono text-xs font-bold bg-zinc-50 px-3 py-1.5 rounded-lg ring-1 ring-zinc-200">
                        <Clock className="w-3.5 h-3.5" />
                        {currentTime}
                    </div>
                    <button onClick={logout} className="p-2 bg-zinc-50 hover:bg-red-50 text-zinc-400 hover:text-red-600 rounded-xl ring-1 ring-zinc-200 hover:ring-red-200 transition-all" title="Logout">
                        <LogOut className="w-4 h-4" />
                    </button>
                </div>
            </header>

            {/* Mobile Tabs */}
            <div className="sm:hidden flex bg-white ring-1 ring-zinc-200/50 shadow-sm px-2 py-1.5 gap-1">
                <button onClick={() => setActiveTab('dashboard')} className={`flex-1 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest ${activeTab === 'dashboard' ? 'bg-orange-50 text-orange-600' : 'text-zinc-500'}`}>Dashboard</button>
                <button onClick={() => setActiveTab('nodes')} className={`flex-1 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest ${activeTab === 'nodes' ? 'bg-orange-50 text-orange-600' : 'text-zinc-500'}`}>Nodes</button>
                <button onClick={() => setActiveTab('billing')} className={`flex-1 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest ${activeTab === 'billing' ? 'bg-orange-50 text-orange-600' : 'text-zinc-500'}`}>Billing</button>
            </div>

            {/* Tab Content */}
            <div className="flex-1 flex flex-col">
                {activeTab === 'dashboard' && (
                    <DashboardView orgId={orgSlug} />
                )}
                {activeTab === 'nodes' && (
                    <ManageNodesTab orgSlug={orgSlug} />
                )}
                {activeTab === 'billing' && (
                    <OrgBillingTab />
                )}
            </div>
        </div>
    )
}

// ============================================================
// MANAGE NODES TAB
// ============================================================
function ManageNodesTab({ orgSlug }: { orgSlug: string }) {
    const { user } = useAuth()
    const [nodes, setNodes] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [orgInfo, setOrgInfo] = useState<any>(null)
    const [showAddModal, setShowAddModal] = useState(false)
    const [newNodeName, setNewNodeName] = useState('')
    const [addError, setAddError] = useState('')
    const [addLoading, setAddLoading] = useState(false)
    const [downloadingNode, setDownloadingNode] = useState<string | null>(null)

    const fetchData = async () => {
        try {
            const [nodesRes, dashRes] = await Promise.all([
                apiFetch('/api/org/nodes'),
                apiFetch('/api/org/dashboard'),
            ])
            if (nodesRes.ok) setNodes(await nodesRes.json())
            if (dashRes.ok) {
                const d = await dashRes.json()
                setOrgInfo(d)
            }
        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { fetchData() }, [])

    const handleAddNode = async () => {
        if (!newNodeName.trim()) {
            setAddError('Node name is required')
            return
        }
        setAddError('')
        setAddLoading(true)
        try {
            const res = await apiFetch('/api/org/nodes/add', {
                method: 'POST',
                body: JSON.stringify({ comp_id: newNodeName.trim() }),
            })
            const data = await res.json()
            if (!res.ok) {
                setAddError(data.error || 'Failed to add node')
            } else {
                setShowAddModal(false)
                setNewNodeName('')
                fetchData()
            }
        } catch {
            setAddError('Network error')
        } finally {
            setAddLoading(false)
        }
    }

    const handleDownloadClient = async (node: any) => {
        setDownloadingNode(node.id)
        try {
            const res = await apiFetch('/api/org/download-client', {
                method: 'POST',
                body: JSON.stringify({
                    org_id: node.org_id,
                    comp_id: node.comp_id,
                    system_id: node.system_id,
                }),
            })
            if (res.ok) {
                const blob = await res.blob()
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `SysLogger_Client_${node.org_id}_${node.comp_id}.zip`
                document.body.appendChild(a)
                a.click()
                document.body.removeChild(a)
                URL.revokeObjectURL(url)
            }
        } catch {
            console.error('Download failed')
        } finally {
            setDownloadingNode(null)
        }
    }

    const nodeLimit = orgInfo?.node_limit || 0
    const canAddMore = nodes.length < nodeLimit

    return (
        <div className="p-4 lg:p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-black tracking-tight uppercase">Manage Nodes</h2>
                    <p className="text-xs text-zinc-500 font-bold mt-1">
                        {nodes.length} / {nodeLimit} nodes allocated
                        {orgInfo?.tier_info && <span className="ml-2 text-orange-500">({orgInfo.tier_info.name} Tier)</span>}
                    </p>
                </div>
                <button
                    onClick={() => setShowAddModal(true)}
                    disabled={!canAddMore}
                    className={`px-4 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest flex items-center gap-2 transition-all shadow-sm ${canAddMore
                        ? 'bg-zinc-900 hover:bg-zinc-800 text-white hover:shadow-md'
                        : 'bg-zinc-200 text-zinc-400 cursor-not-allowed'
                        }`}
                >
                    + Add Node
                </button>
            </div>

            {!canAddMore && nodes.length >= nodeLimit && (
                <div className="bg-orange-50 rounded-xl ring-1 ring-orange-200/50 p-4 text-sm">
                    <p className="font-bold text-orange-700">Node limit reached ({nodeLimit})</p>
                    <p className="text-orange-600 text-xs mt-1">Upgrade your tier or contact admin for additional nodes at extra cost.</p>
                </div>
            )}

            {/* Nodes List */}
            {loading ? (
                <div className="flex items-center justify-center p-16">
                    <div className="w-8 h-8 border-2 border-zinc-200 border-t-orange-500 rounded-full animate-spin" />
                </div>
            ) : nodes.length === 0 ? (
                <div className="bg-white rounded-2xl ring-1 ring-zinc-200/80 shadow-sm p-12 text-center">
                    <Server className="w-12 h-12 text-zinc-300 mx-auto mb-3" />
                    <p className="font-bold text-zinc-700">No nodes yet</p>
                    <p className="text-xs text-zinc-400 mt-1">Add your first node to get started with monitoring.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {nodes.map(node => (
                        <motion.div
                            key={node.id}
                            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                            className="bg-white rounded-2xl ring-1 ring-zinc-200/80 shadow-sm p-5"
                        >
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center gap-3">
                                    <div className={`p-2 rounded-xl ${node.status === 'online' ? 'bg-emerald-50 text-emerald-600' : 'bg-zinc-100 text-zinc-400'}`}>
                                        <Server className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h3 className="font-black text-sm uppercase">{node.comp_id || node.name}</h3>
                                        <p className="text-[10px] text-zinc-400 font-mono">{node.id}</p>
                                    </div>
                                </div>
                                <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${node.status === 'online' ? 'bg-emerald-50 text-emerald-600 ring-1 ring-emerald-200/50' : 'bg-zinc-100 text-zinc-500 ring-1 ring-zinc-200'}`}>
                                    {node.status}
                                </span>
                            </div>
                            <div className="flex items-center gap-4 text-xs text-zinc-500 font-bold mb-4">
                                <span>IP: {node.ip || '—'}</span>
                                <span>OS: {node.os_info || '—'}</span>
                            </div>
                            <button
                                onClick={() => handleDownloadClient(node)}
                                disabled={downloadingNode === node.id}
                                className="w-full bg-zinc-50 hover:bg-orange-50 text-zinc-600 hover:text-orange-600 rounded-xl py-2.5 text-[10px] font-black uppercase tracking-widest ring-1 ring-zinc-200 hover:ring-orange-200 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {downloadingNode === node.id ? (
                                    <div className="w-3.5 h-3.5 border-2 border-zinc-300 border-t-orange-500 rounded-full animate-spin" />
                                ) : '📦'} Download Client Installer
                            </button>
                        </motion.div>
                    ))}
                </div>
            )}

            {/* Add Node Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-zinc-900/30 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setShowAddModal(false)}>
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                        className="bg-white rounded-2xl ring-1 ring-zinc-200 shadow-xl p-6 w-full max-w-md"
                        onClick={e => e.stopPropagation()}
                    >
                        <h3 className="text-lg font-black tracking-tight uppercase mb-4">Add New Node</h3>
                        <p className="text-xs text-zinc-500 mb-4">Enter a name for this node (e.g., computer hostname or label). This will be used as the Computer ID in the client installer.</p>
                        {addError && (
                            <div className="bg-red-50 text-red-600 rounded-xl px-4 py-2.5 mb-4 text-sm font-bold ring-1 ring-red-200/50">
                                {addError}
                            </div>
                        )}
                        <input
                            type="text"
                            value={newNodeName}
                            onChange={e => setNewNodeName(e.target.value)}
                            placeholder="e.g., LAB-PC-01"
                            className="w-full bg-zinc-50 ring-1 ring-zinc-200 rounded-xl px-4 py-3 text-sm font-bold text-zinc-800 focus:ring-orange-500 outline-none transition-all mb-4"
                            onKeyDown={e => e.key === 'Enter' && handleAddNode()}
                            autoFocus
                        />
                        <div className="flex gap-3">
                            <button onClick={handleAddNode} disabled={addLoading} className="flex-1 bg-zinc-900 hover:bg-zinc-800 text-white rounded-xl py-3 text-xs font-black uppercase tracking-widest transition-all disabled:opacity-50">
                                {addLoading ? 'Adding...' : 'Create Node'}
                            </button>
                            <button onClick={() => setShowAddModal(false)} className="px-6 bg-zinc-100 hover:bg-zinc-200 text-zinc-600 rounded-xl py-3 text-xs font-black uppercase tracking-widest transition-colors">
                                Cancel
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}
        </div>
    )
}

// ============================================================
// ORG BILLING TAB
// ============================================================
function OrgBillingTab() {
    const [data, setData] = useState<any>(null)
    const [loading, setLoading] = useState(true)
    const [switching, setSwitching] = useState(false)

    useEffect(() => {
        const fetchBilling = async () => {
            try {
                const res = await apiFetch('/api/billing/info')
                if (res.ok) setData(await res.json())
            } catch (err) {
                console.error(err)
            } finally {
                setLoading(false)
            }
        }
        fetchBilling()
    }, [])

    const handleSwitchTier = async (tier: string) => {
        if (!confirm(`Switch to ${tier} tier? This will adjust your node limit.`)) return
        setSwitching(true)
        try {
            const res = await apiFetch('/api/billing/switch-tier', {
                method: 'POST',
                body: JSON.stringify({ tier }),
            })
            if (res.ok) {
                // Refetch
                const billingRes = await apiFetch('/api/billing/info')
                if (billingRes.ok) setData(await billingRes.json())
            }
        } catch {
            console.error('Switch tier failed')
        } finally {
            setSwitching(false)
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center p-16">
                <div className="w-8 h-8 border-2 border-zinc-200 border-t-orange-500 rounded-full animate-spin" />
            </div>
        )
    }

    if (!data) return null
    const org = data.organization
    const tierInfo = data.tier_info

    return (
        <div className="p-4 lg:p-6 space-y-6">
            <h2 className="text-xl font-black tracking-tight uppercase">Billing & Subscription</h2>

            {/* Current Plan */}
            <div className="bg-white rounded-2xl ring-1 ring-zinc-200/80 shadow-sm p-6">
                <h3 className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em] mb-4">Current Plan</h3>
                <div className="flex items-center gap-4 mb-4">
                    <div className="p-3 rounded-xl bg-orange-50 text-orange-600">
                        <CreditCard className="w-6 h-6" />
                    </div>
                    <div>
                        <h4 className="text-xl font-black uppercase">{tierInfo?.name || org?.tier}</h4>
                        <p className="text-xs text-zinc-500 font-bold">{tierInfo?.price_label} • {org?.node_limit} nodes included</p>
                    </div>
                </div>

                {org?.next_payment_date && (
                    <div className="bg-orange-50 rounded-xl p-4 ring-1 ring-orange-200/50">
                        <p className="text-sm font-bold text-orange-700 flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            Next payment due: <span className="font-mono">{org.next_payment_date}</span>
                        </p>
                    </div>
                )}
            </div>

            {/* Switch Tier */}
            {data.tiers && (
                <div className="bg-white rounded-2xl ring-1 ring-zinc-200/80 shadow-sm p-6">
                    <h3 className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em] mb-4">Available Plans</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {Object.entries(data.tiers).map(([key, tier]: [string, any]) => {
                            const isCurrent = org?.tier === key
                            return (
                                <div key={key} className={`rounded-xl p-5 ring-1 transition-all ${isCurrent ? 'bg-orange-50 ring-orange-200' : 'bg-zinc-50 ring-zinc-200 hover:ring-zinc-300'}`}>
                                    <h4 className="font-black text-sm uppercase mb-1">{tier.name}</h4>
                                    <p className="text-[10px] text-zinc-500 font-bold mb-1">Default: {tier.max_nodes} nodes • {tier.price_label}</p>
                                    {key === 'business' && (
                                        <p className="text-[10px] text-orange-500 font-bold mb-3">Extra nodes available on request</p>
                                    )}
                                    {isCurrent ? (
                                        <span className="text-[10px] font-black text-orange-600 uppercase tracking-widest">✓ Current Plan</span>
                                    ) : (
                                        <button
                                            onClick={() => handleSwitchTier(key)}
                                            disabled={switching}
                                            className="mt-2 w-full bg-zinc-900 hover:bg-zinc-800 text-white rounded-lg py-2 text-[10px] font-black uppercase tracking-widest transition-all disabled:opacity-50"
                                        >
                                            Switch to {tier.name}
                                        </button>
                                    )}
                                </div>
                            )
                        })}
                    </div>
                    <p className="text-[10px] text-zinc-400 mt-4 font-bold">
                        💳 Razorpay payment integration coming soon. Contact admin for billing inquiries.
                    </p>
                </div>
            )}
        </div>
    )
}
