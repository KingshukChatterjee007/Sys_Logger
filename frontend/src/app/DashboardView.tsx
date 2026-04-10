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

import { Unit, UsageData } from './components/types'
import {
    Monitor, Server, Database, Globe,
    ChevronRight, Download, Cpu, HardDrive,
    Wifi, Zap, Clock, AlertTriangle,
    Terminal, Pencil, Trash2, X, Save, Activity, Menu, ArrowLeft, Shield, LogOut,
    Copy, FolderOpen, Plus
} from 'lucide-react'

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

interface DashboardViewProps {
    orgId?: string
}

interface PricingPlan {
    plan_id: number;
    name: string;
    slug: string;
    price_monthly: number;
    node_limit: number;
    features: string[];
    is_active: boolean;
}


import { useAuth } from './components/AuthContext';
import { useRouter } from 'next/navigation';

// ----------------------------------------------------------------------

const CompactStatCard = ({ unit, onClick }: { unit: Unit; onClick: () => void }) => {
    const isOnline = unit.status === 'online';
    const metrics = unit.metrics;

    return (
        <motion.button
            whileHover={{ y: -4, boxShadow: "0 20px 40px -10px rgba(0,0,0,0.05)" }}
            whileTap={{ scale: 0.98 }}
            onClick={onClick}
            className={cn(
                "flex flex-col p-6 bg-white rounded-[2rem] border transition-all duration-300 relative group overflow-hidden",
                isOnline
                    ? "border-zinc-100 shadow-[0_8px_30px_rgba(0,0,0,0.02)] hover:border-orange-200"
                    : "border-zinc-50 opacity-60 grayscale"
            )}
        >
            <div className="flex justify-between items-center mb-5">
                <div className="flex items-center gap-3">
                    <div className={cn(
                        "w-2 h-2 rounded-full",
                        isOnline ? "bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.4)]" : "bg-zinc-300"
                    )} />
                    <h3 className="font-bold text-xs uppercase tracking-widest text-zinc-500 truncate">
                        {unit.name.split('/').pop()}
                    </h3>
                </div>
                <div className="w-7 h-7 rounded-full bg-zinc-50 flex items-center justify-center text-zinc-300 group-hover:bg-orange-50 group-hover:text-orange-500 transition-colors">
                    <ChevronRight size={14} />
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                {[
                    { label: 'CPU', value: metrics?.cpu, icon: <Cpu size={12} /> },
                    { label: 'RAM', value: metrics?.ram, icon: <HardDrive size={12} /> },
                    { label: 'GPU', value: metrics?.gpu, icon: <Zap size={12} /> },
                    { label: 'NET', value: metrics?.network_rx, icon: <Wifi size={12} />, suffix: 'MB/s' }
                ].map((stat, i) => (
                    <div key={i} className="flex flex-col gap-1">
                        <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-1.5 font-mono">
                            {stat.icon} {stat.label}
                        </span>
                        <div className="text-xl font-bold text-zinc-900 tracking-tight">
                            {stat.value !== undefined ? (typeof stat.value === 'number' ? stat.value.toFixed(stat.label === 'NET' ? 1 : 0) : stat.value) : '--'}
                            <span className="text-[10px] text-zinc-300 font-bold ml-1 uppercase">{stat.suffix || '%'}</span>
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-5 pt-4 border-t border-zinc-50 flex items-center justify-between text-[10px] font-medium text-zinc-400">
                <span className="font-mono">{unit.ip || 'DISCONNECTED'}</span>
                <span>{unit.last_seen ? new Date(unit.last_seen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '--'}</span>
            </div>
        </motion.button>
    );
};

export default function DashboardView({ orgId: propOrgId }: DashboardViewProps) {
    const { user, token, logout, isLoading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!isLoading && !token) {
            router.push('/login');
        }
    }, [token, isLoading, router]);

    const [selectedUnit, setSelectedUnit] = useState<Unit | null>(null)
    const [mockUsageData, setMockUsageData] = useState<UsageData[]>([])
    const [currentTime, setCurrentTime] = useState<string>('')
    const [viewOrgId] = useState<string | null>(propOrgId || null)

    // Real API Hooks
    const apiUsage = useUsageData(viewOrgId || undefined)
    const apiUnits = useUnits(viewOrgId || undefined)

    // Sync selected unit with usage hook
    useEffect(() => {
        if (selectedUnit) {
            apiUsage.setSelectedUnitId(selectedUnit.id);
        } else {
            apiUsage.setSelectedUnitId(null);
        }
    }, [selectedUnit, apiUsage]);

    // Determine which data to use
    const units = apiUnits.units
    const sortedUnits = useMemo(() => {
        return [...units].sort((a, b) => {
            // 1. Primary Sort: Status (Online first)
            if (a.status === 'online' && b.status !== 'online') return -1;
            if (a.status !== 'online' && b.status === 'online') return 1;

            // 2. Secondary Sort: Name (Alphabetical - stable)
            return a.name.localeCompare(b.name);
        });
    }, [units]);

    const usageData = apiUsage.data
    const loading = apiUnits.loading
    const selectedUnitId = apiUsage.selectedUnitId

    const [activeTab, setActiveTab] = useState<'metrics' | 'logs' | 'management'>('metrics')
    const [selectedMetric, setSelectedMetric] = useState<'cpu' | 'gpu' | 'ram' | 'network_rx'>('cpu')


    const [isEditing, setIsEditing] = useState(false)
    const [editModeData, setEditModeData] = useState({ org_id: '', comp_id: '' })
    const [isDeleting, setIsDeleting] = useState(false)
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

    // Add Node State
    const [isAddNodeOpen, setIsAddNodeOpen] = useState(false)
    const [newNodeName, setNewNodeName] = useState('')
    const [isDownloading, setIsDownloading] = useState(false)
    const [addNodeError, setAddNodeError] = useState('')
    const [generatedLink, setGeneratedLink] = useState('')
    const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState(false)
    const [plans, setPlans] = useState<PricingPlan[]>([])
    const [paymentLoading, setPaymentLoading] = useState<string | null>(null)
    const [isReportModalOpen, setIsReportModalOpen] = useState(false)
    const [reportTarget, setReportTarget] = useState<{ id: string, name: string, type: 'node' | 'org' }>({ id: '', name: '', type: 'node' })
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

        // Load Razorpay & fetch plans
        const script = document.createElement('script');
        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
        script.async = true;
        document.body.appendChild(script);

        fetch('/api/pricing')
            .then(res => res.ok ? res.json() : Promise.reject())
            .then(data => { if (Array.isArray(data) && data.length > 0) setPlans(data) })
            .catch(() => setPlans([
                { plan_id: 2, name: "Pro", slug: "pro", price_monthly: 99, node_limit: 5, features: ["5 Active Nodes", "Advanced Metrics", "Priority Support"], is_active: true },
                { plan_id: 3, name: "Business", slug: "business", price_monthly: 199, node_limit: 10, features: ["10 Nodes", "Global Fleet Control", "24/7 Support"], is_active: true }
            ]))

        return () => {
            clearInterval(timeInterval)
            clearInterval(logoInterval)
            if (document.body.contains(script)) document.body.removeChild(script);
        }
    }, [logos.length])

    const handlePayment = async (plan: PricingPlan) => {
        setPaymentLoading(plan.slug);
        try {
            const orderResp = await fetch('/api/payments/create-order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ plan_slug: plan.slug })
            });
            const orderData = await orderResp.json();
            if (!orderResp.ok) throw new Error(orderData.error || 'Failed to create order');

            const options = {
                key: orderData.key_id,
                amount: orderData.amount,
                currency: orderData.currency,
                name: "SysLogger",
                description: `Upgrade to ${plan.name} Plan`,
                order_id: orderData.order_id,
                handler: async (response: any) => {
                    const verifyResp = await fetch('/api/payments/verify', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                        body: JSON.stringify({
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_signature: response.razorpay_signature
                        })
                    });
                    const verifyData = await verifyResp.json();
                    if (verifyResp.ok) {
                        setIsUpgradeModalOpen(false);
                        alert(`✅ Upgraded to ${verifyData.tier}! You can now add more monitors.`);
                        apiUnits.refetchUnits();
                    } else {
                        alert('Payment verification failed: ' + verifyData.error);
                    }
                },
                prefill: { name: '', email: user?.email || '' },
                theme: { color: '#f97316' }
            };
            const rzp = new (window as any).Razorpay(options);
            rzp.open();
        } catch (err: any) {
            alert(err.message || 'Payment failed to initiate');
        } finally {
            setPaymentLoading(null);
        }
    };

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
        if (!selectedUnit) return
        setReportTarget({
            id: selectedUnit.id.toString(),
            name: (selectedUnit.name || 'Unknown Node').split('/').pop() || '',
            type: 'node'
        })
        setIsReportModalOpen(true)
    }

    const triggerRawExport = (id: string, range: string) => {
        window.open(`/api/units/${id}/export?range=${range}`, '_blank')
    }

    const triggerIntelligentReport = (id: string, type: 'node' | 'org', range: string) => {
        window.open(`/report/${type}/${id}?range=${range}`, '_blank')
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
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            })
            if (response.ok) {
                clearSelection()
                apiUnits.refetchUnits()
            }
        } catch (err) {
            console.error('Failed to delete unit:', err)
        } finally {
            setIsDeleting(false)
        }
    }

    const downloadInstaller = async (compName: string) => {
        setIsDownloading(true)
        setAddNodeError('')

        try {
            const response = await fetch('/api/units/download-installer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ comp_id: compName })
            })

            if (!response.ok) {
                const data = await response.json()
                // Check for limit_reached error and open upgrade modal
                if (data.error === 'limit_reached') {
                    setIsAddNodeOpen(false)
                    setIsUpgradeModalOpen(true)
                    return false
                }
                setAddNodeError(data.message || 'Failed to download installer')
                return false
            }

            const blob = await response.blob()
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `sys_logger_installer_${compName}.zip`
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)
            return true
        } catch (err) {
            console.error('Download error:', err)
            setAddNodeError('Connection failure while preparing installer')
            return false
        } finally {
            setIsDownloading(false)
        }
    }

    const handleAddNode = async () => {
        if (!newNodeName.trim()) {
            setAddNodeError('Unit Name is required')
            return
        }

        const success = await downloadInstaller(newNodeName)
        if (success) {
            setIsAddNodeOpen(false)
            setNewNodeName('')
            apiUnits.refetchUnits()
        }
    }

    const handleGenerateLink = async (compName: string) => {
        if (!compName.trim()) {
            setAddNodeError('Unit Name is required')
            return
        }

        setIsDownloading(true)
        setAddNodeError('')
        setGeneratedLink('')

        try {
            const response = await fetch('/api/units/generate-link', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ comp_id: compName })
            })

            const data = await response.json()
            if (!response.ok) {
                if (data.error === 'limit_reached') {
                    setIsAddNodeOpen(false)
                    setIsUpgradeModalOpen(true)
                    return false
                }
                setAddNodeError(data.message || 'Failed to generate link')
                return false
            }

            const fullUrl = window.location.origin + data.download_url;
            setGeneratedLink(fullUrl)
            return true
        } catch (err) {
            console.error('Link generation error:', err)
            setAddNodeError('Connection failure while generating link')
            return false
        } finally {
            setIsDownloading(false)
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
        { id: 'network_rx', title: 'Network', label: 'RX Rate', value: (lastData?.network_rx ?? 0).toFixed(3), unit: 'MB/s', icon: <Wifi className="w-5 h-5" />, color: 'orange' }
    ], [lastData])

    const activeMetricData = currentMetrics.find(m => m.id === selectedMetric)

    return (
        <div className="h-screen overflow-hidden bg-[#FAFAFA] text-zinc-900 font-sans flex flex-col p-2 sm:p-4 lg:p-6 gap-4 lg:gap-6 relative selection:bg-orange-500/20">
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

                        <button
                            onClick={() => {
                                if (selectedUnit) {
                                    clearSelection();
                                } else {
                                    router.push('/');
                                }
                            }}
                            className="hidden sm:flex items-center justify-center w-10 h-10 bg-zinc-100 text-zinc-600 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors shadow-sm"
                            title={selectedUnit ? "Back to Fleet Overview" : "Return to Home"}
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>

                        <button
                            onClick={clearSelection}
                            className="text-left group"
                        >
                            <h1 className="text-xl lg:text-2xl font-black tracking-tight text-zinc-900 uppercase group-hover:text-orange-600 transition-colors">
                                Dashboard
                            </h1>
                        </button>
                    </div>
                </div>

                <div className="flex items-center gap-4 lg:gap-8">
                    {/* Time and Security Badge stacked compactly */}
                    <div className="flex flex-col items-end gap-1 px-4 lg:px-8 border-r border-zinc-100 shrink-0">
                        <div className="flex items-center gap-1.5 lg:gap-2 text-zinc-800 font-mono font-bold text-xs lg:text-sm tracking-tight whitespace-nowrap">
                            <Clock className="w-3 h-3 text-zinc-400" />
                            {currentTime}
                        </div>
                        <span className="text-[9px] text-green-600 flex items-center gap-1.5 font-black uppercase tracking-[0.1em] bg-green-50 px-2.5 py-0.5 rounded-md ring-1 ring-green-200/50 w-fit">
                            <Shield className="w-2.5 h-2.5 text-green-500" />
                            <span className="hidden lg:inline">Secure Link Active</span>
                            <span className="lg:hidden text-[8px]">Secure</span>
                        </span>
                    </div>

                    {/* Branding in Header */}
                    <div className="hidden md:flex items-center gap-3 lg:gap-6">
                        <div className="flex items-center gap-4 lg:gap-6">
                            <img src="/krishishayogi.png" alt="Krishi Sahayogi" className="h-16 lg:h-20 object-contain mix-blend-multiply transition-all" />
                            <div className="h-10 w-[1px] bg-zinc-100" />
                            <img src="/Nielit_logo.jpeg" alt="NIELIT" className="h-10 lg:h-11 object-contain mix-blend-multiply" />
                            <img src="/India-AI_logo.jpeg" alt="India AI" className="h-10 lg:h-11 object-contain mix-blend-multiply" />
                        </div>
                        <div className="hidden xl:flex flex-col">
                            <span className="text-[8px] font-black text-zinc-400 uppercase tracking-widest leading-none mb-1">Built by</span>
                            <span className="text-[10px] font-black text-orange-600 uppercase tracking-tighter leading-none">Krishi Sahayogi</span>
                        </div>
                    </div>
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
                    "fixed inset-y-0 left-0 z-[110] w-[85%] sm:w-80 bg-white/40 backdrop-blur-3xl lg:border border-white/60 lg:shadow-2xl lg:shadow-black/5 lg:rounded-[2.5rem] flex flex-col shrink-0 lg:relative lg:translate-x-0 transition-transform duration-500 ease-[cubic-bezier(0.16,1,0.3,1)]",
                    isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
                )}>
                    <div className="flex items-center justify-between p-6 border-b border-white/40 lg:hidden bg-white/20 backdrop-blur-md">
                        <span className="font-bold text-zinc-900 text-xs tracking-widest uppercase flex items-center gap-2">
                            <Activity size={16} className="text-orange-500" /> Fleet Overview
                        </span>
                        <button
                            onClick={() => setIsMobileMenuOpen(false)}
                            className="w-9 h-9 flex items-center justify-center text-zinc-400 hover:text-orange-600 bg-white/50 rounded-full shadow-sm transition-all"
                        >
                            <X size={18} />
                        </button>
                    </div>

                    <div className="p-8 border-b border-white/40 relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-orange-400/5 rounded-bl-full blur-2xl pointer-events-none" />
                        <div className="flex justify-between items-end mb-4 relative z-10">
                            <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.2em]">Live Nodes</h3>
                            <span className="px-3 py-1 rounded-full bg-white/80 backdrop-blur-sm shadow-sm text-[11px] font-bold text-zinc-900">
                                {activeUnits} <span className="text-zinc-300 font-medium">/ {totalUnits}</span>
                            </span>
                        </div>
                        <div className="w-full bg-black/5 rounded-full h-1.5 overflow-hidden relative z-10">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${totalUnits > 0 ? (activeUnits / totalUnits) * 100 : 0}%` }}
                                className="bg-orange-500 h-full rounded-full shadow-[0_0_12px_rgba(249,115,22,0.3)] transition-all duration-1000 ease-out"
                            />
                        </div>
                    </div>

                    {/* Navigation Actions */}
                    <div className="px-6 flex flex-col gap-4 py-8">
                        <button
                            onClick={() => setIsAddNodeOpen(true)}
                            className="w-full py-4 bg-zinc-900 text-white rounded-full font-bold uppercase tracking-widest text-[10px] flex items-center justify-center gap-2 hover:bg-orange-500 hover:shadow-xl hover:shadow-orange-500/20 active:scale-95 transition-all duration-300 group"
                        >
                            <Plus className="w-4 h-4 text-orange-400 group-hover:text-white transition-colors" />
                            Deploy Monitor
                        </button>

                        {user?.role === 'ROOT' && (
                            <div className="flex flex-col gap-2">
                                <button
                                    onClick={() => {
                                        setActiveTab(activeTab === 'management' ? 'metrics' : 'management');
                                        setIsMobileMenuOpen(false);
                                    }}
                                    className={cn(
                                        "w-full py-3.5 rounded-full font-bold uppercase tracking-widest text-[10px] flex items-center justify-center gap-2 transition-all duration-300 active:scale-95",
                                        activeTab === 'management'
                                            ? "bg-orange-50 text-orange-600 shadow-sm"
                                            : "bg-white/60 hover:bg-white text-zinc-500 hover:text-orange-500 shadow-sm"
                                    )}
                                >
                                    <Shield className={cn("w-3.5 h-3.5", activeTab === 'management' ? "text-orange-500" : "text-zinc-400")} />
                                    {activeTab === 'management' ? 'Exit Admin' : 'Admin Panel'}
                                </button>
                            </div>
                        )}

                        {activeTab === 'management' && user?.org_id && (
                            <button
                                onClick={() => {
                                    setReportTarget({
                                        id: user.org_id.toString(),
                                        name: 'Full Fleet Audit',
                                        type: 'org'
                                    });
                                    setIsReportModalOpen(true);
                                }}
                                className="w-full py-3.5 rounded-full bg-zinc-900 text-white font-bold uppercase tracking-widest text-[10px] flex items-center justify-center gap-2 hover:bg-orange-500 transition-all active:scale-95 shadow-lg shadow-black/5"
                            >
                                <Activity className="w-3.5 h-3.5 text-orange-400" />
                                Fleet Audit
                            </button>
                        )}
                    </div>

                    {/* Unit List Explorer */}
                    <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar bg-white/5 relative border-t border-white/20">
                        <div className="absolute inset-x-0 top-0 h-6 bg-gradient-to-b from-white/40 to-transparent pointer-events-none" />
                        {loading ? (
                            <div className="flex flex-col items-center justify-center p-8 text-zinc-500 gap-4">
                                <div className="w-8 h-8 border-[3px] border-zinc-200/50 border-t-orange-500 rounded-full animate-spin shadow-[0_0_15px_rgba(249,115,22,0.2)]" />
                                <span className="text-[10px] font-black uppercase tracking-[0.2em]">Scanning Nodes...</span>
                            </div>
                        ) : units.length === 0 ? (
                            <div className="text-center p-8 bg-white rounded-2xl border border-zinc-200 border-dashed m-2">
                                <Server className="w-8 h-8 text-zinc-300 mx-auto mb-3" />
                                <p className="text-xs font-bold text-zinc-500">No nodes found.</p>
                            </div>
                        ) : (
                            Object.entries(
                                sortedUnits.reduce((acc, unit) => {
                                    const org = unit.org_id || 'Global';
                                    if (!acc[org]) acc[org] = [];
                                    acc[org].push(unit);
                                    return acc;
                                }, {} as Record<string, Unit[]>)
                            ).map(([org, orgUnits]) => (
                                <div key={org} className="space-y-2 lg:space-y-3">
                                    <div className="flex items-center gap-2 px-1 mb-2">
                                        <div className="p-1 px-2 bg-zinc-900 rounded-lg text-[9px] font-black text-white border border-zinc-800 uppercase tracking-widest shadow-sm">
                                            {orgUnits[0].org_name}
                                            <span className="ml-1.5 font-bold border-l border-white/20 pl-1.5 text-orange-400">
                                                {orgUnits[0].org_slug}
                                            </span>
                                        </div>
                                        <div className="h-[1px] flex-1 bg-zinc-200/60" />
                                    </div>
                                    <div className="space-y-2 lg:space-y-3">
                                        {orgUnits.map((unit) => {
                                            const isSelected = selectedUnitId === unit.id;
                                            const isOnline = unit.status === 'online';
                                            const isPending = unit.status === 'pending';

                                            return (
                                                <div
                                                    key={unit.id}
                                                    role="button"
                                                    tabIndex={0}
                                                    onClick={() => handleUnitToggle(unit)}
                                                    onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleUnitToggle(unit); }}
                                                    className={cn(
                                                        "w-full text-left p-4 lg:p-5 rounded-[1.5rem] transition-all duration-300 relative overflow-hidden group/card backdrop-blur-md cursor-pointer",
                                                        isSelected
                                                            ? 'bg-white/90 ring-[1.5px] ring-orange-400 shadow-[0_8px_30px_rgba(249,115,22,0.15)] scale-[1.02]'
                                                            : 'bg-white/40 ring-1 ring-white/60 hover:ring-orange-200 hover:bg-white/60 hover:shadow-[0_4px_20px_rgba(0,0,0,0.05)] hover:-translate-y-1'
                                                    )}
                                                >
                                                    {isSelected && <div className="absolute inset-0 bg-gradient-to-br from-orange-400/5 to-transparent pointer-events-none" />}
                                                    <div className="flex justify-between items-start mb-3 relative z-10">
                                                        <div className="flex items-center gap-3 lg:gap-4">
                                                            <div className={cn("p-2 lg:p-2.5 rounded-xl transition-all duration-300",
                                                                isSelected ? 'bg-gradient-to-br from-orange-400 to-orange-500 text-white shadow-[0_4px_12px_rgba(249,115,22,0.3)]' : 'bg-white/80 ring-1 ring-white text-zinc-500 group-hover/card:text-orange-500 group-hover/card:shadow-md'
                                                            )}>
                                                                <Monitor className="w-4 h-4 lg:w-5 lg:h-5" />
                                                            </div>
                                                            <div className="flex flex-col min-w-0">
                                                                <span className={cn("font-black truncate text-sm lg:text-base tracking-tight transition-colors", isSelected ? 'text-zinc-900' : 'text-zinc-700 group-hover/card:text-zinc-900')}>
                                                                    {unit.name.split('/').pop()}
                                                                </span>
                                                                {isPending && (
                                                                    <span className="text-[9px] font-black text-orange-500 uppercase tracking-tighter animate-pulse">
                                                                        Awaiting Install
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </div>
                                                        <div className="flex items-center gap-2 mt-2.5 shrink-0">
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    downloadInstaller(unit.comp_id || unit.name.split('/').pop() || '');
                                                                }}
                                                                className={cn(
                                                                    "p-1.5 rounded-lg transition-all duration-300",
                                                                    isSelected
                                                                        ? "bg-zinc-100/80 text-orange-600 hover:bg-orange-600 hover:text-white"
                                                                        : "bg-white/50 text-zinc-400 hover:text-orange-500 hover:bg-white"
                                                                )}
                                                                title="Download Client"
                                                            >
                                                                <Download size={14} />
                                                            </button>
                                                            <div className={cn("w-2.5 h-2.5 rounded-full shadow-sm relative",
                                                                isOnline ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.8)]' :
                                                                    isPending ? 'bg-orange-400 animate-ping shadow-[0_0_10px_rgba(251,146,60,0.8)]' : 'bg-zinc-300'
                                                            )}>
                                                                {isOnline && <div className="absolute inset-0 rounded-full ring-2 ring-emerald-500/30 animate-ping" />}
                                                            </div>
                                                        </div>
                                                    </div>

                                                    <div className="flex justify-between items-center text-xs pl-[48px] lg:pl-[60px] relative z-10">
                                                        <span className={cn("font-mono text-[10px] lg:text-[11px] font-bold truncate pr-2 tracking-tight", isSelected ? 'text-orange-600/80' : 'text-zinc-500')}>
                                                            {isPending ? 'DEPLOYMENT PENDING' : unit.ip}
                                                        </span>
                                                    </div>
                                                </div>
                                            )
                                        })}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>


                    {/* User Profile & Logout */}
                    <div className="p-4 border-t border-white/60 bg-white/50 backdrop-blur-xl">
                        <div className="flex items-center gap-3 p-3 bg-white/80 rounded-[1.25rem] ring-1 ring-white shadow-sm hover:shadow-md transition-shadow">
                            <div className="w-11 h-11 bg-gradient-to-br from-zinc-800 to-zinc-900 rounded-[1rem] flex items-center justify-center text-orange-400 font-black text-sm shadow-[0_4px_15px_rgba(0,0,0,0.15)] ring-1 ring-zinc-700/50">
                                {user?.email.charAt(0).toUpperCase() || 'U'}
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-black text-zinc-900 truncate tracking-tight">{user?.email}</p>
                                <div className="flex items-center gap-1.5 mt-1">
                                    <span className="text-[9px] font-black uppercase tracking-[0.15em] text-orange-600 bg-orange-100/50 backdrop-blur-sm px-2 py-0.5 rounded-md ring-1 ring-orange-200">
                                        {user?.role}
                                    </span>
                                    <span className="text-[9px] font-black text-zinc-500 uppercase tracking-widest truncate">
                                        ID: {user?.org_id}
                                    </span>
                                </div>
                            </div>
                            <button
                                onClick={logout}
                                className="p-2.5 text-zinc-400 bg-white border border-transparent hover:border-red-200 hover:text-red-500 hover:bg-red-50 hover:shadow-[0_4px_15px_rgba(239,68,68,0.1)] rounded-xl transition-all shadow-sm"
                                title="Log Out"
                            >
                                <LogOut size={18} />
                            </button>
                        </div>
                    </div>
                </aside>


                {/* ADD MONITOR MODAL */}
                <AnimatePresence>
                    {isAddNodeOpen && (
                        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                onClick={() => setIsAddNodeOpen(false)}
                                className="absolute inset-0 bg-white/20 backdrop-blur-sm"
                            />
                            <motion.div
                                initial={{ opacity: 0, scale: 0.98, y: 10 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.98, y: 10 }}
                                className="relative w-full max-w-lg bg-white/90 backdrop-blur-2xl rounded-[3rem] shadow-[0_40px_120px_-20px_rgba(0,0,0,0.2)] p-10 lg:p-14 overflow-hidden border border-white"
                            >
                                <div className="flex justify-between items-start mb-10">
                                    <div className="flex items-center gap-5">
                                        <div className="w-14 h-14 bg-zinc-900 rounded-[1.25rem] flex items-center justify-center shadow-2xl shadow-zinc-900/20 ring-1 ring-zinc-800">
                                            <Activity className="w-7 h-7 text-orange-500" />
                                        </div>
                                        <div>
                                            <h2 className="text-3xl font-bold text-zinc-900 tracking-tight">Add Monitor</h2>
                                            <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.2em] mt-1">Telemetry Agent Deployment</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => setIsAddNodeOpen(false)}
                                        className="w-10 h-10 flex items-center justify-center text-zinc-400 hover:text-zinc-900 hover:bg-zinc-100 rounded-full transition-all"
                                    >
                                        <X size={20} />
                                    </button>
                                </div>

                                <div className="space-y-10">
                                    {/* STEP 1: IDENTIFY */}
                                    <div className="space-y-4">
                                        <div className="flex items-center gap-3">
                                            <span className="w-6 h-6 rounded-full bg-orange-500 text-white text-[10px] font-black flex items-center justify-center shadow-lg shadow-orange-500/30">1</span>
                                            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">Identify Unit</label>
                                        </div>
                                        <div className="relative">
                                            <Terminal className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-300" />
                                            <input
                                                type="text"
                                                value={newNodeName}
                                                onChange={(e) => setNewNodeName(e.target.value)}
                                                className="w-full bg-zinc-50 border-none ring-1 ring-zinc-100 rounded-[1.5rem] py-5 pl-14 pr-5 text-sm text-zinc-900 focus:ring-2 focus:ring-orange-500/20 transition-all font-semibold placeholder:text-zinc-300 shadow-sm"
                                                placeholder="e.g. primary-server"
                                            />
                                        </div>
                                    </div>

                                    {/* STEP 2: DEPLOY */}
                                    <div className="space-y-4">
                                        <div className="flex items-center gap-3">
                                            <span className="w-6 h-6 rounded-full bg-orange-500 text-white text-[10px] font-black flex items-center justify-center shadow-lg shadow-orange-500/30">2</span>
                                            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">Get Pre-configured Bundle</label>
                                        </div>

                                        {addNodeError && (
                                            <div className="flex items-center gap-3 bg-red-50 text-red-600 p-5 rounded-[1.5rem] text-[11px] font-bold ring-1 ring-red-100 animate-shake mb-4">
                                                <AlertTriangle className="w-4 h-4" />
                                                {addNodeError}
                                            </div>
                                        )}

                                        {generatedLink ? (
                                            <div className="p-6 bg-zinc-50 rounded-[2rem] border border-zinc-100 space-y-4">
                                                <div className="flex justify-between items-center">
                                                    <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500">Deployment Link</span>
                                                    <span className="text-[9px] font-bold text-orange-500 bg-orange-50 px-2 py-1 rounded-full">Expires in 24h</span>
                                                </div>
                                                <div className="relative group">
                                                    <input
                                                        type="text"
                                                        readOnly
                                                        value={generatedLink}
                                                        className="w-full bg-white border-none ring-1 ring-zinc-200 rounded-2xl py-4 pl-5 pr-14 text-xs font-mono text-zinc-600 focus:outline-none"
                                                        onClick={(e) => { e.currentTarget.select(); navigator.clipboard.writeText(generatedLink); }}
                                                    />
                                                    <button 
                                                        onClick={() => { navigator.clipboard.writeText(generatedLink); }}
                                                        className="absolute right-2 top-1/2 -translate-y-1/2 p-3 text-zinc-400 hover:text-orange-500 hover:bg-orange-50 rounded-xl transition-all"
                                                    >
                                                        <Copy size={18} />
                                                    </button>
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="grid grid-cols-2 gap-4">
                                                <button
                                                    onClick={handleAddNode}
                                                    disabled={isDownloading}
                                                    className="group bg-zinc-900 text-white rounded-full py-5 px-8 font-bold uppercase tracking-widest text-[10px] flex items-center justify-center gap-3 hover:bg-zinc-800 transition-all disabled:opacity-50 shadow-xl shadow-zinc-900/10 active:scale-[0.98]"
                                                >
                                                    {isDownloading ? (
                                                        <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                                    ) : (
                                                        <>Download ZIP <Download size={14} /></>
                                                    )}
                                                </button>
                                                <button
                                                    onClick={() => handleGenerateLink(newNodeName)}
                                                    disabled={isDownloading}
                                                    className="group bg-white text-zinc-600 ring-1 ring-zinc-200 rounded-full py-5 px-8 font-bold uppercase tracking-widest text-[10px] flex items-center justify-center gap-3 hover:bg-zinc-50 hover:ring-zinc-300 transition-all disabled:opacity-50 active:scale-[0.98]"
                                                >
                                                    Generate Link <Globe size={14} />
                                                </button>
                                            </div>
                                        )}
                                    </div>

                                    {/* STEP 3: SETUP */}
                                    <div className="space-y-4">
                                        <div className="flex items-center gap-3">
                                            <span className="w-6 h-6 rounded-full bg-orange-500 text-white text-[10px] font-black flex items-center justify-center shadow-lg shadow-orange-500/30">3</span>
                                            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">Installation Steps</label>
                                        </div>
                                        <div className="grid grid-cols-1 gap-3">
                                            {[
                                                { icon: <HardDrive className="w-4 h-4" />, text: "Extract ZIP to C:\\ drive" },
                                                { icon: <FolderOpen className="w-4 h-4" />, text: "Open 'SysLogger_Agent' folder" },
                                                { icon: <Zap className="w-4 h-4" />, text: "Run 'install.bat' as Admin" }
                                            ].map((step, idx) => (
                                                <div key={idx} className="flex items-center gap-5 p-5 bg-white rounded-[1.5rem] border border-zinc-100/80 hover:border-zinc-200 hover:shadow-sm transition-all group">
                                                    <div className="p-2.5 bg-zinc-50 rounded-xl text-zinc-400 group-hover:text-orange-500 group-hover:bg-orange-50 transition-colors">
                                                        {step.icon}
                                                    </div>
                                                    <p className="text-[11px] font-bold text-zinc-600 leading-tight">{step.text}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                {generatedLink && (
                                    <motion.button
                                        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                                        onClick={() => { setIsAddNodeOpen(false); setNewNodeName(''); setGeneratedLink(''); apiUnits.refetchUnits(); }}
                                        className="w-full mt-10 bg-orange-500 hover:bg-orange-600 text-white rounded-full py-5 font-bold uppercase tracking-widest text-xs transition-all shadow-xl shadow-orange-500/30 active:scale-[0.98]"
                                    >
                                        Setup Complete
                                    </motion.button>
                                )}
                            </motion.div>
                        </div>
                    )}
                </AnimatePresence>

                {/* UPGRADE MODAL */}
                <AnimatePresence>
                    {isUpgradeModalOpen && (
                        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                            <motion.div
                                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                onClick={() => setIsUpgradeModalOpen(false)}
                                className="absolute inset-0 bg-zinc-900/50 backdrop-blur-sm"
                            />
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                                className="relative w-full max-w-xl bg-white rounded-[2.5rem] shadow-[0_32px_64px_-16px_rgba(0,0,0,0.25)] p-10 overflow-hidden"
                            >
                                <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-orange-500 to-emerald-500" />
                                <button
                                    onClick={() => setIsUpgradeModalOpen(false)}
                                    className="absolute top-6 right-6 p-2 text-zinc-400 hover:text-zinc-900 hover:bg-zinc-100 rounded-xl transition-all"
                                >
                                    <X size={20} />
                                </button>

                                <div className="mb-6">
                                    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-orange-50 ring-1 ring-orange-200 mb-4">
                                        <AlertTriangle className="w-3.5 h-3.5 text-orange-500" />
                                        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-orange-600">Node Limit Reached</span>
                                    </div>
                                    <h2 className="text-2xl font-black text-zinc-900 tracking-tight mb-2">Upgrade Your Plan</h2>
                                    <p className="text-sm font-medium text-zinc-500">You've used all your available node slots. Upgrade below to unlock more monitors instantly.</p>
                                </div>

                                {plans && plans.length > 0 && (
                                    <div className="space-y-4">
                                        {plans
                                            .filter(p => p.price_monthly > 0) // Only show paid plans for upgrade
                                            .map((plan) => {
                                                const isCurrentPlan = user?.tier?.toUpperCase() === plan.slug.toUpperCase();
                                                const isRecommended = (user?.tier?.toUpperCase() === 'PRO' && plan.slug === 'business') ||
                                                    (user?.tier?.toUpperCase() !== 'PRO' && plan.slug === 'pro');

                                                return (
                                                    <div key={plan.plan_id} className={`relative flex items-center justify-between p-5 rounded-2xl ring-1 transition-all ${isRecommended ? 'ring-orange-300 bg-orange-50/50' : 'ring-zinc-200 bg-zinc-50/50'} ${isCurrentPlan ? 'opacity-70 grayscale-[0.5]' : ''}`}>
                                                        {isRecommended && (
                                                            <div className="absolute -top-2.5 left-4 px-3 py-0.5 bg-orange-500 text-white text-[9px] font-black uppercase tracking-widest rounded-full shadow-sm">
                                                                Recommended
                                                            </div>
                                                        )}
                                                        {isCurrentPlan && (
                                                            <div className="absolute -top-2.5 left-4 px-3 py-0.5 bg-zinc-400 text-white text-[9px] font-black uppercase tracking-widest rounded-full shadow-sm">
                                                                Current Plan
                                                            </div>
                                                        )}
                                                        <div>
                                                            <p className="font-black text-zinc-900 uppercase tracking-wider text-sm">{plan.name}</p>
                                                            <p className="text-xs font-medium text-zinc-500 mt-0.5">{plan.node_limit} Active Nodes • ₹{plan.price_monthly}/mo</p>
                                                        </div>
                                                        <button
                                                            onClick={() => !isCurrentPlan && handlePayment(plan)}
                                                            disabled={paymentLoading === plan.slug || isCurrentPlan}
                                                            className={`px-5 py-2.5 rounded-xl font-black uppercase tracking-widest text-[10px] flex items-center gap-2 transition-all disabled:opacity-50 ${isRecommended ? 'bg-zinc-900 text-white hover:bg-zinc-800 shadow-lg shadow-zinc-900/10' : 'bg-white text-zinc-700 ring-1 ring-zinc-200 hover:ring-zinc-300'}`}
                                                        >
                                                            {paymentLoading === plan.slug ? (
                                                                <div className="w-3.5 h-3.5 border-2 border-current/30 border-t-current rounded-full animate-spin" />
                                                            ) : isCurrentPlan ? 'Active' : 'Upgrade Now'}
                                                        </button>
                                                    </div>
                                                );
                                            })}
                                    </div>
                                )}
                            </motion.div>
                        </div>
                    )}
                </AnimatePresence>

                {/* LINK MODAL FOR ACTIVE NODES */}
                <AnimatePresence>
                    {generatedLink && !isAddNodeOpen && (!selectedUnit || selectedUnit.status !== 'pending') && (
                        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                onClick={() => setGeneratedLink('')}
                                className="absolute inset-0 bg-zinc-900/40 backdrop-blur-sm"
                            />
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                                className="relative w-full max-w-md bg-white rounded-[2.5rem] shadow-[0_32px_64px_-16px_rgba(0,0,0,0.2)] p-10 overflow-hidden"
                            >
                                <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-orange-500 to-emerald-500" />
                                <button
                                    onClick={() => setGeneratedLink('')}
                                    className="absolute top-6 right-6 p-2 text-zinc-400 hover:text-zinc-900 hover:bg-zinc-100 rounded-xl transition-all"
                                >
                                    <X size={20} />
                                </button>
                                <div className="mb-6">
                                    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 ring-1 ring-emerald-200 mb-4">
                                        <Globe className="w-3.5 h-3.5 text-emerald-500" />
                                        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-600">Link Generated</span>
                                    </div>
                                    <h2 className="text-2xl font-black text-zinc-900 tracking-tight mb-2">Share Installer</h2>
                                    <p className="text-sm font-medium text-zinc-500">Copy the URL below. It will expire in 24 hours.</p>
                                </div>
                                <input
                                    type="text"
                                    readOnly
                                    value={generatedLink}
                                    className="w-full bg-zinc-50 border-none ring-1 ring-zinc-200 rounded-xl py-4 px-4 text-xs font-mono text-zinc-600 focus:outline-none mb-6 text-center"
                                    onClick={(e) => { e.currentTarget.select(); navigator.clipboard.writeText(generatedLink); }}
                                />
                                <button
                                    onClick={() => { navigator.clipboard.writeText(generatedLink); setGeneratedLink(''); }}
                                    className="w-full bg-zinc-900 text-white rounded-2xl py-4 font-black uppercase tracking-widest text-[11px] flex items-center justify-center gap-2 hover:bg-zinc-800 transition-all shadow-md"
                                >
                                    Copy & Close
                                </button>
                            </motion.div>
                        </div>
                    )}
                </AnimatePresence>

                {/* EXPORT & REPORT MODAL */}
                <AnimatePresence>
                    {isReportModalOpen && (
                        <div className="fixed inset-0 z-[110] flex items-center justify-center p-4">
                            <motion.div
                                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                onClick={() => setIsReportModalOpen(false)}
                                className="absolute inset-0 bg-zinc-900/60 backdrop-blur-md"
                            />
                            <motion.div
                                initial={{ opacity: 0, scale: 0.9, y: 30 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.9, y: 30 }}
                                className="relative w-full max-w-lg bg-white rounded-[3rem] shadow-2xl p-12 overflow-hidden"
                            >
                                <div className="absolute top-0 left-0 w-full h-2 bg-zinc-900" />
                                <div className="flex justify-between items-start mb-10">
                                    <div>
                                        <div className="flex items-center gap-2 text-orange-500 mb-2">
                                            <Activity size={20} />
                                            <span className="text-[10px] font-black uppercase tracking-[0.2em]">Data Audit Engine</span>
                                        </div>
                                        <h2 className="text-3xl font-black text-zinc-900 tracking-tighter uppercase whitespace-pre-line">Audit & Export{"\n"}Generation</h2>
                                        <p className="text-sm font-bold text-zinc-400 mt-2 uppercase tracking-wide">Target: <span className="text-zinc-900">{reportTarget.name}</span></p>
                                    </div>
                                    <button onClick={() => setIsReportModalOpen(false)} className="p-3 bg-zinc-50 hover:bg-zinc-100 text-zinc-400 hover:text-zinc-900 rounded-2xl transition-all"><X size={20} /></button>
                                </div>

                                <div className="space-y-8">
                                    <div>
                                        <label className="text-[9px] font-black uppercase tracking-[0.2em] text-zinc-400 ml-1 block mb-3">1. Select Audit Timeframe</label>
                                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                            {['1d', '7d', '30d', '1y'].map((r) => (
                                                <button
                                                    key={r}
                                                    onClick={() => setReportTarget({ ...reportTarget, range: r } as any)}
                                                    className={cn(
                                                        "py-3 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all ring-1",
                                                        (reportTarget as any).range === r
                                                            ? "bg-zinc-900 text-white ring-zinc-900 shadow-lg shadow-zinc-900/20"
                                                            : "bg-white text-zinc-500 ring-zinc-100 hover:ring-zinc-300"
                                                    )}
                                                >
                                                    {r === '1d' ? '24H' : r === '7d' ? '7 Days' : r === '30d' ? '30 Days' : '1 Year'}
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="flex flex-col gap-4">
                                        <button
                                            onClick={() => { triggerIntelligentReport(reportTarget.id, reportTarget.type, (reportTarget as any).range || '7d'); setIsReportModalOpen(false); }}
                                            className="w-full bg-gradient-to-r from-orange-600 to-orange-500 text-white rounded-[1.5rem] py-5 font-black uppercase tracking-widest text-xs flex items-center justify-center gap-3 hover:shadow-xl hover:shadow-orange-500/20 transition-all border-b-4 border-orange-700 active:border-b-0 active:translate-y-1"
                                        >
                                            <Zap size={18} />
                                            View Intelligent Audit Report
                                        </button>
                                        <button
                                            onClick={() => { triggerRawExport(reportTarget.id, (reportTarget as any).range || '7d'); setIsReportModalOpen(false); }}
                                            className="w-full bg-zinc-100 hover:bg-zinc-200 text-zinc-700 rounded-[1.5rem] py-5 font-black uppercase tracking-widest text-xs flex items-center justify-center gap-3 transition-all"
                                        >
                                            <Download size={18} />
                                            Download Raw CSV Data
                                        </button>
                                    </div>

                                    <p className="text-[10px] text-center text-zinc-400 font-medium leading-relaxed italic">
                                        * Intelligent reports utilize heuristic patterns to detect bottlenecks, performance anomalies and provide automated resource advice.
                                    </p>
                                </div>
                            </motion.div>
                        </div>
                    )}
                </AnimatePresence>

                <main className="flex-1 flex flex-col relative min-w-0">
                    <AnimatePresence mode="wait">
                        {activeTab === 'management' ? (
                            <motion.div
                                key="management"
                                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
                                className="flex-1 overflow-y-auto p-4 lg:p-10 custom-scrollbar"
                            >
                                <OrgManager />
                            </motion.div>
                        ) : selectedUnit ? (
                            <motion.div
                                key={selectedUnit.id}
                                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
                                className="flex-1 flex flex-col p-4 lg:p-10 overflow-y-auto custom-scrollbar"
                            >
                                {/* Unit Details Header */}
                                <div className="bg-white/70 backdrop-blur-xl rounded-[2.5rem] p-8 mb-8 border border-white/60 shadow-[0_8px_40px_-10px_rgba(0,0,0,0.03)] flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
                                    <div className="flex items-center gap-6">
                                        <div className="w-16 h-16 bg-zinc-900 rounded-[1.5rem] flex items-center justify-center shadow-xl ring-1 ring-zinc-800">
                                            <Monitor className="w-8 h-8 text-orange-500" />
                                        </div>
                                        <div className="min-w-0">
                                            <div className="flex items-center gap-3 mb-1">
                                                <h2 className="text-3xl font-bold text-zinc-900 tracking-tight truncate">{selectedUnit.name.split('/').pop()}</h2>
                                                <div className={cn(
                                                    "w-2.5 h-2.5 rounded-full shrink-0",
                                                    selectedUnit.status === 'online' ? "bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.4)]" : "bg-zinc-300"
                                                )} />
                                            </div>
                                            <div className="flex items-center gap-4 text-xs font-bold text-zinc-400 uppercase tracking-widest whitespace-nowrap">
                                                <span className="flex items-center gap-1.5"><Globe size={12} /> {selectedUnit.ip || 'Local Node'}</span>
                                                <span className="w-1 h-1 bg-zinc-200 rounded-full" />
                                                <span className="flex items-center gap-1.5 font-mono">ID: {selectedUnit.id.slice(0, 8)}</span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div className="flex items-center gap-3 w-full lg:w-auto">
                                        <button 
                                            onClick={() => { setEditModeData({ org_id: selectedUnit.org_id?.toString() || '', comp_id: selectedUnit.comp_id || '' }); setIsEditing(!isEditing); }}
                                            className="flex-1 lg:flex-none px-6 py-3.5 bg-zinc-50 hover:bg-zinc-100 text-zinc-600 rounded-full font-bold text-[10px] uppercase tracking-widest transition-all ring-1 ring-zinc-100"
                                        >
                                            Configure
                                        </button>
                                        <button 
                                            onClick={() => {
                                                setReportTarget({ id: selectedUnit.id, name: selectedUnit.name, type: 'node' });
                                                setIsReportModalOpen(true);
                                            }}
                                            className="flex-1 lg:flex-none px-6 py-3.5 bg-zinc-900 text-white rounded-full font-bold text-[10px] uppercase tracking-widest transition-all shadow-lg shadow-zinc-900/10 active:scale-95"
                                        >
                                            Node Audit
                                        </button>
                                    </div>
                                </div>

                                {/* Main Metrics Display */}
                                <div className="flex flex-col lg:flex-row gap-8 lg:flex-1 min-h-0">
                                    <div className="grid grid-cols-2 lg:grid-cols-1 gap-4 lg:w-60 shrink-0">
                                        {currentMetrics.map((metric) => (
                                            <button 
                                                key={metric.id} 
                                                onClick={() => setSelectedMetric(metric.id as any)}
                                                className={cn(
                                                    "p-6 text-left rounded-[2rem] transition-all duration-300 flex flex-col justify-between items-start group relative overflow-hidden",
                                                    selectedMetric === metric.id 
                                                        ? 'bg-zinc-900 text-white shadow-2xl scale-[1.02] ring-1 ring-zinc-800' 
                                                        : 'bg-white/80 backdrop-blur-md text-zinc-500 border border-white hover:border-orange-200 hover:shadow-lg'
                                                )}
                                            >
                                                <div className="flex items-center justify-between w-full mb-6">
                                                    <div className={cn(
                                                        "w-10 h-10 rounded-2xl flex items-center justify-center transition-colors",
                                                        selectedMetric === metric.id ? 'bg-orange-500 text-white' : 'bg-zinc-50 text-zinc-400 group-hover:bg-orange-50 group-hover:text-orange-500'
                                                    )}>
                                                        {metric.icon}
                                                    </div>
                                                    <span className="text-[9px] font-bold uppercase tracking-[0.2em]">{metric.title}</span>
                                                </div>
                                                <div>
                                                    <p className={cn("text-[10px] font-bold uppercase tracking-widest mb-1 opacity-60")}>{metric.label}</p>
                                                    <p className="text-2xl font-bold font-mono tracking-tighter">
                                                        {metric.value} <span className="text-xs font-bold opacity-40">{metric.unit}</span>
                                                    </p>
                                                </div>
                                            </button>
                                        ))}
                                    </div>

                                    <div className="flex-1 bg-white border border-zinc-100 rounded-[2.5rem] p-6 lg:p-10 shadow-[0_8px_60px_-15px_rgba(0,0,0,0.03)] flex flex-col relative overflow-hidden min-h-[450px] lg:h-full">
                                        <div className="absolute top-0 right-0 w-64 h-64 bg-orange-500/5 blur-[80px] rounded-full -mr-32 -mt-32" />
                                        
                                        <div className="flex justify-between items-end mb-10 relative z-10">
                                            <div>
                                                <div className="flex items-center gap-2 mb-2">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse" />
                                                    <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.2em]">Live Telemetry Stream</p>
                                                </div>
                                                <h2 className="text-2xl font-bold text-zinc-900 tracking-tight">{activeMetricData?.label} <span className="text-zinc-300 font-medium">History</span></h2>
                                            </div>
                                            <div className="text-right">
                                                <span className="text-3xl lg:text-[2.5rem] font-bold font-mono text-zinc-900 tracking-tighter leading-none block">
                                                    {activeMetricData?.value}<span className="text-sm lg:text-base text-zinc-300 ml-1">{activeMetricData?.unit}</span>
                                                </span>
                                            </div>
                                        </div>

                                        <div className="flex-1 relative min-h-0 w-full">
                                            <UsageGraph data={usageData} metric={selectedMetric} className="h-full w-full" />
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        ) : (
                            <motion.div
                                key="fleet-overview"
                                initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.98 }}
                                className="flex-1 flex flex-col p-4 lg:p-10 min-h-0"
                            >
                                <div className="flex items-center justify-between mb-10 shrink-0">
                                    <div>
                                        <h2 className="text-4xl font-bold text-zinc-900 tracking-tight">Fleet Overview</h2>
                                        <p className="text-[10px] font-bold uppercase tracking-[0.3em] text-zinc-400 mt-2">Active Health Monitoring • {activeUnits} Online</p>
                                    </div>
                                    <div className="flex items-center gap-4 bg-white/70 backdrop-blur-md p-2 rounded-full border border-white/60 shadow-sm">
                                        <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-600 rounded-full text-[10px] font-bold uppercase tracking-widest">
                                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                                            {activeUnits} Online
                                        </div>
                                        <div className="flex items-center gap-2 px-4 py-2 bg-zinc-50 text-zinc-400 rounded-full text-[10px] font-bold uppercase tracking-widest">
                                            <div className="w-1.5 h-1.5 rounded-full bg-zinc-300" />
                                            {totalUnits - activeUnits} Offline
                                        </div>
                                    </div>
                                </div>

                                <div className="flex-1 overflow-y-auto custom-scrollbar">
                                    {units.length === 0 ? (
                                        <div className="flex-1 flex flex-col items-center justify-center p-20 bg-white/80 backdrop-blur-xl rounded-[3rem] border border-white text-center shadow-xl shadow-black/5">
                                            <div className="w-24 h-24 bg-zinc-50 rounded-[2rem] flex items-center justify-center mb-8 ring-1 ring-zinc-100">
                                                <Server className="w-10 h-10 text-zinc-300" />
                                            </div>
                                            <h2 className="text-2xl font-bold text-zinc-900 tracking-tight mb-3">Initialize Fleet</h2>
                                            <p className="text-zinc-500 max-w-xs text-sm font-medium leading-relaxed mb-10">Deploy your first telemetry monitor to begin tracking system health in real-time.</p>
                                            <button
                                                onClick={() => setIsAddNodeOpen(true)}
                                                className="bg-zinc-900 text-white rounded-full py-5 px-10 font-bold uppercase tracking-widest text-xs flex items-center gap-3 hover:bg-orange-500 transition-all shadow-2xl shadow-zinc-900/20 active:scale-95"
                                            >
                                                <Plus size={18} /> Deploy First Monitor
                                            </button>
                                        </div>
                                    ) : (
                                        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-6 pb-10">
                                            {sortedUnits.map((unit) => (
                                                <CompactStatCard key={unit.id} unit={unit} onClick={() => handleUnitToggle(unit)} />
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </main>
            </div>
        </div>
    )
}