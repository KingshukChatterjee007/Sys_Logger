'use client'

import Link from 'next/link';
import React, { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { UsageGraph } from './components/UsageGraph'
import { OrgManager } from './components/OrgManager'
import { useUsageData } from './components/hooks/useUsageData'
import { useUnits } from './components/hooks/useUnits'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

import { Unit } from './components/types'
import {
    Monitor, Server, Database, Globe,
    ChevronRight, Download, Cpu, HardDrive,
    Wifi, Zap, Clock, AlertTriangle,
    Terminal, Pencil, Trash2, X, Save, Activity, Menu, ArrowLeft, Shield, LogOut
} from 'lucide-react'

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

interface DashboardViewProps {
    orgId?: string
}


import { useAuth } from './components/AuthContext';
import { useRouter } from 'next/navigation';

export default function DashboardView({ orgId: propOrgId }: DashboardViewProps) {
    const { user, token, logout, isLoading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!isLoading && !token) {
            router.push('/login');
        }
    }, [token, isLoading, router]);

    const [viewOrgId] = useState<string | null>(propOrgId || null)

    // Real API Hooks
    const apiUsage = useUsageData(viewOrgId || undefined)
    const apiUnits = useUnits(viewOrgId || undefined)

    // Determine which data to use
    const units = apiUnits.units
    const loading = apiUnits.loading
    const usageData = apiUsage.data
    const selectedUnitId = apiUsage.selectedUnitId

    const [selectedUnit, setSelectedUnit] = useState<Unit | null>(null)
    const [currentTime, setCurrentTime] = useState<string>('')
    const [activeTab, setActiveTab] = useState<'metrics' | 'logs' | 'management'>('metrics')

    // Track the selected component metric
    const [selectedMetric, setSelectedMetric] = useState<'cpu' | 'gpu' | 'ram' | 'network_rx'>('cpu')

    const [isEditing, setIsEditing] = useState(false)
    const [editModeData, setEditModeData] = useState({ org_id: '', comp_id: '' })
    const [isDeleting, setIsDeleting] = useState(false)
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

    // Logo Carousel State
    const [logoIndex, setLogoIndex] = useState(0)

    // Dynamic logos configuration
    const logos = useMemo(() => [
        { img: '/krishishayogi.png', title: 'KRISHI SAHAYOGI', pre: 'BUILT BY', sub: 'NIELIT BHUBANESHWAR', bgClass: 'bg-zinc-900 shadow-inner', imgClass: '' },
        { img: '/Nielit_logo.jpeg', title: 'NIELIT', pre: 'POWERED BY', sub: 'BHUBANESWAR CENTRE', bgClass: 'bg-white ring-1 ring-zinc-200', imgClass: 'mix-blend-multiply opacity-90' },
        { img: '/India-AI_logo.jpeg', title: 'INDIA AI', pre: 'SUPPORTED BY', sub: 'MIN. OF ELECTRONICS & IT', bgClass: 'bg-white ring-1 ring-zinc-200', imgClass: 'mix-blend-multiply opacity-90' }
    ], [])

    // Clock and Carousel Timers
    useEffect(() => {
        const timeInterval = setInterval(() => setCurrentTime(new Date().toLocaleTimeString()), 1000)

        const logoInterval = setInterval(() => {
            setLogoIndex((prev) => (prev + 1) % logos.length)
        }, 3000)

        return () => {
            clearInterval(timeInterval)
            clearInterval(logoInterval)
        }
    }, [logos.length])

    useEffect(() => {
        if (selectedUnitId && units.length > 0) {
            const updatedUnit = units.find(u => u.id === selectedUnitId)
            if (updatedUnit) setSelectedUnit(updatedUnit)
        }
    }, [units, selectedUnitId])

    const handleUnitToggle = (unit: Unit) => {
        if (selectedUnitId === unit.id) {
            setIsMobileMenuOpen(false)
            return;
        }
        setSelectedUnit(unit)
        apiUsage.setSelectedUnitId(unit.id)
        setIsEditing(false)
        setIsMobileMenuOpen(false)
        setSelectedMetric('cpu') // Reset to CPU when switching units
    }

    const clearSelection = () => {
        setSelectedUnit(null)
        apiUsage.setSelectedUnitId(null)
        setIsEditing(false)
    }

    const handleCustomDownload = () => {
        if (!selectedUnitId) return
        window.open(`/api/units/${selectedUnitId}/export?range=1d`, '_blank')
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

    const systemHealth = useMemo(() => {
        if (!usageData.length) return 100
        const last = usageData[usageData.length - 1]
        const cpu = last.cpu ?? last.cpu_usage ?? 0
        const ram = last.ram ?? last.ram_usage ?? 0
        return Math.max(0, 100 - (cpu * 0.6 + ram * 0.4))
    }, [usageData])

    const lastData = usageData.length > 0 ? usageData[usageData.length - 1] : null
    const activeUnits = units.filter(u => u.status === 'online').length
    const totalUnits = units.length

    // Data for the Mini-Cards
    const currentMetrics = useMemo(() => [
        { id: 'cpu', title: 'Processing', label: 'CPU Load', value: (lastData?.cpu ?? lastData?.cpu_usage ?? 0).toFixed(1), unit: '%', icon: <Cpu className="w-5 h-5" />, color: 'orange' },
        { id: 'gpu', title: 'Graphics', label: 'GPU Compute', value: (lastData?.gpu ?? lastData?.gpu_load ?? 0).toFixed(1), unit: '%', icon: <Zap className="w-5 h-5" />, color: 'emerald' },
        { id: 'ram', title: 'Memory', label: 'RAM Util', value: (lastData?.ram ?? lastData?.ram_usage ?? 0).toFixed(1), unit: '%', icon: <HardDrive className="w-5 h-5" />, color: 'orange' },
        { id: 'network_rx', title: 'Network', label: 'RX Rate', value: (lastData?.network_rx ?? 0).toFixed(1), unit: 'KB/s', icon: <Wifi className="w-5 h-5" />, color: 'orange' }
    ], [lastData])

    const activeMetricData = currentMetrics.find(m => m.id === selectedMetric)

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-zinc-900 font-sans flex flex-col p-2 sm:p-4 lg:p-6 gap-4 lg:gap-6 relative selection:bg-orange-500/20">
            <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden flex justify-center items-center">
                <div className="absolute top-[-20%] left-[-10%] w-[70%] h-[60%] bg-orange-500/5 blur-[140px] rounded-full" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[70%] h-[60%] bg-orange-600/5 blur-[140px] rounded-full" />
            </div>

            {/* HEADER SECTION */}
            <header className="bg-white ring-1 ring-zinc-200/50 shadow-[0_2px_8px_rgba(0,0,0,0.02)] rounded-2xl px-4 lg:px-6 py-3 lg:py-4 flex justify-between items-center z-20 shrink-0">
                <div className="flex items-center gap-3 lg:gap-6">
                    <button
                        onClick={() => setIsMobileMenuOpen(true)}
                        className="lg:hidden p-2 text-zinc-500 hover:bg-zinc-100 hover:text-orange-600 rounded-lg transition-colors"
                    >
                        <Menu size={20} />
                    </button>
                    <div className="flex items-center gap-3 lg:pr-6">

                        <Link
                            href="/"
                            className="hidden sm:flex items-center justify-center w-10 h-10 bg-zinc-100 text-zinc-600 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors shadow-sm"
                            title="Return to Home"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </Link>

                        <div>
                            <h1 className="text-xl lg:text-2xl font-black tracking-tight text-zinc-900 uppercase">
                                Dashboard
                            </h1>
                        </div>
                    </div>
                </div>

                <div className="flex flex-col items-end">
                    <div className="flex items-center gap-1.5 lg:gap-2 text-zinc-800 font-mono font-bold text-sm lg:text-base tracking-tight">
                        <Clock className="w-3.5 h-3.5 text-zinc-400" />
                        {currentTime}
                    </div>
                    <span className="text-[9px] text-green-600 flex items-center gap-1.5 font-bold uppercase tracking-[0.1em] mt-1 bg-green-50 px-2.5 py-0.5 rounded-md ring-1 ring-green-200/50">
                        <Shield className="w-3 h-3 text-green-500" />
                        <span className="hidden sm:inline">Secure Link Active</span>
                        <span className="sm:hidden">Secure</span>
                    </span>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden gap-6 relative z-10 h-full">

                <AnimatePresence>
                    {isMobileMenuOpen && (
                        <motion.div
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-zinc-900/20 backdrop-blur-sm z-[100] lg:hidden"
                            onClick={() => setIsMobileMenuOpen(false)}
                        />
                    )}
                </AnimatePresence>

                <aside className={cn(
                    "fixed inset-y-0 left-0 z-[110] w-[85%] sm:w-80 bg-[#FAFAFA] shadow-[24px_0_40px_rgba(0,0,0,0.08)] lg:shadow-none lg:ring-1 ring-zinc-200/80 lg:rounded-3xl flex flex-col shrink-0 overflow-hidden lg:relative lg:translate-x-0 transition-transform duration-300 ease-in-out",
                    isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
                )}>
                    <div className="flex items-center justify-between p-4 border-b border-zinc-200/60 lg:hidden bg-white">
                        <span className="font-black text-zinc-800 text-xs tracking-widest uppercase flex items-center gap-2">
                            <Activity size={16} className="text-orange-500" /> Fleet Menu
                        </span>
                        <button
                            onClick={() => setIsMobileMenuOpen(false)}
                            className="p-1.5 text-zinc-400 hover:text-zinc-800 bg-zinc-50 hover:bg-zinc-100 rounded-md transition-colors"
                        >
                            <X size={18} />
                        </button>
                    </div>

                    <div className="p-5 lg:p-6 border-b border-zinc-200/60 bg-white shadow-sm z-10">
                        <div className="flex justify-between items-end mb-3">
                            <h3 className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em]">Network Status</h3>
                            <span className="px-2 py-0.5 rounded bg-zinc-50 ring-1 ring-zinc-200 text-[10px] font-black text-zinc-700 shadow-sm">
                                {activeUnits} <span className="text-zinc-400 font-bold">/ {totalUnits}</span>
                            </span>
                        </div>
                        <div className="w-full bg-zinc-100 rounded-full h-1.5 overflow-hidden shadow-inner">
                            <div
                                className="bg-orange-500 h-1.5 rounded-full transition-all duration-1000 ease-out"
                                style={{ width: `${totalUnits > 0 ? (activeUnits / totalUnits) * 100 : 0}%` }}
                            ></div>
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto p-3 lg:p-4 space-y-4 lg:space-y-6 custom-scrollbar bg-white/50">
                        {loading ? (
                            <div className="flex flex-col items-center justify-center p-8 text-zinc-400 gap-3">
                                <div className="w-6 h-6 border-2 border-zinc-200 border-t-orange-500 rounded-full animate-spin" />
                                <span className="text-[10px] font-bold uppercase tracking-widest">Scanning Nodes...</span>
                            </div>
                        ) : units.length === 0 ? (
                            <div className="text-center p-8 bg-white rounded-2xl border border-zinc-200 border-dashed m-2">
                                <Server className="w-8 h-8 text-zinc-300 mx-auto mb-3" />
                                <p className="text-xs font-bold text-zinc-500">No nodes found.</p>
                            </div>
                        ) : (
                            Object.entries(
                                units.reduce((acc, unit) => {
                                    const org = unit.org_id || 'Global';
                                    if (!acc[org]) acc[org] = [];
                                    acc[org].push(unit);
                                    return acc;
                                }, {} as Record<string, Unit[]>)
                            ).map(([org, orgUnits]) => (
                                <div key={org} className="space-y-2 lg:space-y-3">
                                    <div className="flex items-center gap-2 px-1 mb-2">
                                        <div className="p-1 px-1.5 bg-zinc-100 rounded text-[9px] font-black text-zinc-400 border border-zinc-200 uppercase tracking-widest">
                                            {org}
                                        </div>
                                        <div className="h-[1px] flex-1 bg-zinc-200/60" />
                                    </div>
                                    <div className="space-y-2 lg:space-y-3">
                                        {orgUnits.map((unit) => {
                                            const isSelected = selectedUnitId === unit.id;
                                            const isOnline = unit.status === 'online';

                                            return (
                                                <button
                                                    key={unit.id}
                                                    onClick={() => handleUnitToggle(unit)}
                                                    className={cn(
                                                        "w-full text-left p-3 lg:p-4 rounded-xl transition-all duration-200 relative overflow-hidden group/card shadow-sm",
                                                        isSelected
                                                            ? 'bg-white ring-1 ring-orange-500 shadow-[0_4px_12px_rgba(249,115,22,0.08)]'
                                                            : 'bg-white ring-1 ring-zinc-200/60 hover:ring-zinc-300 hover:shadow-md hover:-translate-y-0.5'
                                                    )}
                                                >
                                                    <div className="flex justify-between items-start mb-2.5">
                                                        <div className="flex items-center gap-2.5 lg:gap-3">
                                                            <div className={cn("p-1.5 lg:p-2 rounded-lg transition-colors", isSelected ? 'bg-orange-50 text-orange-600' : 'bg-zinc-50 text-zinc-400 group-hover/card:text-zinc-700')}>
                                                                <Monitor className="w-4 h-4" />
                                                            </div>
                                                            <span className={cn("font-bold truncate text-xs lg:text-sm transition-colors", isSelected ? 'text-zinc-900' : 'text-zinc-600 group-hover/card:text-zinc-900')}>
                                                                {unit.name.split('/').pop()}
                                                            </span>
                                                        </div>
                                                        <div className={cn("w-2 h-2 rounded-full mt-2 shrink-0 shadow-sm", isOnline ? 'bg-emerald-500' : 'bg-zinc-300')} />
                                                    </div>

                                                    <div className="flex justify-between items-center text-xs pl-[36px] lg:pl-[44px]">
                                                        <span className={cn("font-mono text-[10px] lg:text-[11px] font-medium truncate pr-2", isSelected ? 'text-orange-600' : 'text-zinc-400')}>{unit.ip}</span>
                                                    </div>
                                                </button>
                                            )
                                        })}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    {/* Constant Professional Logo Section */}
                    <div className="relative border-t border-zinc-200/60 flex flex-col items-center justify-center shrink-0 shadow-[0_-4px_20px_rgba(0,0,0,0.02)] z-10 py-6 px-4 overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-r from-orange-500/10 via-white to-white z-0 pointer-events-none" />
                        <div className="flex items-center justify-between w-full gap-3 mb-5 relative z-10">
                            <div className="flex-1 h-16 flex items-center justify-center p-1 transition-transform hover:scale-105">
                                <img
                                    src="/krishishayogi.png"
                                    alt="Krishi Sahayogi"
                                    className="max-h-full max-w-full object-contain drop-shadow-md"
                                />
                            </div>
                            <div className="flex-1 h-16 rounded-xl bg-white/70 backdrop-blur-md border border-zinc-200/50 flex items-center justify-center p-1.5 shadow-sm transition-all hover:scale-105">
                                <img
                                    src="/Nielit_logo.jpeg"
                                    alt="NIELIT"
                                    className="h-full w-full object-contain mix-blend-multiply opacity-90"
                                />
                            </div>
                            <div className="flex-1 h-16 rounded-xl bg-white/70 backdrop-blur-md border border-zinc-200/50 flex items-center justify-center p-1.5 shadow-sm transition-all hover:scale-105">
                                <img
                                    src="/India-AI_logo.jpeg"
                                    alt="India AI"
                                    className="h-full w-full object-contain mix-blend-multiply opacity-90"
                                />
                            </div>
                        </div>
                        <div className="text-center space-y-1.5 relative z-10">
                            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-zinc-400">
                                Built by <span className="text-orange-500 font-black">Krishi Sahayogi</span>
                            </p>
                            <p className="text-[9px] text-zinc-300 font-bold tracking-[0.35em] uppercase">
                                NIELIT Bhubaneswar
                            </p>
                        </div>
                    </div>

                    {/* User Profile & Logout */}
                    <div className="p-4 border-t border-zinc-200/60 bg-white">
                        <div className="flex items-center gap-3 p-3 bg-zinc-50 rounded-2xl ring-1 ring-zinc-200/50">
                            <div className="w-10 h-10 bg-zinc-900 rounded-xl flex items-center justify-center text-orange-500 font-black text-xs shadow-lg shadow-zinc-900/10">
                                {user?.email.charAt(0).toUpperCase() || 'U'}
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-xs font-black text-zinc-900 truncate">{user?.email}</p>
                                <div className="flex items-center gap-1.5 mt-0.5">
                                    <span className="text-[9px] font-black uppercase tracking-widest text-orange-600 bg-orange-50 px-1.5 py-0.5 rounded border border-orange-100">
                                        {user?.role}
                                    </span>
                                    <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">
                                        {user?.org_id}
                                    </span>
                                </div>
                            </div>
                            {user?.role === 'ROOT' && (
                                <button
                                    onClick={() => {
                                        setActiveTab(activeTab === 'management' ? 'metrics' : 'management');
                                        setIsMobileMenuOpen(false);
                                    }}
                                    className={cn(
                                        "p-2 rounded-lg transition-all",
                                        activeTab === 'management'
                                            ? "bg-orange-500 text-white shadow-lg shadow-orange-500/20"
                                            : "text-zinc-400 hover:text-orange-500 hover:bg-orange-50"
                                    )}
                                    title="System Management"
                                >
                                    <Shield size={16} />
                                </button>
                            )}
                            <button
                                onClick={logout}
                                className="p-2 text-zinc-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                title="Log Out"
                            >
                                <LogOut size={16} />
                            </button>
                        </div>
                    </div>
                </aside>


                <main className="flex-1 flex flex-col relative overflow-hidden w-full h-full">
                    <AnimatePresence mode="wait">
                        {activeTab === 'management' ? (
                            <motion.div
                                key="management"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="flex-1 overflow-y-auto p-4 lg:p-8 custom-scrollbar"
                            >
                                <OrgManager />
                            </motion.div>
                        ) : selectedUnit ? (
                            <motion.div
                                key={selectedUnit.id}
                                initial={{ opacity: 0, scale: 0.99, y: 5 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.99, y: -5 }}
                                transition={{ duration: 0.2, ease: "easeOut" }}
                                className="flex-1 flex flex-col overflow-y-auto custom-scrollbar h-full"
                            >
                                {/* ... existing unit view ... */}
                                <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-4 lg:mb-6 bg-white p-5 lg:p-6 rounded-2xl lg:rounded-3xl ring-1 ring-zinc-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] gap-4">
                                    <div className="flex-1 w-full">
                                        {isEditing ? (
                                            <div className="flex flex-col gap-3 lg:gap-4 w-full">
                                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 lg:gap-4">
                                                    <div>
                                                        <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1.5 block">Organization ID</label>
                                                        <input
                                                            type="text"
                                                            value={editModeData.org_id}
                                                            onChange={(e) => setEditModeData({ ...editModeData, org_id: e.target.value })}
                                                            className="w-full bg-zinc-50 ring-1 ring-zinc-200 rounded-xl p-3 text-sm font-bold text-zinc-800 focus:ring-orange-500 outline-none transition-all"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1.5 block">Computer ID</label>
                                                        <input
                                                            type="text"
                                                            value={editModeData.comp_id}
                                                            onChange={(e) => setEditModeData({ ...editModeData, comp_id: e.target.value })}
                                                            className="w-full bg-zinc-50 ring-1 ring-zinc-200 rounded-xl p-3 text-sm font-bold text-zinc-800 focus:ring-orange-500 outline-none transition-all"
                                                        />
                                                    </div>
                                                </div>
                                                <div className="flex gap-2 lg:gap-3 mt-1 lg:mt-2">
                                                    <button onClick={handleUpdateUnit} className="flex-1 sm:flex-none bg-orange-600 hover:bg-orange-500 text-white rounded-xl px-4 lg:px-6 py-2.5 lg:py-3 text-[10px] lg:text-[11px] font-black uppercase tracking-widest flex items-center justify-center gap-2 transition-all shadow-md shadow-orange-500/20">
                                                        <Save size={16} /> <span className="hidden sm:inline">Save Identity</span><span className="sm:hidden">Save</span>
                                                    </button>
                                                    <button onClick={() => setIsEditing(false)} className="flex-1 sm:flex-none px-4 lg:px-6 bg-zinc-100 hover:bg-zinc-200 text-zinc-600 rounded-xl py-2.5 lg:py-3 text-[10px] lg:text-[11px] font-black uppercase tracking-widest flex items-center justify-center gap-2 transition-colors">
                                                        <X size={16} /> Cancel
                                                    </button>
                                                </div>
                                            </div>
                                        ) : (
                                            <>
                                                <div className="flex flex-wrap items-center gap-3 lg:gap-4 mb-2 lg:mb-0">
                                                    <h2 className="text-2xl lg:text-3xl font-black text-zinc-900 tracking-tight uppercase truncate max-w-full">{selectedUnit.name.split('/').pop()}</h2>
                                                    <div className={cn("px-2.5 py-1 rounded text-[10px] font-black uppercase tracking-widest", selectedUnit.status === 'online' ? 'bg-emerald-50 text-emerald-600 ring-1 ring-emerald-200/50' : 'bg-red-50 text-red-600 ring-1 ring-red-200/50')}>
                                                        {selectedUnit.status}
                                                    </div>
                                                </div>
                                                <div className="flex flex-wrap items-center gap-4 lg:gap-6 mt-2 lg:mt-3 text-xs font-bold text-zinc-500">
                                                    <span className="flex items-center gap-2 pr-4 lg:pr-6 border-r border-zinc-200"><Globe className="w-4 h-4 text-zinc-400" /> {selectedUnit.ip}</span>
                                                    <span className="flex items-center gap-2"><Database className="w-4 h-4 text-zinc-400" /> <span className="truncate max-w-[150px] sm:max-w-none">{selectedUnit.id}</span></span>
                                                </div>
                                            </>
                                        )}
                                    </div>

                                    <div className="flex flex-row lg:flex-col items-center lg:items-end justify-between w-full lg:w-auto gap-4 lg:gap-4 border-t lg:border-t-0 border-zinc-100 pt-4 lg:pt-0 mt-2 lg:mt-0">
                                        <div className="flex gap-2 lg:gap-2.5">
                                            {!isEditing && (
                                                <button onClick={() => { setEditModeData({ org_id: selectedUnit.org_id || '', comp_id: selectedUnit.comp_id || '' }); setIsEditing(true); }} className="p-2.5 lg:p-3 bg-white ring-1 ring-zinc-200/80 hover:bg-orange-50 hover:ring-orange-200 hover:text-orange-600 text-zinc-400 rounded-xl transition-all shadow-sm" title="Edit Identity">
                                                    <Pencil className="w-4 h-4" />
                                                </button>
                                            )}
                                            <button onClick={handleDeleteUnit} disabled={isDeleting} className="p-2.5 lg:p-3 bg-white ring-1 ring-zinc-200/80 hover:bg-red-50 hover:ring-red-200 hover:text-red-600 text-zinc-400 rounded-xl transition-all shadow-sm disabled:opacity-50" title="Delete Node">
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                            <div className="hidden lg:block w-[1px] h-10 bg-zinc-200 mx-2 self-center" />
                                            <button onClick={handleCustomDownload} className="flex items-center gap-2 px-4 lg:px-5 py-2.5 lg:py-3 bg-zinc-900 hover:bg-zinc-800 text-white rounded-xl transition-all shadow-md active:scale-95">
                                                <Download className="w-4 h-4" />
                                                <span className="hidden sm:inline text-[11px] font-black uppercase tracking-widest">Export</span>
                                            </button>
                                        </div>

                                        {!isEditing && (
                                            <div className="flex bg-zinc-100/50 p-1 rounded-lg ring-1 ring-zinc-200/80 shrink-0">
                                                <button onClick={() => setActiveTab('metrics')} className={cn("px-4 lg:px-6 py-1.5 lg:py-2 rounded-md text-[10px] font-black uppercase tracking-widest transition-all", activeTab === 'metrics' ? 'bg-white text-orange-600 shadow-sm' : 'text-zinc-500 hover:text-zinc-800')}>System View</button>
                                                <button onClick={() => setActiveTab('logs')} className={cn("px-4 lg:px-6 py-1.5 lg:py-2 rounded-md text-[10px] font-black uppercase tracking-widest transition-all", activeTab === 'logs' ? 'bg-white text-orange-600 shadow-sm' : 'text-zinc-500 hover:text-zinc-800')}>Terminal</button>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {activeTab === 'metrics' ? (
                                    <div className="flex flex-col lg:flex-row gap-4 lg:gap-6 pb-4 lg:pb-6 flex-1 min-h-0">
                                        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-1 gap-3 lg:gap-4 shrink-0 lg:w-48 xl:w-56 overflow-y-auto custom-scrollbar p-1">
                                            {currentMetrics.map((metric) => (
                                                <button key={metric.id} onClick={() => setSelectedMetric(metric.id as any)} className={cn("p-4 lg:p-5 text-left rounded-2xl transition-all duration-300 flex flex-col justify-between items-start group relative z-0", selectedMetric === metric.id ? 'bg-white ring-2 ring-orange-500 shadow-[0_4px_15px_rgba(249,115,22,0.15)] scale-[1.02] z-10' : 'bg-white ring-1 ring-zinc-200/80 hover:ring-zinc-300 hover:shadow-md hover:-translate-y-0.5')}>
                                                    <div className="flex items-center justify-between w-full mb-3">
                                                        <div className={cn("p-2 rounded-xl transition-colors", selectedMetric === metric.id ? 'bg-orange-50 text-orange-600' : 'bg-zinc-50 text-zinc-400 group-hover:text-zinc-600')}>
                                                            {metric.icon}
                                                        </div>
                                                        <span className="text-[9px] font-black uppercase tracking-widest text-zinc-400">{metric.title}</span>
                                                    </div>
                                                    <div>
                                                        <p className={cn("font-bold tracking-tight mb-1", selectedMetric === metric.id ? 'text-zinc-900' : 'text-zinc-600')}>{metric.label}</p>
                                                        <p className="text-xl font-black font-mono text-zinc-900 tracking-tighter">
                                                            {metric.value} <span className="text-[10px] text-zinc-400 tracking-widest uppercase">{metric.unit}</span>
                                                        </p>
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                        <div className="flex-1 bg-white p-6 lg:p-8 rounded-2xl lg:rounded-3xl ring-1 ring-zinc-200/80 shadow-sm flex flex-col min-h-[400px] lg:min-h-0">
                                            <div className="flex justify-between items-end mb-6">
                                                <div>
                                                    <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-400 mb-1">Live Telemetry Stream</h3>
                                                    <h2 className="text-xl lg:text-2xl font-black text-zinc-900 tracking-widest uppercase">{activeMetricData?.label}</h2>
                                                </div>
                                                <div className="text-right bg-zinc-50 px-4 py-2 rounded-xl ring-1 ring-zinc-100">
                                                    <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400 block mb-0.5">Current Value</span>
                                                    <span className="text-2xl font-black font-mono text-zinc-900 tracking-tighter">
                                                        {activeMetricData?.value} <span className="text-xs text-zinc-500">{activeMetricData?.unit}</span>
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="flex-1 relative bg-zinc-50/50 rounded-2xl ring-1 ring-zinc-100 p-4">
                                                <UsageGraph data={usageData} metric={selectedMetric} className="h-full" />
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="bg-[#09090B] rounded-2xl lg:rounded-3xl shadow-xl border border-zinc-800 h-full min-h-[400px] lg:min-h-[500px] flex flex-col overflow-hidden">
                                        <div className="bg-[#18181B] p-3 lg:p-4 border-b border-zinc-800 flex items-center justify-between">
                                            <div className="flex items-center gap-2 lg:gap-3">
                                                <Terminal className="text-orange-500 w-4 h-4 lg:w-5 lg:h-5" />
                                                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-300">Secure Node Terminal</span>
                                            </div>
                                            <div className="flex gap-1.5">
                                                <div className="w-2.5 h-2.5 rounded-full bg-zinc-700"></div>
                                                <div className="w-2.5 h-2.5 rounded-full bg-zinc-700"></div>
                                                <div className="w-2.5 h-2.5 rounded-full bg-zinc-700"></div>
                                            </div>
                                        </div>
                                        <div className="p-4 lg:p-6 font-mono text-xs lg:text-[13px] text-zinc-400 space-y-2 overflow-y-auto flex-1 leading-relaxed break-words">
                                            <p>[{currentTime}] <span className="text-orange-400 font-bold">CONNECT</span>: Establishing secure tunnel to {selectedUnit.id}...</p>
                                            <p>[{currentTime}] <span className="text-emerald-400 font-bold">SUCCESS</span>: Auth token verified.</p>
                                            <p>[{currentTime}] <span className="text-zinc-500 font-bold">INFO</span>: Telemetry stream initialized at 1000ms polling rate.</p>
                                            <p className="animate-pulse mt-4 text-zinc-600 font-bold">_</p>
                                        </div>
                                    </div>
                                )}
                            </motion.div>
                        ) : (
                            <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 flex flex-col items-center justify-center bg-white shadow-[0_2px_12px_rgba(0,0,0,0.03)] rounded-2xl lg:rounded-3xl ring-1 ring-zinc-200/80 h-full p-6 text-center">
                                <div className="mb-6 lg:mb-8 p-6 lg:p-8 bg-zinc-50 rounded-full ring-1 ring-zinc-100 shadow-inner">
                                    <Server className="w-12 h-12 lg:w-16 lg:h-16 text-zinc-300" />
                                </div>
                                <h2 className="text-xl lg:text-2xl font-black text-zinc-900 tracking-tight uppercase mb-2 lg:mb-3">Awaiting Selection</h2>
                                <p className="text-zinc-500 max-w-sm text-xs lg:text-sm font-medium leading-relaxed">
                                    Choose a machine from the <span className="text-zinc-700 font-bold">Active Fleet</span> roster to monitor real-time telemetry and manage configurations.
                                </p>
                                <button
                                    onClick={() => setIsMobileMenuOpen(true)}
                                    className="mt-6 lg:hidden px-6 py-2.5 bg-orange-50 text-orange-600 font-bold rounded-xl ring-1 ring-orange-200 shadow-sm text-xs uppercase tracking-wider"
                                >
                                    Open Fleet Menu
                                </button>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </main>
            </div>
        </div>
    )
}