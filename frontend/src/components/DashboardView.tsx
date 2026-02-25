'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { UsageGraph } from '@/components/UsageGraph'
import { useUsageData } from '@/components/hooks/useUsageData'
import { useUnits } from '@/components/hooks/useUnits'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

import { Unit } from '@/components/types'
import {
    Monitor, Server, Database, Activity, Globe,
    ChevronRight, Layout, Download,
    Cpu, HardDrive, Wifi, Zap, Clock,
    Share2, Check, Pencil, Trash2, X, Save
} from 'lucide-react'

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

interface DashboardViewProps {
    orgId?: string
}

export default function DashboardView({ orgId: propOrgId }: DashboardViewProps) {
    const [viewOrgId] = useState<string | null>(propOrgId || null)
    const { data: usageData, loading, setSelectedUnitId, selectedUnitId } = useUsageData(viewOrgId || undefined)
    const { units } = useUnits(viewOrgId || undefined)
    const [selectedUnit, setSelectedUnit] = useState<Unit | null>(null)
    const [currentTime, setCurrentTime] = useState<string>('')
    const [startDate, setStartDate] = useState<string>('')
    const [endDate, setEndDate] = useState<string>('')
    const [copied, setCopied] = useState(false)
    const [isEditing, setIsEditing] = useState(false)
    const [editModeData, setEditModeData] = useState({ org_id: '', comp_id: '' })
    const [isDeleting, setIsDeleting] = useState(false)

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentTime(new Date().toLocaleTimeString())
        }, 1000)
        return () => clearInterval(interval)
    }, [])

    const handleUnitSelect = (unit: Unit) => {
        setSelectedUnit(unit)
        setSelectedUnitId(unit.id)
    }

    const clearSelection = () => {
        setSelectedUnit(null)
        setSelectedUnitId(null)
    }

    const handleShare = () => {
        const orgToShare = viewOrgId || selectedUnit?.org_id
        if (!orgToShare) return

        const url = `${window.location.origin}/org/${orgToShare}`
        navigator.clipboard.writeText(url)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    const handleCustomDownload = () => {
        if (!selectedUnitId) return
        let url = `/api/units/${selectedUnitId}/export`
        if (startDate && endDate) {
            url += `?start_date=${startDate}&end_date=${endDate}`
        } else {
            url += `?range=1d`
        }
        window.open(url, '_blank')
    }

    const handleUpdateUnit = async () => {
        if (!selectedUnit) return
        try {
            const response = await fetch(`/api/units/${selectedUnit.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(editModeData)
            })
            if (response.ok) {
                const updatedUnit = await response.json()
                setSelectedUnit(updatedUnit)
                setIsEditing(false)
            }
        } catch (err) {
            console.error('Failed to update unit:', err)
        }
    }

    const handleDeleteUnit = async () => {
        if (!selectedUnit) return
        if (!confirm(`Are you sure you want to permanently delete ${selectedUnit.name}? All history will be lost.`)) return

        setIsDeleting(true)
        try {
            const response = await fetch(`/api/units/${selectedUnit.id}`, {
                method: 'DELETE'
            })
            if (response.ok) {
                clearSelection()
            }
        } catch (err) {
            console.error('Failed to delete unit:', err)
        } finally {
            setIsDeleting(false)
        }
    }

    const activeUnits = units.filter(u => u.status === 'online').length
    const totalUnits = units.length
    const lastData = usageData.length > 0 ? usageData[usageData.length - 1] : null
    const avgCpu = lastData ? (lastData.cpu ?? lastData.cpu_usage ?? 0) : 0

    return (
        <div className="min-h-screen bg-[#020617] text-slate-200 overflow-hidden selection:bg-blue-500/30">
            {/* Mesh Gradient Backgrounds */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 blur-[120px] rounded-full animate-float" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-emerald-600/5 blur-[120px] rounded-full animate-float" style={{ animationDelay: '2s' }} />
                <div className="absolute top-[20%] right-[10%] w-[30%] h-[30%] bg-purple-600/5 blur-[120px] rounded-full animate-float" style={{ animationDelay: '4s' }} />
            </div>

            <div className="relative z-10 container mx-auto p-4 lg:p-6 max-w-[1600px] flex flex-col h-screen">

                {/* Modern Navbar */}
                <motion.header
                    initial={{ y: -20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className="flex justify-between items-center mb-6 glass-panel-rich p-4 rounded-2xl"
                >
                    <div className="flex items-center gap-4">
                        <div className="relative group">
                            <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-cyan-400 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-1000"></div>
                            <div className="relative p-2.5 bg-slate-900 rounded-xl border border-white/10">
                                <Activity className="w-6 h-6 text-blue-400" />
                            </div>
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <h1 className="text-xl font-bold tracking-tight text-white">Sys_Logger <span className="text-blue-400">Prime</span></h1>
                                <span className="px-1.5 py-0.5 rounded-md bg-blue-500/10 border border-blue-500/20 text-[10px] font-bold text-blue-400 tracking-widest uppercase">V2.0</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <p className="text-[10px] text-slate-400 font-semibold tracking-[0.2em] uppercase opacity-60">Fleet Telemetry Matrix</p>
                                {(viewOrgId || selectedUnit?.org_id) && (
                                    <button
                                        onClick={handleShare}
                                        className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 hover:bg-indigo-500/20 transition-colors group"
                                    >
                                        {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Share2 className="w-3 h-3 text-indigo-400 group-hover:text-indigo-300" />}
                                        <span className="text-[9px] font-bold tracking-wider text-indigo-400 group-hover:text-indigo-300 uppercase">
                                            {copied ? 'Copied Link' : 'Share Org'}
                                        </span>
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-8">
                        <div className="hidden lg:flex items-center gap-6 pr-6 border-r border-white/5">
                            <div className="text-right">
                                <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-0.5">Network Load</p>
                                <div className="flex items-center gap-1.5 justify-end">
                                    <div className="w-12 h-1 bg-slate-800 rounded-full overflow-hidden">
                                        <div className="h-full bg-blue-500 w-[45%]" />
                                    </div>
                                    <span className="text-xs font-mono text-blue-400">45%</span>
                                </div>
                            </div>
                        </div>
                        <div className="flex flex-col items-end">
                            <div className="flex items-center gap-2 text-white/90">
                                <Clock className="w-4 h-4 text-slate-500" />
                                <span className="text-xl font-light font-mono leading-none tracking-tight">{currentTime}</span>
                            </div>
                            <span className="text-[9px] uppercase tracking-[0.2em] text-emerald-400 flex items-center gap-1.5 mt-1 font-bold">
                                <span className="relative flex h-2 w-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-40"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                                </span>
                                Link Active
                            </span>
                        </div>
                    </div>
                </motion.header>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0 overflow-hidden">

                    {/* Enhanced Sidebar */}
                    <motion.aside
                        initial={{ x: -20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: 0.1 }}
                        className="lg:col-span-3 flex flex-col gap-4 min-h-0"
                    >
                        {/* Fleet Summary Card */}
                        <div className="glass-panel-rich p-5 rounded-2xl relative overflow-hidden group border-white/5">
                            <div className="absolute -right-4 -top-4 text-white/[0.02] transition-transform duration-700 group-hover:scale-110 group-hover:rotate-6">
                                <Server size={120} />
                            </div>
                            <div className="relative z-10">
                                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Operational Status</h3>
                                <div className="flex justify-between items-end">
                                    <div className="space-y-1">
                                        <p className="text-4xl font-bold text-white tracking-tighter">
                                            {activeUnits}<span className="text-slate-600 text-xl font-medium ml-1">/ {totalUnits}</span>
                                        </p>
                                        <p className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">Online Nodes</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-2xl font-mono text-white/80">{avgCpu.toFixed(0)}%</p>
                                        <p className="text-[9px] text-slate-500 uppercase font-bold tracking-wider">Avg CPU</p>
                                    </div>
                                </div>
                                <div className="mt-4 h-1 w-full bg-white/5 rounded-full overflow-hidden">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${(activeUnits / (totalUnits || 1)) * 100}%` }}
                                        className="h-full bg-gradient-to-r from-blue-500 via-cyan-400 to-emerald-400"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Interactive Unit List */}
                        <div className="glass-panel-rich rounded-2xl overflow-hidden flex flex-col flex-1 min-h-0 border-white/5">
                            <div className="p-4 border-b border-white/5 bg-white/[0.02] flex justify-between items-center">
                                <h3 className="font-bold text-xs uppercase tracking-[0.15em] text-white/70 flex items-center gap-2">
                                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></div>
                                    Registered Nodes
                                </h3>
                                <span className="px-2 py-0.5 rounded-full bg-white/5 text-[9px] font-bold text-slate-500 border border-white/5">
                                    {totalUnits} TOTAL
                                </span>
                            </div>
                            <div className="overflow-y-auto p-2 space-y-1 custom-scrollbar flex-1">
                                <AnimatePresence mode='popLayout'>
                                    {loading ? (
                                        <div className="flex flex-col items-center justify-center p-12 text-slate-500 gap-3">
                                            <div className="w-8 h-8 border-2 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
                                            <span className="text-[10px] font-bold uppercase tracking-widest">Scanning Network...</span>
                                        </div>
                                    ) : units.map((unit, idx) => (
                                        <motion.button
                                            layout
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: idx * 0.05 }}
                                            key={unit.id}
                                            onClick={() => handleUnitSelect(unit)}
                                            className={cn(
                                                "w-full text-left p-3.5 rounded-xl transition-all duration-300 border relative group",
                                                selectedUnit?.id === unit.id
                                                    ? 'bg-blue-600/10 border-blue-500/40 aura-blue'
                                                    : 'bg-white/[0.01] border-white/5 hover:bg-white/[0.04] hover:border-white/10'
                                            )}
                                        >
                                            <div className="flex justify-between items-center relative z-10">
                                                <div className="flex items-center gap-3">
                                                    <div className={cn(
                                                        "p-2 rounded-lg transition-colors",
                                                        selectedUnit?.id === unit.id ? 'bg-blue-500/20 text-blue-400' : 'bg-white/5 text-slate-500 group-hover:text-slate-300'
                                                    )}>
                                                        <Monitor size={16} />
                                                    </div>
                                                    <div>
                                                        <div className={cn(
                                                            "text-xs font-bold transition-colors",
                                                            selectedUnit?.id === unit.id ? 'text-white' : 'text-slate-300 group-hover:text-white'
                                                        )}>
                                                            {unit.name}
                                                        </div>
                                                        <div className="text-[9px] text-slate-500 font-mono mt-0.5 flex items-center gap-1 opacity-70">
                                                            <Globe size={8} /> {unit.ip || 'DHCP-LEASE'}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex flex-col items-end gap-1">
                                                    <div className={cn(
                                                        "w-1.5 h-1.5 rounded-full",
                                                        unit.status === 'online' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-slate-600'
                                                    )} />
                                                    <span className="text-[8px] font-bold text-slate-600 uppercase tracking-tighter">
                                                        {unit.status === 'online' ? 'LIVE' : 'OFFLINE'}
                                                    </span>
                                                </div>
                                            </div>
                                        </motion.button>
                                    ))}
                                </AnimatePresence>
                            </div>
                        </div>

                        {/* Developer Credit */}
                        <div className="mt-auto pt-4 px-4 pb-2 border-t border-white/5 opacity-40 hover:opacity-100 transition-opacity">
                            <p className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500 leading-relaxed text-center">
                                Developed by <span className="text-blue-400">Krishi Sahayogi Team</span><br />
                                NIELIT Bhubaneshwar
                            </p>
                        </div>
                    </motion.aside>

                    {/* Main Content Area */}
                    <main className="lg:col-span-9 flex flex-col min-h-0 min-w-0 pr-2">
                        <AnimatePresence mode="wait">
                            {selectedUnit ? (
                                <motion.div
                                    key={selectedUnit.id}
                                    initial={{ opacity: 0, scale: 0.98, y: 10 }}
                                    animate={{ opacity: 1, scale: 1, y: 0 }}
                                    exit={{ opacity: 0, scale: 0.98, y: -10 }}
                                    className="flex flex-col flex-1 min-h-0 gap-6"
                                >
                                    {/* Active Unit Header */}
                                    <div className="flex justify-between items-end pb-2">
                                        <div className="flex-1">
                                            <button
                                                onClick={clearSelection}
                                                className="text-[10px] font-bold text-blue-400 hover:text-blue-300 mb-3 flex items-center gap-1.5 uppercase tracking-widest transition-all hover:-translate-x-1"
                                            >
                                                <ChevronRight className="w-3 h-3 rotate-180" /> Back to Matrix
                                            </button>

                                            {isEditing ? (
                                                <div className="flex flex-col gap-4 bg-white/5 p-4 rounded-2xl border border-white/10 aura-blue mb-4 max-w-xl">
                                                    <div className="grid grid-cols-2 gap-4">
                                                        <div>
                                                            <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1.5 block">Organization ID</label>
                                                            <input
                                                                type="text"
                                                                value={editModeData.org_id}
                                                                onChange={(e) => setEditModeData({ ...editModeData, org_id: e.target.value })}
                                                                className="w-full bg-slate-900 border border-white/10 rounded-lg p-2 text-xs font-bold text-white focus:border-blue-500 outline-none"
                                                            />
                                                        </div>
                                                        <div>
                                                            <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1.5 block">Computer ID</label>
                                                            <input
                                                                type="text"
                                                                value={editModeData.comp_id}
                                                                onChange={(e) => setEditModeData({ ...editModeData, comp_id: e.target.value })}
                                                                className="w-full bg-slate-900 border border-white/10 rounded-lg p-2 text-xs font-bold text-white focus:border-blue-500 outline-none"
                                                            />
                                                        </div>
                                                    </div>
                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={handleUpdateUnit}
                                                            className="flex-1 bg-blue-600 hover:bg-blue-500 text-white rounded-lg py-2 text-[10px] font-black uppercase tracking-widest flex items-center justify-center gap-2 transition-colors"
                                                        >
                                                            <Save size={14} /> Save Changes
                                                        </button>
                                                        <button
                                                            onClick={() => setIsEditing(false)}
                                                            className="px-4 bg-white/5 hover:bg-white/10 text-slate-400 rounded-lg py-2 text-[10px] font-black uppercase tracking-widest flex items-center justify-center gap-2 transition-colors"
                                                        >
                                                            <X size={14} /> Cancel
                                                        </button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <>
                                                    <div className="flex items-center gap-3">
                                                        <h2 className="text-4xl font-black text-white tracking-tighter uppercase italic">{selectedUnit.name}</h2>
                                                        <div className={cn(
                                                            "px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-widest border",
                                                            selectedUnit.status === 'online' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'
                                                        )}>
                                                            {selectedUnit.status}
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-5 mt-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                                                        <span className="flex items-center gap-2 border-r border-white/10 pr-5 italic opacity-80"><Globe className="w-3 h-3" /> {selectedUnit.ip}</span>
                                                        <span className="flex items-center gap-2 italic opacity-80"><Database className="w-3 h-3" /> UID: {selectedUnit.id.substring(0, 12)}</span>
                                                    </div>
                                                </>
                                            )}
                                        </div>

                                        {/* Management Controls */}
                                        <div className="flex gap-2 items-center">
                                            {!isEditing && (
                                                <button
                                                    onClick={() => {
                                                        setEditModeData({ org_id: selectedUnit.org_id || '', comp_id: selectedUnit.comp_id || '' })
                                                        setIsEditing(true)
                                                    }}
                                                    className="p-3 bg-white/[0.03] border border-white/5 hover:bg-white/[0.08] hover:border-blue-500/30 text-slate-400 hover:text-blue-400 rounded-xl transition-all group"
                                                    title="Edit Unit Identity"
                                                >
                                                    <Pencil className="w-4 h-4" />
                                                </button>
                                            )}
                                            <button
                                                onClick={handleDeleteUnit}
                                                disabled={isDeleting}
                                                className="p-3 bg-red-500/5 border border-red-500/10 hover:bg-red-500/10 hover:border-red-500/40 text-red-400/60 hover:text-red-400 rounded-xl transition-all group disabled:opacity-50"
                                                title="Delete Unit Permanently"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                            <div className="w-[1px] h-8 bg-white/5 mx-2" />
                                            <button
                                                onClick={handleCustomDownload}
                                                className="p-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-all shadow-xl shadow-blue-600/20 active:scale-95 group"
                                                title="Export Usage Data"
                                            >
                                                <Download className="w-4 h-4 transition-transform group-hover:-translate-y-0.5" />
                                            </button>
                                        </div>
                                    </div>

                                    {/* Advanced Metric Grid */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1 min-h-0 overflow-y-auto pr-1 pb-4 custom-scrollbar">
                                        {/* CPU CARD */}
                                        <div className="glass-card p-6 !bg-blue-500/[0.02] border-blue-500/10 hover:border-blue-500/30 group/card aura-blue">
                                            <div className="flex justify-between items-start mb-6">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2.5 bg-blue-500/10 text-blue-400 rounded-xl group-hover/card:scale-110 transition-transform">
                                                        <Cpu size={20} />
                                                    </div>
                                                    <div>
                                                        <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-blue-400/80">Processor</h3>
                                                        <p className="font-bold text-white italic">CPU USAGE</p>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <span className="text-3xl font-mono font-bold text-white tracking-tighter">
                                                        {(lastData?.cpu ?? lastData?.cpu_usage ?? 0).toFixed(1)}<span className="text-sm text-blue-500/50 ml-0.5">%</span>
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="h-40 relative">
                                                <UsageGraph data={usageData} metric="cpu" className="h-full" />
                                            </div>
                                        </div>

                                        {/* GPU CARD */}
                                        <div className="glass-card p-6 !bg-emerald-500/[0.02] border-emerald-500/10 hover:border-emerald-500/30 group/card aura-emerald">
                                            <div className="flex justify-between items-start mb-6">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2.5 bg-emerald-500/10 text-emerald-400 rounded-xl group-hover/card:scale-110 transition-transform">
                                                        <Zap size={20} />
                                                    </div>
                                                    <div>
                                                        <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-400/80">Graphics</h3>
                                                        <p className="font-bold text-white italic">GPU USAGE</p>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <span className="text-3xl font-mono font-bold text-white tracking-tighter">
                                                        {typeof lastData?.gpu === 'number' ? lastData.gpu.toFixed(1) : (lastData?.gpu_load ?? 0).toFixed(1)}
                                                        <span className="text-sm text-emerald-500/50 ml-0.5">%</span>
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="h-40 relative">
                                                <UsageGraph data={usageData} metric="gpu" className="h-full" />
                                            </div>
                                        </div>

                                        {/* RAM CARD */}
                                        <div className="glass-card p-6 !bg-purple-500/[0.02] border-purple-500/10 hover:border-purple-500/30 group/card aura-purple">
                                            <div className="flex justify-between items-start mb-6">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2.5 bg-purple-500/10 text-purple-400 rounded-xl group-hover/card:scale-110 transition-transform">
                                                        <HardDrive size={20} />
                                                    </div>
                                                    <div>
                                                        <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-purple-400/80">Memory</h3>
                                                        <p className="font-bold text-white italic">RAM USAGE</p>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <span className="text-3xl font-mono font-bold text-white tracking-tighter">
                                                        {(lastData?.ram ?? lastData?.ram_usage ?? 0).toFixed(1)}<span className="text-sm text-purple-500/50 ml-0.5">%</span>
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="h-40 relative">
                                                <UsageGraph data={usageData} metric="ram" className="h-full" />
                                            </div>
                                        </div>

                                        {/* NETWORK CARD */}
                                        <div className="glass-card p-6 !bg-cyan-500/[0.02] border-cyan-500/10 hover:border-cyan-500/30 group/card shadow-[0_0_40px_rgba(6,182,212,0.15)]">
                                            <div className="flex justify-between items-start mb-6">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2.5 bg-cyan-500/10 text-cyan-400 rounded-xl group-hover/card:scale-110 transition-transform">
                                                        <Wifi size={20} />
                                                    </div>
                                                    <div>
                                                        <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-400/80">Interface</h3>
                                                        <p className="font-bold text-white italic">NETWORK THROUGHPUT</p>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <span className="text-3xl font-mono font-bold text-white tracking-tighter">
                                                        {(lastData?.network_rx ?? 0).toFixed(1)}<span className="text-[10px] text-cyan-500/50 ml-1 font-sans font-black uppercase">kb/s</span>
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="h-40 relative">
                                                <UsageGraph data={usageData} metric="network_rx" className="h-full" />
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            ) : (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="flex-1 flex flex-col items-center justify-center p-12 glass-panel-rich rounded-[2rem] border-dashed border-2 border-white/5 relative group"
                                >
                                    <div className="absolute inset-0 bg-blue-600/[0.02] animate-pulse rounded-[2rem] pointer-events-none" />
                                    <div className="relative">
                                        <div className="absolute -inset-8 bg-blue-500/10 blur-[50px] rounded-full animate-float" />
                                        <div className="relative p-8 bg-slate-800/80 rounded-3xl border border-white/10 shadow-2xl">
                                            <Layout className="w-16 h-16 text-blue-400" />
                                        </div>
                                    </div>
                                    <h2 className="text-3xl font-black text-white mt-8 tracking-tighter uppercase italic">Ready for Uplink</h2>
                                    <p className="text-slate-500 text-center max-w-sm mt-4 font-bold text-xs uppercase tracking-widest leading-relaxed">
                                        Select a node from the telemetry matrix to initiate high-frequency data streaming and unit analysis.
                                    </p>

                                    <div className="grid grid-cols-3 gap-12 mt-16 w-full max-w-lg">
                                        <div className="text-center group/stat">
                                            <div className="text-3xl font-mono font-black text-emerald-400 group-hover/stat:scale-110 transition-transform">10<span className="text-xs">Hz</span></div>
                                            <div className="text-[9px] text-slate-600 font-bold uppercase tracking-[0.2em] mt-2">Matrix Polling</div>
                                        </div>
                                        <div className="text-center group/stat">
                                            <div className="text-3xl font-mono font-black text-blue-400 group-hover/stat:scale-110 transition-transform">~0<span className="text-xs">ms</span></div>
                                            <div className="text-[9px] text-slate-600 font-bold uppercase tracking-[0.2em] mt-2">Latency Info</div>
                                        </div>
                                        <div className="text-center group/stat">
                                            <div className="text-3xl font-mono font-black text-purple-400 group-hover/stat:scale-110 transition-transform">{totalUnits}</div>
                                            <div className="text-[9px] text-slate-600 font-bold uppercase tracking-[0.2em] mt-2">Active Slots</div>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </main>
                </div>
            </div>
        </div>
    )
}
