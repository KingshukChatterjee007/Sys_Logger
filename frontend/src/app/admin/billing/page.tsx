'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../../components/AuthContext'
import { apiFetch } from '../../components/hooks/apiUtils'
import Link from 'next/link'
import {
    CreditCard, ArrowLeft, Building2, TrendingUp,
    Clock, AlertCircle, CheckCircle, Shield
} from 'lucide-react'

interface BillingData {
    role: string
    active_subscriptions: number
    total_orgs: number
    upcoming_payments: number
    upcoming_payment_orgs: any[]
    all_orgs: any[]
    tiers: Record<string, { name: string; max_nodes: number; price_label: string }>
}

export default function AdminBillingPage() {
    const { user, isAdmin } = useAuth()
    const [data, setData] = useState<BillingData | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchBilling = async () => {
            try {
                const res = await apiFetch('/api/billing/info')
                if (res.ok) setData(await res.json())
            } catch (err) {
                console.error('Failed to fetch billing:', err)
            } finally {
                setLoading(false)
            }
        }
        fetchBilling()
    }, [])

    if (!isAdmin) {
        return <div className="min-h-screen flex items-center justify-center bg-[#FAFAFA]"><p className="text-zinc-500 font-bold">Access Denied.</p></div>
    }

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-zinc-900 font-sans p-4 lg:p-8">
            <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
                <div className="absolute top-[-20%] left-[-10%] w-[70%] h-[60%] bg-orange-500/5 blur-[140px] rounded-full" />
            </div>

            <header className="bg-white ring-1 ring-zinc-200/50 shadow-sm rounded-2xl px-6 py-4 flex justify-between items-center mb-6 relative z-10">
                <div className="flex items-center gap-4">
                    <Link href="/admin" className="p-2.5 bg-zinc-100 hover:bg-orange-50 text-zinc-600 hover:text-orange-600 rounded-xl transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div>
                        <h1 className="text-xl font-black tracking-tight uppercase">Billing Overview</h1>
                        <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Admin Panel</p>
                    </div>
                </div>
            </header>

            <div className="relative z-10 space-y-6">
                {loading ? (
                    <div className="flex items-center justify-center p-16">
                        <div className="w-8 h-8 border-2 border-zinc-200 border-t-orange-500 rounded-full animate-spin" />
                    </div>
                ) : data && (
                    <>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl ring-1 ring-zinc-200/80 shadow-sm p-6">
                                <div className="flex items-center gap-2 mb-3">
                                    <CheckCircle className="w-5 h-5 text-emerald-500" />
                                    <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Active Subs</span>
                                </div>
                                <p className="text-3xl font-black font-mono">{data.active_subscriptions}</p>
                            </motion.div>
                            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-white rounded-2xl ring-1 ring-zinc-200/80 shadow-sm p-6">
                                <div className="flex items-center gap-2 mb-3">
                                    <Clock className="w-5 h-5 text-orange-500" />
                                    <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Due in 7 days</span>
                                </div>
                                <p className="text-3xl font-black font-mono">{data.upcoming_payments}</p>
                            </motion.div>
                            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-white rounded-2xl ring-1 ring-zinc-200/80 shadow-sm p-6">
                                <div className="flex items-center gap-2 mb-3">
                                    <Building2 className="w-5 h-5 text-zinc-500" />
                                    <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Total Orgs</span>
                                </div>
                                <p className="text-3xl font-black font-mono">{data.total_orgs}</p>
                            </motion.div>
                        </div>

                        {/* Upcoming Payments Alert */}
                        {data.upcoming_payment_orgs.length > 0 && (
                            <div className="bg-orange-50 rounded-2xl ring-1 ring-orange-200/50 p-6">
                                <div className="flex items-center gap-2 mb-3">
                                    <AlertCircle className="w-5 h-5 text-orange-500" />
                                    <span className="text-sm font-black text-orange-700 uppercase tracking-wider">Upcoming Payments</span>
                                </div>
                                <div className="space-y-2">
                                    {data.upcoming_payment_orgs.map((o: any) => (
                                        <div key={o.org_id} className="flex justify-between items-center bg-white rounded-xl p-3 ring-1 ring-orange-100">
                                            <span className="font-bold text-sm">{o.name} <span className="text-zinc-400">({o.slug})</span></span>
                                            <span className="text-sm font-mono font-bold text-orange-600">{o.next_payment_date}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* All Orgs Billing */}
                        <div className="bg-white rounded-2xl ring-1 ring-zinc-200/80 shadow-sm p-6">
                            <h3 className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em] mb-4">All Organizations</h3>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-zinc-100">
                                            <th className="text-left py-3 px-2 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Org</th>
                                            <th className="text-left py-3 px-2 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Tier</th>
                                            <th className="text-center py-3 px-2 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Node Limit</th>
                                            <th className="text-left py-3 px-2 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Next Payment</th>
                                            <th className="text-center py-3 px-2 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.all_orgs.map((o: any) => (
                                            <tr key={o.org_id} className="border-b border-zinc-50 hover:bg-zinc-50/50">
                                                <td className="py-3 px-2 font-bold">{o.name}</td>
                                                <td className="py-3 px-2">
                                                    <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${o.tier === 'business' ? 'bg-orange-50 text-orange-600 ring-1 ring-orange-200/50' : 'bg-zinc-100 text-zinc-600 ring-1 ring-zinc-200'}`}>
                                                        {o.tier}
                                                    </span>
                                                </td>
                                                <td className="py-3 px-2 text-center font-mono font-bold">{o.node_limit}</td>
                                                <td className="py-3 px-2 font-mono text-xs text-zinc-500">{o.next_payment_date || '—'}</td>
                                                <td className="py-3 px-2 text-center">
                                                    <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${o.is_active ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'}`}>
                                                        {o.is_active ? 'Active' : 'Inactive'}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Tier Reference */}
                        <div className="bg-white rounded-2xl ring-1 ring-zinc-200/80 shadow-sm p-6">
                            <h3 className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em] mb-4">Tier Reference</h3>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                {Object.entries(data.tiers).map(([key, tier]) => (
                                    <div key={key} className="bg-zinc-50 rounded-xl p-4 ring-1 ring-zinc-100">
                                        <h4 className="font-black text-sm uppercase mb-1">{tier.name}</h4>
                                        <p className="text-[10px] text-zinc-500 font-bold">Default Nodes: {tier.max_nodes} • {tier.price_label}</p>
                                        {key === 'business' && (
                                            <p className="text-[10px] text-orange-500 font-bold mt-1">+ Additional nodes available at extra cost</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}
