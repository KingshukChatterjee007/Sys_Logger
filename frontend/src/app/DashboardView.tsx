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
    Terminal, Pencil, Trash2, X, Save, Activity, Menu, ArrowLeft, Shield, LogOut
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

// --- FIXED DUMMY DATA (Moved outside to prevent hydration mismatch) ---
const DUMMY_UNITS: Unit[] = [
    {
        id: 'dummy-1',
        name: 'Production/Main-Frame',
        status: 'online',
        ip: '192.168.1.105',
        last_seen: '2026-04-08T14:17:00.000Z',
        metrics: { cpu: 42, ram: 65, gpu: 12, network_rx: 4.5, network_tx: 1.2 }
    },
    {
        id: 'dummy-2',
        name: 'Edge/Sensor-Alpha',
        status: 'online',
        ip: '10.0.0.42',
        last_seen: '2026-04-08T14:17:00.000Z',
        metrics: { cpu: 8, ram: 12, gpu: 0, network_rx: 0.2, network_tx: 0.1 }
    },
    {
        id: 'dummy-3',
        name: 'Cloud/Database-Relay',
        status: 'offline',
        ip: '172.16.0.5',
        last_seen: '2026-04-08T13:17:00.000Z',
        metrics: { cpu: 0, ram: 0, gpu: 0, network_rx: 0, network_tx: 0 }
    },
    {
        id: 'dummy-4',
        name: 'Dev/Test-Environment',
        status: 'online',
        ip: '127.0.0.1',
        last_seen: '2026-04-08T14:17:00.000Z',
        metrics: { cpu: 95, ram: 88, gpu: 75, network_rx: 24.8, network_tx: 15.2 }
    }
];
// ----------------------------------------------------------------------

