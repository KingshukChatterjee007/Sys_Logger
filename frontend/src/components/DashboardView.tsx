'use client'

import React, { useState, useEffect } from 'react'
import { UsageGraph } from '@/components/UsageGraph'
import { useUsageData } from '@/components/hooks/useUsageData'
import { useUnits } from '@/components/hooks/useUnits'

import { Unit } from '@/components/types'
import {
    Monitor, Server, Database, Activity, Globe,
    ChevronRight, Layout,
    Cpu, HardDrive, Wifi, Zap
} from 'lucide-react'

interface DashboardViewProps {
    orgId?: string
}

export default function DashboardView({ orgId: propOrgId }: DashboardViewProps) {
    const [viewOrgId] = useState<string | null>(propOrgId || null)
    const { data: usageData, loading, setSelectedUnitId } = useUsageData(viewOrgId || undefined)
    const { units } = useUnits(viewOrgId || undefined)
    const [selectedUnit, setSelectedUnit] = useState<Unit | null>(null)
    const [currentTime, setCurrentTime] = useState<string>('')

    useEffect(() => {
        // Clock for header
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

    // Calculated Stats
    const activeUnits = units.filter(u => u.status === 'online').length
    const totalUnits = units.length
    const avgCpu = usageData.length > 0 ? usageData[usageData.length - 1].cpu : 0

    return (
        <div className="min-h-screen text-slate-200 font-sans selection:bg-cyan-500/30">
            {/* Ambient Background Glows */}
            <div className="fixed top-0 left-0 w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[120px] pointer-events-none -translate-x-1/2 -translate-y-1/2 z-0" />
            <div className="fixed bottom-0 right-0 w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[120px] pointer-events-none translate-x-1/3 translate-y-1/3 z-0" />

            <div className="relative z-10 container mx-auto p-4 lg:p-8 max-w-[1600px]">

                {/* Header */}
                <header className="flex justify-between items-center mb-8 glass-panel p-4 rounded-2xl">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-lg shadow-lg shadow-blue-500/20">
                            <Activity className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold tracking-tight text-white">Sys_Logger <span className="text-blue-400">Prime</span></h1>
                            <p className="text-xs text-slate-400 font-medium tracking-wide">REAL-TIME FLEET MONITORING</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-6">
                        <div className="hidden md:flex flex-col items-end">
                            <span className="text-2xl font-light font-mono text-white">{currentTime}</span>
                            <span className="text-[10px] uppercase tracking-widest text-emerald-400 flex items-center gap-1">
                                <span className="relative flex h-2 w-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                                </span>
                                System Operational
                            </span>
                        </div>
                    </div>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

                    {/* Sidebar / Unit List */}
                    <aside className="lg:col-span-1 space-y-4">

                        {/* Status Card */}
                        <div className="glass-panel p-6 rounded-2xl relative overflow-hidden group">
                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                <Server className="w-24 h-24" />
                            </div>
                            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-1">Fleet Status</h2>
                            <div className="flex items-baseline gap-2">
                                <span className="text-4xl font-bold text-white">{activeUnits}</span>
                                <span className="text-sm text-slate-400">/ {totalUnits} Online</span>
                            </div>
                            <div className="mt-4 h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-1000"
                                    style={{ width: `${(activeUnits / (totalUnits || 1)) * 100}%` }}
                                />
                            </div>
                        </div>

                        {/* Unit List */}
                        <div className="glass-panel rounded-2xl overflow-hidden flex flex-col max-h-[600px]">
                            <div className="p-4 border-b border-white/5 bg-white/5 backdrop-blur-md">
                                <h3 className="font-semibold text-white flex items-center gap-2">
                                    <Monitor className="w-4 h-4 text-blue-400" />
                                    Connected Units
                                </h3>
                            </div>
                            <div className="overflow-y-auto p-2 space-y-1 custom-scrollbar flex-1">
                                {loading ? (
                                    <div className="text-center p-8 text-slate-500 animate-pulse">Scanning...</div>
                                ) : units.map(unit => (
                                    <button
                                        key={unit.id}
                                        onClick={() => handleUnitSelect(unit)}
                                        className={`w-full text-left p-3 rounded-xl transition-all duration-200 border border-transparent group relative overflow-hidden
                                            ${selectedUnit?.id === unit.id
                                                ? 'bg-blue-600/20 border-blue-500/50 shadow-[0_0_20px_rgba(37,99,235,0.2)]'
                                                : 'hover:bg-white/5 hover:border-white/10'
                                            }
                                        `}
                                    >
                                        <div className="flex justify-between items-start relative z-10">
                                            <div>
                                                <div className={`font-medium ${selectedUnit?.id === unit.id ? 'text-white' : 'text-slate-300'}`}>
                                                    {unit.name}
                                                </div>
                                                <div className="text-[10px] text-slate-500 font-mono mt-0.5">{unit.ip}</div>
                                            </div>
                                            <div className={`w-2 h-2 rounded-full mt-1.5 ${unit.status === 'online' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-slate-600'}`} />
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="glass-panel p-4 rounded-2xl text-center">
                            <p className="text-xs text-slate-500">Avg CPU Load</p>
                            <div className="text-2xl font-bold text-white mt-1">{avgCpu.toFixed(1)}%</div>
                            <div className="text-[10px] text-emerald-400 mt-1">System Nominal</div>
                        </div>

                    </aside>

                    {/* Main Content Area */}
                    <main className="lg:col-span-3 space-y-6">
                        {selectedUnit ? (
                            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                {/* Unit Header */}
                                <div className="flex justify-between items-end">
                                    <div>
                                        <button onClick={clearSelection} className="text-xs text-blue-400 hover:text-blue-300 mb-2 flex items-center gap-1 transition-colors">
                                            <ChevronRight className="w-3 h-3 rotate-180" /> Back to Fleet
                                        </button>
                                        <h2 className="text-3xl font-bold text-white tracking-tight">{selectedUnit.name}</h2>
                                        <div className="flex items-center gap-4 mt-2 text-sm text-slate-400">
                                            <span className="flex items-center gap-1.5"><Globe className="w-3 h-3" /> {selectedUnit.ip}</span>
                                            <span className="flex items-center gap-1.5"><Database className="w-3 h-3" /> ID: {selectedUnit.id.substring(0, 8)}...</span>
                                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${selectedUnit.status === 'online' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/20 text-red-400'}`}>
                                                {selectedUnit.status}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        {/* Actions could go here */}
                                    </div>
                                </div>

                                {/* Metrics Grid */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="glass-panel rounded-2xl p-5 border-t-2 border-t-blue-500 relative group">
                                        <div className="absolute inset-0 bg-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl" />
                                        <div className="flex justify-between items-center mb-4 relative z-10">
                                            <div className="flex items-center gap-2 text-blue-400">
                                                <Cpu className="w-5 h-5" />
                                                <h3 className="font-semibold">CPU Load</h3>
                                            </div>
                                            <span className="text-2xl font-mono text-white">{usageData.length > 0 ? usageData[usageData.length - 1].cpu?.toFixed(1) : 0}%</span>
                                        </div>
                                        <div className="relative z-10">
                                            <UsageGraph data={usageData} metric="cpu" timeRange="1m" />
                                        </div>
                                    </div>

                                    <div className="glass-panel rounded-2xl p-5 border-t-2 border-t-emerald-500 relative group">
                                        <div className="absolute inset-0 bg-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl" />
                                        <div className="flex justify-between items-center mb-4 relative z-10">
                                            <div className="flex items-center gap-2 text-emerald-400">
                                                <Zap className="w-5 h-5" />
                                                <h3 className="font-semibold">GPU Load</h3>
                                            </div>
                                            <span className="text-2xl font-mono text-white">
                                                {usageData.length > 0 ? (
                                                    typeof usageData[usageData.length - 1].gpu === 'number'
                                                        ? (usageData[usageData.length - 1].gpu as number).toFixed(1)
                                                        : (usageData[usageData.length - 1].gpu_load || 0).toFixed(1)
                                                ) : 0}%
                                            </span>
                                        </div>
                                        <div className="relative z-10">
                                            <UsageGraph data={usageData} metric="gpu" timeRange="1m" />
                                        </div>
                                    </div>

                                    <div className="glass-panel rounded-2xl p-5 border-t-2 border-t-purple-500 relative group">
                                        <div className="absolute inset-0 bg-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl" />
                                        <div className="flex justify-between items-center mb-4 relative z-10">
                                            <div className="flex items-center gap-2 text-purple-400">
                                                <HardDrive className="w-5 h-5" />
                                                <h3 className="font-semibold">RAM Usage</h3>
                                            </div>
                                            <span className="text-2xl font-mono text-white">{usageData.length > 0 ? usageData[usageData.length - 1].ram?.toFixed(1) : 0}%</span>
                                        </div>
                                        <div className="relative z-10">
                                            <UsageGraph data={usageData} metric="ram" timeRange="1m" />
                                        </div>
                                    </div>

                                    <div className="glass-panel rounded-2xl p-5 border-t-2 border-t-cyan-500 relative group">
                                        <div className="absolute inset-0 bg-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl" />
                                        <div className="flex justify-between items-center mb-4 relative z-10">
                                            <div className="flex items-center gap-2 text-cyan-400">
                                                <Wifi className="w-5 h-5" />
                                                <h3 className="font-semibold">Network RX</h3>
                                            </div>
                                            <span className="text-2xl font-mono text-white">{usageData.length > 0 ? usageData[usageData.length - 1].network_rx?.toFixed(1) : 0} <span className="text-xs text-slate-500">KB/s</span></span>
                                        </div>
                                        <div className="relative z-10">
                                            <UsageGraph data={usageData} metric="network_rx" timeRange="1m" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            // Empty State / Global Dashboard Overview
                            <div className="h-full flex flex-col items-center justify-center p-12 glass-panel rounded-3xl border-dashed border-2 border-slate-700/50">
                                <div className="p-6 bg-slate-800/50 rounded-full mb-6 relative">
                                    <div className="absolute inset-0 bg-blue-500/20 blur-xl rounded-full animate-pulse" />
                                    <Layout className="w-16 h-16 text-blue-400 relative z-10" />
                                </div>
                                <h2 className="text-2xl font-bold text-white mb-2">Select a Unit</h2>
                                <p className="text-slate-400 text-center max-w-md">
                                    Choose a unit from the sidebar to view high-frequency real-time telemetry, GPU load, and system performance metrics.
                                </p>

                                <div className="grid grid-cols-3 gap-8 mt-12 w-full max-w-2xl">
                                    <div className="text-center">
                                        <div className="text-3xl font-bold text-emerald-400 mb-1">10Hz</div>
                                        <div className="text-xs text-slate-500 uppercase tracking-widest">Polling Rate</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-3xl font-bold text-blue-400 mb-1">0ms</div>
                                        <div className="text-xs text-slate-500 uppercase tracking-widest">Latency Info</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-3xl font-bold text-purple-400 mb-1">{totalUnits}</div>
                                        <div className="text-xs text-slate-500 uppercase tracking-widest">Total Monitored</div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </main>
                </div>
            </div>
        </div>
    )
}
