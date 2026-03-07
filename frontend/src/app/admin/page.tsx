'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../components/AuthContext'
import { apiFetch } from '../components/hooks/apiUtils'
import Link from 'next/link'
import {
    Activity, Building2, Server, Users, CreditCard,
    LogOut, ChevronRight, Globe, Clock, Shield,
    Cpu, HardDrive, Zap, TrendingUp
} from 'lucide-react'

interface OrgInfo {
    org_id: number
    name: string
    slug: string
    tier: string
    node_limit: number
    node_count: number
    online_nodes: number
    contact_email: string
    next_payment_date: string | null
    created_at: string
    user_count: number
}

interface DashboardData {
    total_orgs: number
    total_org_users: number
    total_nodes: number
    online_nodes: number
    organizations: OrgInfo[]
    upcoming_payments: number
    server_stats: { cpu: number; ram: number; gpu_load: number; timestamp: string }
}

export default function AdminDashboard() {
    const { user, logout, isAdmin } = useAuth()
    const [data, setData] = useState<DashboardData | null>(null)
    const [loading, setLoading] = useState(true)
    const [currentTime, setCurrentTime] = useState('')

    useEffect(() => {
        const interval = setInterval(() => setCurrentTime(new Date().toLocaleTimeString()), 1000)
        return () => clearInterval(interval)
    }, [])

    useEffect(() => {
        const fetchDashboard = async () => {
            try {
                const res = await apiFetch('/api/admin/dashboard')
                if (res.ok) {
                    setData(await res.json())
                }
            } catch (err) {
                console.error('Failed to fetch admin dashboard:', err)
            } finally {
                setLoading(false)
            }
        }
        fetchDashboard()
        const interval = setInterval(fetchDashboard, 5000)
        return () => clearInterval(interval)
    }, [])

    if (!isAdmin) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[#FAFAFA]">
                <p className="text-zinc-500 font-bold">Access Denied. Admin only.</p>
            </div>
        )
    }

    const statCards = data ? [
        { label: 'Organizations', value: data.total_orgs, icon: <Building2 className="w-5 h-5" />, color: 'orange' },
        { label: 'Total Nodes', value: data.total_nodes, icon: <Server className="w-5 h-5" />, color: 'emerald' },
        { label: 'Online Nodes', value: data.online_nodes, icon: <Globe className="w-5 h-5" />, color: 'emerald' },
        { label: 'Upcoming Payments', value: data.upcoming_payments, icon: <CreditCard className="w-5 h-5" />, color: 'orange' },
    ] : []

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-zinc-900 font-sans p-4 lg:p-8">
            {/* Ambient */}
            <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
                <div className="absolute top-[-20%] left-[-10%] w-[70%] h-[60%] bg-orange-500/5 blur-[140px] rounded-full" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[70%] h-[60%] bg-emerald-500/5 blur-[140px] rounded-full" />
            </div>

            {/* Header */}
            <header className="bg-white ring-1 ring-zinc-200/50 shadow-sm rounded-2xl px-6 py-4 flex justify-between items-center mb-6 relative z-10">
                <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center shadow-lg shadow-orange-500/20">
                        <Shield className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-black tracking-tight uppercase">Admin Dashboard</h1>
                        <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">System Logger PRO</p>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <div className="hidden sm:flex items-center gap-2 text-zinc-500 font-mono text-xs font-bold bg-zinc-50 px-3 py-1.5 rounded-lg ring-1 ring-zinc-200">
                        <Clock className="w-3.5 h-3.5" />
                        {currentTime}
                    </div>
                    <Link href="/admin/billing" className="hidden sm:flex items-center gap-2 px-4 py-2 bg-zinc-50 hover:bg-orange-50 text-zinc-600 hover:text-orange-600 rounded-xl ring-1 ring-zinc-200 hover:ring-orange-200 transition-all text-xs font-black uppercase tracking-wider">
                        <CreditCard className="w-4 h-4" /> Billing
                    </Link>

                    <button onClick={logout} className="p-2.5 bg-zinc-50 hover:bg-red-50 text-zinc-400 hover:text-red-600 rounded-xl ring-1 ring-zinc-200 hover:ring-red-200 transition-all" title="Logout">
                        <LogOut className="w-4 h-4" />
                    </button>
                </div>
            </header>

            <div className="relative z-10 space-y-6">
                {/* Stat Cards */}
                {loading ? (
                    <div className="flex items-center justify-center p-16">
                        <div className="w-8 h-8 border-2 border-zinc-200 border-t-orange-500 rounded-full animate-spin" />
                    </div>
                ) : data && (
                    <>
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                            {statCards.map((card, i) => (
                                <motion.div
                                    key={card.label}
                                    initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.1 }}
                                    className="bg-white rounded-2xl ring-1 ring-zinc-200/80 shadow-sm p-5 lg:p-6"
                                >
                                    <div className="flex items-center justify-between mb-3">
                                        <div className={`p-2 rounded-xl ${card.color === 'orange' ? 'bg-orange-50 text-orange-600' : 'bg-emerald-50 text-emerald-600'}`}>
                                            {card.icon}
                                        </div>
                                        <span className="text-[9px] font-black uppercase tracking-widest text-zinc-400">{card.label}</span>
                                    </div>
                                    <p className="text-3xl font-black font-mono tracking-tighter">{card.value}</p>
                                </motion.div>
                            ))}
                        </div>

                        {/* Server Stats */}
                        <div className="bg-white rounded-2xl ring-1 ring-zinc-200/80 shadow-sm p-6">
                            <h3 className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em] mb-4">Server Health</h3>
                            <div className="grid grid-cols-3 gap-4">
                                {[
                                    { label: 'CPU', value: data.server_stats.cpu, icon: <Cpu className="w-4 h-4" /> },
                                    { label: 'RAM', value: data.server_stats.ram, icon: <HardDrive className="w-4 h-4" /> },
                                    { label: 'GPU', value: data.server_stats.gpu_load, icon: <Zap className="w-4 h-4" /> },
                                ].map(s => (
                                    <div key={s.label} className="bg-zinc-50 rounded-xl p-4 ring-1 ring-zinc-100">
                                        <div className="flex items-center gap-2 mb-2 text-zinc-500">
                                            {s.icon}
                                            <span className="text-[10px] font-black uppercase tracking-widest">{s.label}</span>
                                        </div>
                                        <span className="text-2xl font-black font-mono">{s.value.toFixed(1)}%</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Organizations Table */}
                        <div className="bg-white rounded-2xl ring-1 ring-zinc-200/80 shadow-sm p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em]">Organizations</h3>
                                <span className="text-[10px] font-bold text-zinc-500 bg-zinc-50 px-2 py-1 rounded ring-1 ring-zinc-200">{data.organizations.length} total</span>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-zinc-100">
                                            <th className="text-left py-3 px-2 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Name</th>
                                            <th className="text-left py-3 px-2 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Tier</th>
                                            <th className="text-center py-3 px-2 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Nodes</th>
                                            <th className="text-center py-3 px-2 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Online</th>
                                            <th className="text-left py-3 px-2 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Next Payment</th>
                                            <th className="text-right py-3 px-2"></th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.organizations.map(org => (
                                            <tr key={org.org_id} className="border-b border-zinc-50 hover:bg-zinc-50/50 transition-colors">
                                                <td className="py-3 px-2 font-bold text-zinc-800">
                                                    <div className="flex items-center gap-2">
                                                        <Building2 className="w-4 h-4 text-zinc-400 shrink-0" />
                                                        {org.name}
                                                    </div>
                                                    <span className="text-[10px] text-zinc-400 ml-6">{org.slug}</span>
                                                </td>
                                                <td className="py-3 px-2">
                                                    <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${org.tier === 'business' ? 'bg-orange-50 text-orange-600 ring-1 ring-orange-200/50' : 'bg-zinc-100 text-zinc-600 ring-1 ring-zinc-200'}`}>
                                                        {org.tier}
                                                    </span>
                                                </td>
                                                <td className="py-3 px-2 text-center font-mono font-bold">{org.node_count}/{org.node_limit}</td>
                                                <td className="py-3 px-2 text-center">
                                                    <span className="flex items-center justify-center gap-1">
                                                        <span className={`w-2 h-2 rounded-full ${org.online_nodes > 0 ? 'bg-emerald-500' : 'bg-zinc-300'}`} />
                                                        <span className="font-mono font-bold">{org.online_nodes}</span>
                                                    </span>
                                                </td>
                                                <td className="py-3 px-2 text-xs text-zinc-500 font-mono">{org.next_payment_date || '—'}</td>
                                                <td className="py-3 px-2 text-right">
                                                    <Link href={`/${org.slug}`} className="p-1.5 hover:bg-orange-50 text-zinc-400 hover:text-orange-600 rounded-lg transition-colors inline-flex">
                                                        <ChevronRight className="w-4 h-4" />
                                                    </Link>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}
