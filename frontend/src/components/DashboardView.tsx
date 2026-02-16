'use client'

import React, { useState, useEffect, useMemo } from 'react'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'
import { UsageGraph } from '@/components/UsageGraph'
import { useUsageData } from '@/components/hooks/useUsageData'
import { useUnits } from '@/components/hooks/useUnits'
import { useOrgs } from '@/components/hooks/useOrgs'
import { Unit } from '@/components/types'
import { Folder, ChevronRight, ChevronDown, Monitor, Layout, Server, Database, Package, ExternalLink, Activity, Globe, Clock, AlertCircle, CheckCircle2, Download, Trash2, Edit, Save, X } from 'lucide-react'
import Link from 'next/link'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

interface DashboardViewProps {
    orgId?: string
}

export default function DashboardView({ orgId: propOrgId }: DashboardViewProps) {
    // Internal navigation state
    const [viewOrgId, setViewOrgId] = useState<string | null>(propOrgId || null)

    const { orgs } = useOrgs()
    const { data: usageData, loading, error, refetch, setSelectedUnitId } = useUsageData(viewOrgId || undefined)
    const { units, loading: unitsLoading, refetchUnits } = useUnits(viewOrgId || undefined)
    const [selectedUnit, setSelectedUnit] = useState<Unit | null>(null)
    const [expandedOrgs, setExpandedOrgs] = useState<Record<string, boolean>>({})
    const [origin, setOrigin] = useState('')

    // Edit State
    const [editingUnitId, setEditingUnitId] = useState<string | null>(null)
    const [editForm, setEditForm] = useState({ comp_id: '', org_id: '' })

    useEffect(() => {
        if (typeof window !== 'undefined') {
            setOrigin(window.location.origin)
        }
    }, [])

    const toggleOrg = (orgId: string) => {
        setExpandedOrgs(prev => ({ ...prev, [orgId]: !prev[orgId] }))
    }

    // Navigation Helper
    const navigateToOrg = (orgId: string | null) => {
        // If we are in "Shareable Link Mode" (propOrgId is set), we cannot go back to global
        if (propOrgId) return

        setViewOrgId(orgId)
        setSelectedUnit(null)
        setSelectedUnitId(null)
    }

    // Export Helper
    const downloadData = (range: string) => {
        if (!selectedUnit) return
        const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'}/api/units/${selectedUnit.id}/export?range=${range}`
        window.open(url, '_blank')
    }

    // Deployment Helper
    const downloadClient = () => {
        const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'}/api/deploy/generate`
        window.open(url, '_blank')
    }

    // Management Handlers
    const handleDeleteUnit = async (unitId: string, e: React.MouseEvent) => {
        e.stopPropagation()
        if (!confirm('Are you sure you want to delete this unit? This action cannot be undone.')) return

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'}/api/units/${unitId}`, {
                method: 'DELETE'
            })
            if (res.ok) {
                refetchUnits() // Reload list
                if (selectedUnit?.id === unitId) {
                    setSelectedUnit(null)
                    setSelectedUnitId(null)
                }
            } else {
                alert('Failed to delete unit')
            }
        } catch (error) {
            console.error('Delete failed:', error)
            alert('Error deleting unit')
        }
    }

    const startEditing = (unit: Unit, e: React.MouseEvent) => {
        e.stopPropagation()
        setEditingUnitId(unit.id)
        setEditForm({ comp_id: unit.comp_id || '', org_id: unit.org_id || '' })
    }

    const cancelEditing = (e: React.MouseEvent) => {
        e.stopPropagation()
        setEditingUnitId(null)
    }

    const saveEdit = async (unitId: string, e: React.MouseEvent) => {
        e.stopPropagation()
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'}/api/units/${unitId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(editForm)
            })
            if (res.ok) {
                setEditingUnitId(null)
                refetchUnits()
            } else {
                alert('Failed to update unit')
            }
        } catch (error) {
            console.error('Update failed:', error)
            alert('Error updating unit')
        }
    }
    // Robust Local Time Formatting
    const formatTimestamp = (timestamp: string) => {
        if (!timestamp) return 'N/A'
        try {
            const isoString = timestamp.endsWith('Z') ? timestamp : timestamp + 'Z'
            const date = new Date(isoString)
            if (isNaN(date.getTime())) return 'Inv. Date'
            return date.toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            })
        } catch {
            return 'Error'
        }
    }

    const formatLastSeen = (timestamp: string) => {
        try {
            const date = new Date(timestamp)
            const now = new Date()
            const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

            if (diffInSeconds < 60) return 'Just now'
            if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
            if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
            return date.toLocaleDateString()
        } catch {
            return 'Unknown'
        }
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-900 flex">
                <div className="w-64 bg-slate-800 border-r border-slate-700"></div>
                <div className="flex-1 ml-64 flex items-center justify-center">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent mx-auto mb-3"></div>
                        <p className="text-slate-400 text-sm">Loading system data</p>
                    </div>
                </div>
            </div>
        )
    }

    const currentData = usageData.length > 0 ? usageData[usageData.length - 1] : null

    // Stats for sidebar and views
    const activeUnitsCount = units.filter(u => u.status === 'online').length
    const activeOrgsCount = Array.from(new Set(units.filter(u => u.status === 'online').map(u => u.org_id))).length

    return (
        <div className="min-h-screen bg-slate-900 flex transition-all duration-500 font-sans">
            {/* Left Sidebar - Fixed */}
            <div className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col fixed h-screen z-20">

                {/* 📦 HIDE SHIPPING LINK in Shareable Mode */}
                {!propOrgId && (
                    <div className="p-3 bg-blue-600/10 border-b border-blue-500/20">
                        <Link
                            href="/deployment"
                            className="flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-[10px] font-bold text-white transition-all uppercase tracking-widest shadow-lg shadow-blue-500/20 group"
                        >
                            <Package className="w-4 h-4 group-hover:scale-110 transition-transform" />
                            Shipping Guide
                            <ExternalLink className="w-3 h-3 opacity-70" />
                        </Link>
                    </div>
                )}

                {/* Sidebar Header */}
                <div className="p-6 border-b border-slate-700 bg-slate-800/50">
                    <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/10">
                            <Server className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h1 className="text-lg font-black text-white tracking-tighter uppercase">{viewOrgId ? viewOrgId : 'Main Hub'}</h1>
                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Sys_Logger v2.0</p>
                        </div>
                    </div>
                </div>

                {/* Navigation */}
                <div className="p-4 border-b border-slate-700 flex-1 overflow-y-auto custom-scrollbar">
                    {/* Show Global Fleet Button ONLY if not in Shareable Mode */}
                    {!propOrgId && (
                        <button
                            onClick={() => navigateToOrg(null)}
                            className={`w-full px-4 py-3 rounded-lg transition-all text-left flex items-center space-x-3 mb-6 ${viewOrgId === null && selectedUnit === null
                                ? 'bg-blue-600 shadow-xl shadow-blue-500/30 text-white'
                                : 'text-slate-400 hover:bg-slate-700/50 hover:text-slate-200'
                                }`}
                        >
                            <Globe className="w-5 h-5" />
                            <span className="font-bold tracking-tight text-sm">Global Fleet</span>
                        </button>
                    )}

                    <div className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-4 px-2">Folders</div>
                    <div className="space-y-1.5">
                        {orgs.map(org => {
                            // If in Shareable Mode, only show the relevant org
                            if (propOrgId && org !== propOrgId) return null

                            const orgUnits = units.filter(u => u.org_id === org)
                            const isSelected = viewOrgId === org && selectedUnit === null
                            const isExpanded = expandedOrgs[org] || viewOrgId === org

                            return (
                                <div key={org} className="group-nav">
                                    <div className="flex items-center mb-1">
                                        <button
                                            onClick={() => navigateToOrg(org)}
                                            className={`flex-1 flex items-center gap-2.5 px-3 py-2 text-sm rounded-lg transition-all group ${isSelected ? 'bg-slate-700 text-blue-400 font-bold' : 'text-slate-300 hover:text-white hover:bg-slate-700/40'}`}
                                        >
                                            <Folder className={`w-4 h-4 ${isSelected || isExpanded ? 'text-blue-400 fill-blue-400/10' : 'text-slate-500'}`} />
                                            <span className="truncate uppercase tracking-tight">{org}</span>
                                        </button>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); toggleOrg(org); }}
                                            className="p-2 text-slate-600 hover:text-slate-400 transition-colors"
                                        >
                                            {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                                        </button>
                                    </div>

                                    {isExpanded && (
                                        <div className="ml-4 mt-1 space-y-1 border-l border-slate-700/50 animate-in fade-in slide-in-from-left-1 duration-200">
                                            {orgUnits.length === 0 ? (
                                                <div className="px-5 py-2 text-[10px] text-slate-600 italic font-medium">No active nodes</div>
                                            ) : (
                                                orgUnits.map(unit => (
                                                    <button
                                                        key={unit.id}
                                                        onClick={() => {
                                                            setSelectedUnitId(unit.id)
                                                            setSelectedUnit(unit)
                                                        }}
                                                        className={`w-full flex items-center gap-2.5 px-4 py-2 text-xs transition-all ${selectedUnit?.id === unit.id ? 'text-white font-black bg-blue-600/20 border-r-2 border-blue-500' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/20'}`}
                                                    >
                                                        <div className={`w-1.5 h-1.5 rounded-full ${unit.status === 'online' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]' : 'bg-red-500'}`} />
                                                        <span className="truncate font-mono">{unit.comp_id}</span>
                                                    </button>
                                                ))
                                            )}
                                        </div>
                                    )}
                                </div>
                            )
                        })}
                    </div>
                </div>

                {/* Status Footer */}
                <div className="p-4 bg-slate-900/30 border-t border-slate-700">
                    <div className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-4">Fleet Health</div>
                    <div className="grid grid-cols-2 gap-3">
                        <div className="bg-slate-800/80 rounded-xl p-3 border border-slate-700 shadow-inner">
                            <div className="text-[9px] text-slate-500 font-bold uppercase mb-1">Active Orgs</div>
                            <div className="text-xl font-black text-white">{activeOrgsCount}</div>
                        </div>
                        <div className="bg-slate-800/80 rounded-xl p-3 border border-slate-700 shadow-inner">
                            <div className="text-[9px] text-slate-500 font-bold uppercase mb-1">Online Units</div>
                            <div className="text-xl font-black text-green-500">{activeUnitsCount}</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 ml-64 overflow-y-auto min-h-screen flex flex-col bg-slate-900/50">
                {/* Header Bar */}
                <div className="bg-slate-800 border-b border-slate-700 sticky top-0 z-10 backdrop-blur-xl bg-opacity-80">
                    <div className="px-6 py-4 flex justify-between items-center">
                        <div className="flex items-center gap-4">
                            {!viewOrgId && !selectedUnit ? (
                                <h2 className="text-lg font-black text-white flex items-center gap-2 uppercase tracking-tighter">
                                    <Globe className="w-5 h-5 text-blue-500" />
                                    Infrastructure Overview
                                </h2>
                            ) : (
                                <div className="flex items-center gap-2 text-xs font-bold">
                                    {/* Hide Global Breadcrumb if in Shareable Mode */}
                                    {!propOrgId && (
                                        <>
                                            <button
                                                onClick={() => navigateToOrg(null)}
                                                className="text-slate-500 hover:text-blue-400 transition-colors uppercase"
                                            >
                                                Global
                                            </button>
                                            <ChevronRight className="w-3.5 h-3.5 text-slate-700" />
                                        </>
                                    )}

                                    <button
                                        onClick={() => navigateToOrg(viewOrgId)}
                                        className={`uppercase ${!selectedUnit ? 'text-blue-400' : 'text-slate-500 hover:text-blue-400'} transition-colors`}
                                    >
                                        {viewOrgId}
                                    </button>
                                    {selectedUnit && (
                                        <>
                                            <ChevronRight className="w-3.5 h-3.5 text-slate-700" />
                                            <span className="text-white font-mono bg-slate-700 px-2 py-0.5 rounded">{selectedUnit.comp_id}</span>
                                        </>
                                    )}
                                </div>
                            )}
                        </div>

                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-3 px-4 py-1.5 bg-slate-900/80 rounded-full border border-slate-700/50 shadow-inner">
                                <Activity className={`w-3.5 h-3.5 ${currentData ? 'text-green-500 animate-pulse' : 'text-slate-600'}`} />
                                <span className="text-[10px] text-slate-400 font-mono font-bold tracking-tight">
                                    SYNC: {formatTimestamp(currentData?.timestamp || '')}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="max-w-7xl mx-auto px-6 py-8 w-full transition-opacity duration-300">

                    {/* VIEW 1: GLOBAL LANDING SCREEN */}
                    {!viewOrgId && !selectedUnit && !propOrgId && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-700">
                            {/* SHIP CLIENT BUTTON */}
                            <div className="flex justify-end mb-4">
                                <button
                                    onClick={downloadClient}
                                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-blue-500/20"
                                >
                                    <Download className="w-4 h-4" />
                                    Ship Client Payload
                                </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {orgs.map(org => {
                                    const orgUnits = units.filter(u => u.org_id === org)
                                    const onlineCount = orgUnits.filter(u => u.status === 'online').length
                                    return (
                                        <div
                                            key={org}
                                            onClick={() => navigateToOrg(org)}
                                            className="bg-slate-800/40 border border-slate-700/80 rounded-3xl p-8 hover:border-blue-500/50 hover:bg-slate-800/60 transition-all group cursor-pointer relative overflow-hidden shadow-2xl hover:shadow-blue-500/5"
                                        >
                                            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 blur-3xl -mr-16 -mt-16 group-hover:bg-blue-500/10 transition-colors" />
                                            <div className="flex justify-between items-start mb-8">
                                                <div className="p-4 bg-blue-500/10 rounded-2xl group-hover:scale-110 transition-transform duration-500">
                                                    <Folder className="w-8 h-8 text-blue-500 fill-blue-500/10" />
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-[10px] font-black text-slate-500 mb-1.5 uppercase tracking-widest">Live Nodes</div>
                                                    <span className={`text-[11px] px-3 py-1 rounded-full font-black tracking-tighter ${onlineCount > 0 ? 'bg-green-500/10 text-green-500 border border-green-500/20' : 'bg-slate-800 text-slate-500 border border-slate-700'}`}>
                                                        {onlineCount}/{orgUnits.length} ONLINE
                                                    </span>
                                                </div>
                                            </div>
                                            <h3 className="text-2xl font-black text-white mb-1 group-hover:text-blue-400 transition-colors uppercase tracking-tighter">{org}</h3>
                                            <p className="text-[10px] text-slate-500 mb-8 font-black tracking-[0.2em] uppercase opacity-60">Fleet Cluster ID: {org.slice(0, 3)}-PROD</p>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    )}

                    {/* VIEW 2: ORGANIZATION DASHBOARD (STATUS OVERVIEW) */}
                    {viewOrgId && !selectedUnit && (
                        <div className="space-y-8 animate-in zoom-in-95 duration-500">
                            {/* Organization Health Stats */}
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                                <div className="bg-slate-800/40 border border-slate-700/80 rounded-2xl p-6 relative overflow-hidden">
                                    <div className="absolute top-0 right-0 w-24 h-24 bg-green-500/5 blur-2xl -mr-8 -mt-8" />
                                    <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Cluster Status</h3>
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
                                        <span className="text-2xl font-black text-white">ONLINE</span>
                                    </div>
                                </div>

                                <div className="bg-slate-800/40 border border-slate-700/80 rounded-2xl p-6 relative overflow-hidden">
                                    <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Active Nodes</h3>
                                    <div className="text-3xl font-black text-white">
                                        {units.filter(u => u.status === 'online').length} / {units.length}
                                    </div>
                                </div>

                                {/* HIDE Shareable Link CARD in Shareable Mode, but SHOW in Admin Mode */}
                                {!propOrgId && (
                                    <div className="bg-slate-800/40 border border-slate-700/80 rounded-2xl p-6 relative overflow-hidden">
                                        <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Shareable Dashboard</h3>
                                        <div className="flex flex-col gap-2">
                                            <div className="text-[10px] font-mono text-blue-400 truncate bg-blue-500/10 p-1.5 rounded border border-blue-500/20 select-all">
                                                {origin}/org/{viewOrgId}/dashboard
                                            </div>
                                            <Link
                                                href={`/org/${viewOrgId}/dashboard`}
                                                target="_blank"
                                                className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 hover:text-white transition-colors"
                                            >
                                                <ExternalLink className="w-3 h-3" /> Open Direct Link
                                            </Link>
                                        </div>
                                    </div>
                                )}

                                {/* Fill space if no shareable link card */}
                                {propOrgId && (
                                    <div className="bg-slate-800/40 border border-slate-700/80 rounded-2xl p-6 relative overflow-hidden">
                                        <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Sync Frequency</h3>
                                        <div className="text-3xl font-black text-blue-400">1s</div>
                                        <div className="text-[10px] text-slate-500 mt-1">Real-time Encrypted</div>
                                    </div>
                                )}

                                <div className="bg-slate-800/40 border border-slate-700/80 rounded-2xl p-6 relative overflow-hidden">
                                    <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Active Alerts</h3>
                                    <div className="text-3xl font-black text-blue-400">0</div>
                                    <div className="text-[10px] text-slate-500 mt-1">System Healthy</div>
                                </div>
                            </div>

                            {/* Node Table */}
                            <div className="bg-slate-800/40 border border-slate-700/80 rounded-3xl overflow-hidden backdrop-blur-sm">
                                <div className="px-8 py-6 border-b border-slate-700/50 flex items-center justify-between">
                                    <h3 className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-2">
                                        <Server className="w-4 h-4 text-blue-500" />
                                        Connected Nodes
                                    </h3>
                                    <span className="text-xs font-bold text-slate-500 bg-slate-900/50 px-3 py-1 rounded-full">{units.length} Total</span>
                                </div>
                                <div className="p-2">
                                    <table className="w-full text-left border-collapse">
                                        <thead>
                                            <tr className="text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-slate-700/50">
                                                <th className="px-6 py-4">Node ID</th>
                                                <th className="px-6 py-4">Status</th>
                                                <th className="px-6 py-4">Last Pulse</th>
                                                <th className="px-6 py-4 text-right">Action</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {units.map((unit) => (
                                                <tr
                                                    key={unit.id}
                                                    onClick={() => {
                                                        if (editingUnitId === unit.id) return
                                                        setSelectedUnitId(unit.id)
                                                        setSelectedUnit(unit)
                                                    }}
                                                    className={`group hover:bg-slate-700/30 transition-colors cursor-pointer border-b border-slate-800/50 last:border-0 ${editingUnitId === unit.id ? 'bg-slate-700/40' : ''}`}
                                                >
                                                    <td className="px-6 py-4">
                                                        <div className="flex items-center gap-3">
                                                            <Monitor className={`w-4 h-4 ${unit.status === 'online' ? 'text-slate-300' : 'text-slate-600'}`} />
                                                            {editingUnitId === unit.id ? (
                                                                <div className="flex flex-col gap-1" onClick={e => e.stopPropagation()}>
                                                                    <input
                                                                        type="text"
                                                                        value={editForm.comp_id}
                                                                        onChange={e => setEditForm({ ...editForm, comp_id: e.target.value })}
                                                                        className="bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs text-white focus:border-blue-500 outline-none font-mono"
                                                                        placeholder="Hostname"
                                                                    />
                                                                    <input
                                                                        type="text"
                                                                        value={editForm.org_id}
                                                                        onChange={e => setEditForm({ ...editForm, org_id: e.target.value })}
                                                                        className="bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs text-slate-400 focus:border-blue-500 outline-none"
                                                                        placeholder="Organization"
                                                                    />
                                                                </div>
                                                            ) : (
                                                                <span className="font-bold text-sm text-white font-mono">{unit.comp_id}</span>
                                                            )}
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <div className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wide border ${unit.status === 'online'
                                                            ? 'bg-green-500/10 text-green-500 border-green-500/20'
                                                            : 'bg-red-500/10 text-red-500 border-red-500/20'
                                                            }`}>
                                                            {unit.status === 'online' ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                                                            {unit.status}
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <div className="flex items-center gap-2 text-xs font-medium text-slate-400">
                                                            <Clock className="w-3.5 h-3.5" />
                                                            {formatLastSeen(unit.last_seen)}
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 text-right">
                                                        {editingUnitId === unit.id ? (
                                                            <div className="flex items-center justify-end gap-2">
                                                                <button onClick={(e) => saveEdit(unit.id, e)} className="p-1.5 bg-green-500/10 text-green-500 rounded hover:bg-green-500/20 transition-colors">
                                                                    <Save className="w-4 h-4" />
                                                                </button>
                                                                <button onClick={cancelEditing} className="p-1.5 bg-slate-700 text-slate-400 rounded hover:bg-slate-600 transition-colors">
                                                                    <X className="w-4 h-4" />
                                                                </button>
                                                            </div>
                                                        ) : (
                                                            <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                {!propOrgId && (
                                                                    <>
                                                                        <button onClick={(e) => startEditing(unit, e)} className="p-1.5 hover:bg-blue-500/10 text-slate-500 hover:text-blue-400 rounded transition-colors">
                                                                            <Edit className="w-4 h-4" />
                                                                        </button>
                                                                        <button onClick={(e) => handleDeleteUnit(unit.id, e)} className="p-1.5 hover:bg-red-500/10 text-slate-500 hover:text-red-400 rounded transition-colors">
                                                                            <Trash2 className="w-4 h-4" />
                                                                        </button>
                                                                    </>
                                                                )}
                                                                <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-blue-400 group-hover:translate-x-1 transition-all inline-block" />
                                                            </div>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                            {units.length === 0 && (
                                                <tr>
                                                    <td colSpan={4} className="px-6 py-12 text-center text-slate-500 font-medium text-sm italic">
                                                        No nodes connected to this organization cluster.
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* VIEW 3: UNIT DETAIL DASHBOARD (GRAPHS) */}
                    {selectedUnit && (
                        <div className="space-y-6 animate-in zoom-in-95 duration-500">
                            {/* Header Stats Bar */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <div className="bg-slate-800/40 border border-slate-700/80 rounded-2xl p-6 flex items-center justify-between group hover:border-red-500/30 transition-all">
                                    <div>
                                        <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">CPU Power</div>
                                        <div className="text-3xl font-black text-white">{currentData ? currentData.cpu.toFixed(1) : '0.0'}%</div>
                                    </div>
                                    <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center group-hover:bg-red-500/20 transition-colors">
                                        <Activity className="w-6 h-6 text-red-500" />
                                    </div>
                                </div>
                                <div className="bg-slate-800/40 border border-slate-700/80 rounded-2xl p-6 flex items-center justify-between group hover:border-green-500/30 transition-all">
                                    <div>
                                        <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">GPU Compute</div>
                                        <div className="text-3xl font-black text-white">{currentData ? (currentData.gpu_load || 0).toFixed(1) : '0.0'}%</div>
                                    </div>
                                    <div className="w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center group-hover:bg-green-500/20 transition-colors">
                                        <Activity className="w-6 h-6 text-green-500" />
                                    </div>
                                </div>
                                <div className="bg-slate-800/40 border border-slate-700/80 rounded-2xl p-6 flex items-center justify-between group hover:border-blue-500/30 transition-all">
                                    <div>
                                        <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Memory Cache</div>
                                        <div className="text-3xl font-black text-white">{currentData ? currentData.ram.toFixed(1) : '0.0'}%</div>
                                    </div>
                                    <div className="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center group-hover:bg-blue-500/20 transition-colors">
                                        <Activity className="w-6 h-6 text-blue-500" />
                                    </div>
                                </div>
                            </div>

                            {/* DATA EXPORT SECTION - ONLY IN GLOBAL MODE */}
                            {!propOrgId && (
                                <div className="bg-slate-800/40 border border-slate-700/80 rounded-2xl p-6 flex items-center justify-between backdrop-blur-sm">
                                    <div className="flex items-center gap-4">
                                        <div className="p-3 bg-blue-500/10 rounded-xl">
                                            <Download className="w-6 h-6 text-blue-500" />
                                        </div>
                                        <div>
                                            <h3 className="text-sm font-black text-white uppercase tracking-wider">Export Usage Data</h3>
                                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Download historical CSV reports</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        {['1d', '5d', '10d', 'all'].map(range => (
                                            <button
                                                key={range}
                                                onClick={() => downloadData(range)}
                                                className="px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs font-bold text-slate-400 hover:text-white hover:bg-slate-700/80 hover:border-slate-500 transition-all uppercase"
                                            >
                                                {range === 'all' ? 'All Time' : range.toUpperCase()}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="grid grid-cols-1 gap-6">
                                <div className="bg-slate-800/40 border border-slate-700/80 rounded-3xl p-8 backdrop-blur-sm">
                                    <div className="flex items-center justify-between mb-8">
                                        <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.3em] flex items-center gap-3">
                                            <div className="w-1 h-6 bg-red-500 rounded-full" /> Load Timeline (Real-time)
                                        </h3>
                                    </div>
                                    <UsageGraph data={usageData} metric="cpu" loading={loading} error={error} onRetry={refetch} timeRange="1m" />
                                </div>

                                <div className="bg-slate-800/40 border border-slate-700/80 rounded-3xl p-8 backdrop-blur-sm">
                                    <div className="flex items-center justify-between mb-8">
                                        <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.3em] flex items-center gap-3">
                                            <div className="w-1 h-6 bg-green-500 rounded-full" /> Graphics Pipeline
                                        </h3>
                                    </div>
                                    <UsageGraph data={usageData} metric="gpu" loading={loading} error={error} onRetry={refetch} timeRange="1m" />
                                </div>

                                <div className="bg-slate-800/40 border border-slate-700/80 rounded-3xl p-8 backdrop-blur-sm">
                                    <div className="flex items-center justify-between mb-8">
                                        <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.3em] flex items-center gap-3">
                                            <div className="w-1 h-6 bg-blue-500 rounded-full" /> Memory Allocation
                                        </h3>
                                    </div>
                                    <UsageGraph data={usageData} metric="ram" loading={loading} error={error} onRetry={refetch} timeRange="1m" />
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