const CompactStatCard = ({ unit, onClick }: { unit: Unit; onClick: () => void }) => {
    const isOnline = unit.status === 'online';
    const metrics = unit.metrics;

    return (
        <motion.button
            whileHover={{ scale: 1.02, y: -4 }}
            whileTap={{ scale: 0.98 }}
            onClick={onClick}
            className={cn(
                "flex flex-col p-5 bg-white rounded-3xl ring-1 text-left group overflow-hidden relative transition-shadow duration-300 hover:z-20",
                isOnline
                    ? "ring-zinc-200 hover:ring-orange-400 hover:shadow-[0_20px_40px_-15px_rgba(249,115,22,0.1)]"
                    : "ring-zinc-100 opacity-60 hover:opacity-100 grayscale hover:grayscale-0"
            )}
        >
            {isOnline && (
                <div className="absolute top-0 right-0 w-24 h-24 bg-orange-500/5 blur-2xl rounded-full -mr-12 -mt-12 group-hover:bg-orange-500/10 transition-colors" />
            )}

            <div className="flex justify-between items-center mb-4 relative z-10">
                <div className="flex items-center gap-2.5 min-w-0">
                    <div className={cn(
                        "w-2.5 h-2.5 rounded-full ring-4 shadow-sm",
                        isOnline ? "bg-emerald-500 ring-emerald-500/20 animate-pulse" : "bg-zinc-300 ring-zinc-300/20"
                    )} />
                    <h3 className="font-black text-[11px] uppercase tracking-wider text-zinc-800 truncate">{unit.name.split('/').pop()}</h3>
                </div>
                <div className="p-1.5 rounded-lg bg-zinc-50 text-zinc-400 group-hover:text-orange-500 group-hover:bg-orange-50 transition-all">
                    <ChevronRight size={14} />
                </div>
            </div>

            <div className="grid grid-cols-2 gap-y-4 gap-x-6 relative z-10">
                <div className="flex flex-col gap-0.5">
                    <span className="text-[8px] font-black text-zinc-400 uppercase tracking-widest flex items-center gap-1">
                        <Cpu size={10} className="text-zinc-300" /> CPU
                    </span>
                    <span className="text-lg font-black font-mono text-zinc-900 tracking-tighter leading-none">
                        {metrics?.cpu !== undefined ? metrics.cpu.toFixed(0) : '--'}<span className="text-[10px] text-zinc-400 font-bold ml-0.5">%</span>
                    </span>
                </div>
                <div className="flex flex-col gap-0.5 items-end">
                    <span className="text-[8px] font-black text-zinc-400 uppercase tracking-widest flex items-center gap-1">
                        <HardDrive size={10} className="text-zinc-300" /> RAM
                    </span>
                    <span className="text-lg font-black font-mono text-zinc-900 tracking-tighter leading-none">
                        {metrics?.ram !== undefined ? metrics.ram.toFixed(0) : '--'}<span className="text-[10px] text-zinc-400 font-bold ml-0.5">%</span>
                    </span>
                </div>
                <div className="flex flex-col gap-0.5">
                    <span className="text-[8px] font-black text-zinc-400 uppercase tracking-widest flex items-center gap-1">
                        <Zap size={10} className="text-zinc-300" /> GPU
                    </span>
                    <span className="text-lg font-black font-mono text-zinc-900 tracking-tighter leading-none">
                        {metrics?.gpu !== undefined ? metrics.gpu.toFixed(0) : '--'}<span className="text-[10px] text-zinc-400 font-bold ml-0.5">%</span>
                    </span>
                </div>
                <div className="flex flex-col gap-0.5 items-end">
                    <span className="text-[8px] font-black text-zinc-400 uppercase tracking-widest flex items-center gap-1">
                        <Wifi size={10} className="text-zinc-300" /> NET
                    </span>
                    <span className="text-lg font-black font-mono text-zinc-900 tracking-tighter leading-none">
                        {metrics?.network_rx !== undefined ? metrics.network_rx.toFixed(1) : '--'}<span className="text-[8px] text-zinc-400 font-bold ml-0.5">MB/s</span>
                    </span>
                </div>
            </div>

            <div className="mt-4 pt-4 border-t border-zinc-50 flex items-center justify-between text-[9px] font-bold text-zinc-400">
                <span className="truncate max-w-[100px]">{unit.ip || 'no-ip'}</span>
                <span suppressHydrationWarning>{unit.last_seen ? new Date(unit.last_seen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'never'}</span>
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
        if (selectedUnit && !selectedUnit.id.startsWith('dummy-')) {
            apiUsage.setSelectedUnitId(selectedUnit.id);
        } else {
            apiUsage.setSelectedUnitId(null);
        }
    }, [selectedUnit, apiUsage]);

    // Determine which data to use
    const units = [...apiUnits.units, ...DUMMY_UNITS]

    // Sync mock data for dummy units
    useEffect(() => {
        if (selectedUnit?.id.startsWith('dummy-')) {
            const now = Date.now();
            const fakeData: UsageData[] = Array.from({ length: 100 }).map((_, i) => {
                const ts = new Date(now - (100 - i) * 2000).toISOString();
                const m = selectedUnit.metrics || { cpu: 0, ram: 0, gpu: 0, network_rx: 0, network_tx: 0 };
                const jitter = (val: number, range: number) => Math.max(0, Math.min(100, val + (Math.random() * range - range / 2)));
                return {
                    timestamp: ts,
                    cpu: jitter(m.cpu, 15),
                    ram: jitter(m.ram, 5),
                    gpu_load: jitter(m.gpu, 10),
                    network_rx: Math.max(0, m.network_rx + (Math.random() * 0.5 - 0.25)),
                    network_tx: Math.max(0, m.network_tx + (Math.random() * 0.1 - 0.05))
                } as any;
            });
            setMockUsageData(fakeData);
        } else {
            setMockUsageData([]);
        }
    }, [selectedUnit]);

    const usageData = selectedUnit?.id.startsWith('dummy-') ? mockUsageData : apiUsage.data
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
    const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState(false)
    const [plans, setPlans] = useState<PricingPlan[]>([])
    const [paymentLoading, setPaymentLoading] = useState<string | null>(null)

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

                        <Link
                            href="/"
                            className="hidden sm:flex items-center justify-center w-10 h-10 bg-zinc-100 text-zinc-600 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors shadow-sm"
                            title="Return to Home"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </Link>

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
                    "fixed inset-y-0 left-0 z-[110] w-[85%] sm:w-80 bg-white/40 backdrop-blur-3xl shadow-[0_8px_32px_0_rgba(249,115,22,0.15)] lg:border border-white/60 lg:ring-1 lg:ring-white/40 lg:rounded-[2.5rem] flex flex-col shrink-0 overflow-hidden lg:relative lg:translate-x-0 transition-transform duration-300 ease-in-out",
                    isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
                )}>
                    <div className="flex items-center justify-between p-4 border-b border-white/60 lg:hidden bg-white/60 backdrop-blur-md">
                        <span className="font-black text-zinc-800 text-xs tracking-widest uppercase flex items-center gap-2">
                            <Activity size={16} className="text-orange-500" /> Fleet Menu
                        </span>
                        <button
                            onClick={() => setIsMobileMenuOpen(false)}
                            className="p-1.5 text-zinc-400 hover:text-orange-600 bg-white/50 hover:bg-white/90 rounded-xl transition-all shadow-sm"
                        >
                            <X size={18} />
                        </button>
                    </div>

                    <div className="p-5 lg:p-6 border-b border-white/60 bg-gradient-to-br from-white/70 to-white/30 backdrop-blur-xl shadow-sm z-10 relative">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-orange-400/10 rounded-bl-full blur-2xl pointer-events-none" />
                        <div className="flex justify-between items-end mb-4 relative z-10">
                            <h3 className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em]">Network Status</h3>
                            <span className="px-3 py-1 rounded-lg bg-white/80 backdrop-blur-sm ring-1 ring-white shadow-sm text-[11px] font-black text-zinc-800">
                                {activeUnits} <span className="text-zinc-400 font-bold">/ {totalUnits}</span>
                            </span>
                        </div>
                        <div className="w-full bg-black/5 rounded-full h-2 overflow-hidden shadow-inner relative z-10 p-0.5">
                            <div
                                className="bg-gradient-to-r from-orange-400 to-orange-500 h-full rounded-full transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(249,115,22,0.5)] relative"
                                style={{ width: `${totalUnits > 0 ? (activeUnits / totalUnits) * 100 : 0}%` }}
                            >
                                <div className="absolute top-0 right-0 bottom-0 w-4 bg-white/30 blur-[2px]" />
                            </div>
                        </div>
                    </div>

                    {/* Add Monitor & Management Buttons */}
                    <div className="px-4 lg:px-5 flex flex-col gap-3 py-4 bg-white/20">
                        <button
                            onClick={() => setIsAddNodeOpen(true)}
                            className="w-full py-4 bg-gradient-to-r from-zinc-900 to-zinc-800 text-white rounded-[1.25rem] font-black uppercase tracking-widest text-[11px] flex items-center justify-center gap-2 hover:shadow-[0_8px_25px_rgba(0,0,0,0.15)] hover:scale-[1.02] active:scale-95 transition-all duration-300 group ring-1 ring-zinc-800/50"
                        >
                            <Zap className="w-4 h-4 text-orange-400 group-hover:text-orange-300 group-hover:drop-shadow-[0_0_8px_rgba(251,146,60,0.8)] transition-all" />
                            Deploy Monitor
                        </button>

                        {user?.role === 'ROOT' && (
                            <button
                                onClick={() => {
                                    setActiveTab(activeTab === 'management' ? 'metrics' : 'management');
                                    setIsMobileMenuOpen(false);
                                }}
                                className={cn(
                                    "w-full py-3.5 rounded-[1.25rem] font-black uppercase tracking-widest text-[10px] flex items-center justify-center gap-2 transition-all duration-300 ring-1 shadow-sm hover:scale-[1.02] active:scale-95",
                                    activeTab === 'management'
                                        ? "bg-gradient-to-br from-orange-400 to-orange-500 text-white shadow-[0_4px_15px_rgba(249,115,22,0.3)] ring-orange-400/50"
                                        : "bg-white/60 backdrop-blur-md text-zinc-600 hover:bg-white hover:text-orange-500 ring-white hover:shadow-[0_8px_20px_rgba(0,0,0,0.08)]"
                                )}
                            >
                                <Shield className="w-4 h-4" />
                                {activeTab === 'management' ? 'Exit Management' : 'System Management'}
                            </button>
                        )}
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 lg:p-5 space-y-4 lg:space-y-6 custom-scrollbar bg-white/10 relative">
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
                                units.reduce((acc, unit) => {
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

                    {/* Constant Professional Logo Section */}
                    <div className="relative border-t border-white/60 flex flex-col items-center justify-center shrink-0 z-10 py-6 px-4 overflow-hidden bg-white/30 backdrop-blur-md">
                        <div className="absolute inset-0 bg-gradient-to-t from-white/80 to-transparent z-0 pointer-events-none" />
                        <div className="flex items-center justify-between w-full gap-3 mb-5 relative z-10">
                            <div className="flex-1 h-14 flex items-center justify-center p-1 transition-transform hover:scale-105">
                                <img
                                    src="/krishishayogi.png"
                                    alt="Krishi Sahayogi"
                                    className="max-h-full max-w-full object-contain drop-shadow-lg"
                                />
                            </div>
                            <div className="flex-1 h-16 rounded-[1rem] bg-white/80 backdrop-blur-xl ring-1 ring-white flex items-center justify-center p-2 shadow-[0_4px_15px_rgba(0,0,0,0.05)] transition-all hover:scale-110 hover:shadow-[0_8px_25px_rgba(0,0,0,0.1)]">
                                <img
                                    src="/Nielit_logo.jpeg"
                                    alt="NIELIT"
                                    className="h-full w-full object-contain mix-blend-multiply opacity-95"
                                />
                            </div>
                            <div className="flex-1 h-16 rounded-[1rem] bg-white/80 backdrop-blur-xl ring-1 ring-white flex items-center justify-center p-2 shadow-[0_4px_15px_rgba(0,0,0,0.05)] transition-all hover:scale-110 hover:shadow-[0_8px_25px_rgba(0,0,0,0.1)]">
                                <img
                                    src="/India-AI_logo.jpeg"
                                    alt="India AI"
                                    className="h-full w-full object-contain mix-blend-multiply opacity-95"
                                />
                            </div>
                        </div>
                        <div className="text-center space-y-1.5 relative z-10">
                            <p className="text-[9px] font-black uppercase tracking-[0.3em] text-zinc-500">
                                Built by <span className="text-orange-500 font-black drop-shadow-sm">Krishi Sahayogi</span>
                            </p>
                            <p className="text-[8px] text-zinc-400 font-black tracking-[0.4em] uppercase">
                                NIELIT Bhubaneswar
                            </p>
                        </div>
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
                                className="absolute inset-0 bg-zinc-900/40 backdrop-blur-sm"
                            />
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                                className="relative w-full max-w-md bg-white rounded-[2.5rem] shadow-[0_32px_64px_-16px_rgba(0,0,0,0.2)] p-10 overflow-hidden"
                            >
                                <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-orange-500 to-emerald-500" />

                                <div className="flex justify-between items-start mb-8">
                                    <div className="p-3 bg-zinc-900 rounded-2xl shadow-lg shadow-zinc-900/20">
                                        <Activity className="w-6 h-6 text-orange-500" />
                                    </div>
                                    <button
                                        onClick={() => setIsAddNodeOpen(false)}
                                        className="p-2 text-zinc-400 hover:text-zinc-900 hover:bg-zinc-100 rounded-xl transition-all"
                                    >
                                        <X size={20} />
                                    </button>
                                </div>

                                <h2 className="text-2xl font-black text-zinc-900 mb-2 tracking-tight">Add New Monitor.</h2>
                                <p className="text-sm font-medium text-zinc-500 mb-8">Deploy a telemetry agent to your system</p>

                                <div className="space-y-6">
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black uppercase tracking-widest text-zinc-400 ml-4">Unit Identifier</label>
                                        <div className="relative">
                                            <Terminal className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                                            <input
                                                type="text"
                                                value={newNodeName}
                                                onChange={(e) => setNewNodeName(e.target.value)}
                                                className="w-full bg-zinc-50 border-none ring-1 ring-zinc-200 rounded-2xl py-4 pl-12 pr-4 text-sm text-zinc-900 focus:ring-2 focus:ring-orange-500/20 transition-all font-bold placeholder:text-zinc-300"
                                                placeholder="e.g. primary-server"
                                            />
                                        </div>
                                    </div>

                                    {addNodeError && (
                                        <div className="flex items-center gap-2 bg-red-50 text-red-600 p-4 rounded-2xl text-[11px] font-black ring-1 ring-red-100 animate-shake">
                                            <AlertTriangle className="w-4 h-4" />
                                            {addNodeError.toUpperCase()}
                                        </div>
                                    )}

                                    <div className="p-5 bg-orange-50/50 rounded-2xl border border-orange-100 flex flex-col gap-3">
                                        <div className="flex items-center gap-3">
                                            <div className="p-1.5 bg-orange-500 rounded-lg shadow-sm">
                                                <Download className="w-3 h-3 text-white" />
                                            </div>
                                            <span className="text-[10px] font-black uppercase tracking-widest text-orange-600">Generated Bundle</span>
                                        </div>
                                        <p className="text-[11px] text-zinc-600 font-medium leading-relaxed">
                                            We will generate a specialized ZIP package pre-configured for your account. Simply extract and run <code className="font-black text-orange-600">install.bat</code>.
                                        </p>
                                    </div>

                                    <button
                                        onClick={handleAddNode}
                                        disabled={isDownloading}
                                        className="w-full bg-zinc-900 text-white rounded-2xl py-5 font-black uppercase tracking-widest text-xs flex items-center justify-center gap-3 hover:bg-zinc-800 transition-all disabled:opacity-50 group shadow-xl shadow-zinc-900/10"
                                    >
                                        {isDownloading ? (
                                            <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                        ) : (
                                            <>
                                                Download Installer
                                                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                            </>
                                        )}
                                    </button>
                                </div>
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

                                {selectedUnit.status === 'pending' ? (
                                    <div className="flex-1 flex items-center justify-center p-4 lg:p-8">
                                        <div className="max-w-xl w-full bg-white rounded-[2.5rem] border border-zinc-200/60 p-10 lg:p-12 text-center shadow-sm relative overflow-hidden">
                                            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-orange-500/20 via-orange-500 to-orange-500/20" />

                                            <div className="mb-8 relative inline-block">
                                                <div className="w-24 h-24 bg-orange-50 rounded-full flex items-center justify-center ring-4 ring-white shadow-xl">
                                                    <Download className="w-10 h-10 text-orange-500 animate-bounce" />
                                                </div>
                                                <div className="absolute -bottom-2 -right-2 bg-zinc-900 text-white p-2 rounded-xl shadow-lg ring-4 ring-white">
                                                    <Shield className="w-4 h-4 text-emerald-400" />
                                                </div>
                                            </div>

                                            <h2 className="text-3xl font-black text-zinc-900 mb-4 tracking-tight">Awaiting Installation.</h2>
                                            <p className="text-zinc-500 font-medium mb-10 text-sm lg:text-base leading-relaxed">
                                                We've registered your unit <span className="text-zinc-900 font-black px-2 py-1 bg-zinc-100 rounded-lg">{selectedUnit.name.split('/').pop()}</span>.
                                                Now, you need to deploy the telemetry agent to start receiving live metrics.
                                            </p>

                                            <div className="space-y-4 mb-10">
                                                <div className="flex items-start gap-4 text-left p-5 bg-zinc-50 rounded-2xl border border-zinc-100 group hover:border-orange-200 transition-colors">
                                                    <div className="w-8 h-8 rounded-lg bg-zinc-900 text-white flex items-center justify-center text-xs font-black shrink-0 shadow-md">1</div>
                                                    <div>
                                                        <p className="text-[11px] font-black uppercase tracking-widest text-zinc-400 mb-1">Transfer Bundle</p>
                                                        <p className="text-xs font-bold text-zinc-700">Move the downloaded ZIP to your target server and extract it.</p>
                                                    </div>
                                                </div>
                                                <div className="flex items-start gap-4 text-left p-5 bg-zinc-50 rounded-2xl border border-zinc-100 group hover:border-orange-200 transition-colors">
                                                    <div className="w-8 h-8 rounded-lg bg-zinc-900 text-white flex items-center justify-center text-xs font-black shrink-0 shadow-md">2</div>
                                                    <div>
                                                        <p className="text-[11px] font-black uppercase tracking-widest text-zinc-400 mb-1">Single Command Install</p>
                                                        <p className="text-xs font-bold text-zinc-700">Open a terminal in the folder and run <code className="text-orange-600 font-black">install.bat</code>.</p>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex flex-col sm:flex-row gap-3">
                                                <button
                                                    onClick={() => downloadInstaller(selectedUnit.name.split('/').pop() || '')}
                                                    disabled={isDownloading}
                                                    className="flex-1 bg-zinc-900 text-white rounded-2xl py-5 px-8 font-black uppercase tracking-widest text-[11px] flex items-center justify-center gap-3 hover:bg-zinc-800 transition-all shadow-xl shadow-zinc-900/10 disabled:opacity-50"
                                                >
                                                    {isDownloading ? (
                                                        <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                                    ) : (
                                                        <>
                                                            <Download className="w-4 h-4" />
                                                            Download Installer Again
                                                        </>
                                                    )}
                                                </button>
                                                <button
                                                    onClick={handleDeleteUnit}
                                                    className="px-8 bg-zinc-100 hover:bg-red-50 hover:text-red-600 text-zinc-500 rounded-2xl py-5 font-black uppercase tracking-widest text-[11px] transition-all"
                                                >
                                                    Cancel Setup
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ) : activeTab === 'metrics' ? (
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
                            <motion.div
                                key="fleet-overview"
                                initial={{ opacity: 0, scale: 0.98 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.98 }}
                                className="flex-1 flex flex-col min-h-0"
                            >
                                <div className="flex items-center justify-between mb-6 shrink-0 pt-2 px-1">
                                    <div>
                                        <h2 className="text-2xl lg:text-3xl font-black text-zinc-900 tracking-tight uppercase">Fleet Overview</h2>
                                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-400 mt-1">Real-time health monitoring for {units.length} active nodes</p>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className="px-4 py-2 bg-white ring-1 ring-zinc-200 rounded-xl shadow-sm flex items-center gap-3">
                                            <div className="flex items-center gap-1.5">
                                                <div className="w-2 h-2 rounded-full bg-emerald-500" />
                                                <span className="text-[10px] font-black text-zinc-800 uppercase">{activeUnits} Online</span>
                                            </div>
                                            <div className="w-[1px] h-3 bg-zinc-200" />
                                            <div className="flex items-center gap-1.5">
                                                <div className="w-2 h-2 rounded-full bg-zinc-300" />
                                                <span className="text-[10px] font-black text-zinc-500 uppercase">{totalUnits - activeUnits} Offline</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 p-1 pt-4">
                                    {units.length === 0 ? (
                                        <div className="flex-1 flex flex-col items-center justify-center p-12 bg-white rounded-3xl ring-1 ring-zinc-200/50 text-center shadow-sm">
                                            <div className="mb-6 p-6 bg-zinc-50 rounded-full ring-1 ring-zinc-100 shadow-inner">
                                                <Server className="w-12 h-12 text-zinc-300" />
                                            </div>
                                            <h2 className="text-xl font-black text-zinc-900 tracking-tight uppercase mb-2">No nodes found</h2>
                                            <p className="text-zinc-500 max-w-sm text-xs font-medium leading-relaxed mb-8">
                                                Start by deploying a monitor to your first system to see real-time statistics here.
                                            </p>
                                            <button
                                                onClick={() => setIsAddNodeOpen(true)}
                                                className="bg-zinc-900 text-white rounded-2xl py-4 px-8 font-black uppercase tracking-widest text-[11px] flex items-center justify-center gap-2 hover:bg-zinc-800 transition-all shadow-xl shadow-zinc-900/10"
                                            >
                                                <Zap className="w-4 h-4 text-orange-400" /> Deploy First Monitor
                                            </button>
                                        </div>
                                    ) : (
                                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4 lg:gap-5 pb-8">
                                            {units.map((unit) => (
                                                <CompactStatCard
                                                    key={unit.id}
                                                    unit={unit}
                                                    onClick={() => handleUnitToggle(unit)}
                                                />
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