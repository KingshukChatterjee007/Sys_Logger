'use client'

import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { Activity, Globe, ChevronRight, Cpu, Layers, Zap, Network, ShieldCheck, LayoutDashboard } from 'lucide-react'
import MockFleetGraphs from './components/MockFleetGraphs'

interface PricingPlan {
    plan_id: number;
    name: string;
    slug: string;
    price_monthly: number;
    node_limit: number;
    features: string[];
    is_active: boolean;
}

export default function HomeDashboard() {
    const [currentTime, setCurrentTime] = useState<string>('')
    const [plans, setPlans] = useState<PricingPlan[]>([])
    const [paymentLoading, setPaymentLoading] = useState<string | null>(null)
    const [isLoggedIn, setIsLoggedIn] = useState(false)

    useEffect(() => {
        setCurrentTime(new Date().toLocaleTimeString())
        const interval = setInterval(() => setCurrentTime(new Date().toLocaleTimeString()), 1000)
        
        // Load Razorpay Script
        const script = document.createElement('script');
        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
        script.async = true;
        document.body.appendChild(script);

        // Check Auth State
        setIsLoggedIn(!!localStorage.getItem('token'));

        // Fetch Dynamic Pricing
        fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/pricing`)
            .then(res => {
                if (!res.ok) throw new Error('Failed to fetch');
                return res.json();
            })
            .then(data => {
                if (Array.isArray(data) && data.length > 0) {
                    setPlans(data)
                } else {
                    throw new Error('No plans returned');
                }
            })
            .catch(err => {
                console.error("Error fetching pricing, applying fallback plans:", err);
                setPlans([
                    { plan_id: 2, name: "Pro", slug: "pro", price_monthly: 99, node_limit: 5, features: ["5 Active Nodes", "Advanced Metrics", "Priority Support"], is_active: true },
                    { plan_id: 3, name: "Business", slug: "business", price_monthly: 199, node_limit: 10, features: ["10 Nodes", "Global Fleet Control", "24/7 Support"], is_active: true }
                ]);
            })

        return () => {
            clearInterval(interval);
            if (document.body.contains(script)) {
                document.body.removeChild(script);
            }
        };
    }, [])

    const handlePayment = async (plan: PricingPlan) => {
        // Robust check for free plan
        if (Number(plan.price_monthly) === 0) {
            // If it's the free plan, we just redirect to login/register or fleet if already logged in
            const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
            window.location.href = token ? '/fleet' : '/login';
            return;
        }

        setPaymentLoading(plan.slug);
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                alert('Please sign in or create an account to purchase a plan.');
                window.location.href = '/login?next=pricing';
                return;
            }

            // 1. Create Order
            const orderResp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/payments/create-order`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ plan_slug: plan.slug })
            });
            
            const orderData = await orderResp.json();
            if (!orderResp.ok) throw new Error(orderData.error || 'Failed to create order');

            // 2. Open Razorpay Modal
            const options = {
                key: orderData.key_id,
                amount: orderData.amount,
                currency: orderData.currency,
                name: "SysLogger",
                description: `Upgrade to ${plan.name} Plan`,
                order_id: orderData.order_id,
                handler: async (response: any) => {
                    // 3. Verify Payment
                    const verifyResp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/payments/verify`, {
                        method: 'POST',
                        headers: { 
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_signature: response.razorpay_signature
                        })
                    });
                    
                    const verifyData = await verifyResp.json();
                    if (verifyResp.ok) {
                        alert('Payment successful! Your plan has been upgraded to ' + verifyData.tier);
                        window.location.href = '/fleet';
                    } else {
                        alert('Verification failed: ' + verifyData.error);
                    }
                },
                prefill: {
                    name: "",
                    email: ""
                },
                theme: {
                    color: "#f97316"
                }
            };

            const rzp = new (window as any).Razorpay(options);
            rzp.open();

        } catch (err: any) {
            console.error('Payment error:', err);
            alert(err.message || 'Payment failed to initiate');
        } finally {
            setPaymentLoading(null);
        }
    };

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-zinc-900 font-sans flex flex-col relative selection:bg-orange-500/30 overflow-hidden">

            {/* Cinematic Ambient Lighting (Light Theme) */}
            <div className="fixed inset-0 pointer-events-none z-0 flex items-center justify-center">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,0,0,0.03)_1px,transparent_1px)] bg-[size:24px_24px] opacity-100" />

                <motion.div
                    animate={{
                        scale: [1, 1.1, 1],
                        opacity: [0.05, 0.1, 0.05]
                    }}
                    transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                    className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-orange-500 rounded-full blur-[160px]"
                />
                <motion.div
                    animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.03, 0.08, 0.03]
                    }}
                    transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                    className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-emerald-500 rounded-full blur-[160px]"
                />
            </div>

            {/* Premium Glass Header */}
            <motion.header
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                className="px-6 lg:px-12 py-6 flex justify-between items-center z-20"
            >
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white backdrop-blur-md ring-1 ring-zinc-200/80 rounded-xl flex items-center justify-center shadow-sm">
                        <Activity className="w-5 h-5 text-orange-500" />
                    </div>
                    <span className="font-bold tracking-widest text-sm text-zinc-500 uppercase">
                        System Logger 
                    </span>
                </div>
                <div className="flex items-center gap-4">
                    <div className="hidden md:flex items-center gap-2 text-zinc-500 font-mono text-xs font-bold tracking-widest uppercase bg-white/60 backdrop-blur-md px-4 py-2 rounded-full ring-1 ring-zinc-200/80 shadow-sm">
                        <Globe className="w-3.5 h-3.5 animate-pulse text-emerald-500" />
                        {currentTime || "SYNCING..."}
                    </div>
                    <Link href={isLoggedIn ? "/fleet" : "/login"}>
                        <button className="px-6 py-2 bg-zinc-900 text-white rounded-full text-[10px] font-black uppercase tracking-widest hover:bg-zinc-800 transition-all shadow-lg shadow-zinc-500/10 active:scale-95">
                            {isLoggedIn ? 'Dashboard' : 'Sign In'}
                        </button>
                    </Link>
                </div>
            </motion.header>

            {/* Hero Section */}
            <main className="flex-1 flex flex-col items-center justify-center px-4 relative z-10 pt-20 pb-32 text-center">
                <div className="max-w-5xl mx-auto flex flex-col items-center">

                    {/* Live Badge */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
                        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 ring-1 ring-emerald-200 mb-8 backdrop-blur-md shadow-sm"
                    >
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                        </span>
                        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-600">System Online</span>
                    </motion.div>

                    <motion.h1
                        initial={{ opacity: 0, y: 20, filter: 'blur(10px)' }}
                        animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                        transition={{ duration: 1, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
                        className="text-5xl md:text-7xl lg:text-[7rem] font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-zinc-900 via-zinc-800 to-zinc-500 leading-[0.9] pb-4"
                    >
                        Telemetry. <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-orange-600">Perfected.</span>
                    </motion.h1>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 1, delay: 0.4, ease: [0.16, 1, 0.3, 1] }}
                        className="text-lg md:text-xl text-zinc-500 font-medium max-w-2xl mx-auto mb-12 tracking-wide leading-relaxed mt-4"
                    >
                        Monitor, manage, and optimize your entire compute fleet in real-time with Krishi Sahayogi & Nielit Bhubaneshwar.
                    </motion.p>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 1, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
                    >
                        <Link href={isLoggedIn ? "/fleet" : "/login"}>
                            <button className="group relative px-8 py-4 bg-zinc-900 text-white rounded-full font-black uppercase tracking-widest text-xs flex items-center gap-3 transition-all hover:scale-105 hover:bg-zinc-800 hover:shadow-[0_8px_30px_rgba(0,0,0,0.12)] overflow-hidden">
                                <span className="relative z-10 flex items-center gap-2">
                                    {isLoggedIn ? 'Access Fleet Hub' : 'Initialize Fleet Hub'}
                                    <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </span>
                                <div className="absolute inset-0 bg-gradient-to-r from-orange-500/20 to-emerald-500/20 translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-500 ease-in-out" />
                            </button>
                        </Link>
                    </motion.div>
                </div>

                {/* Metric Showcase Section */}
                <div className="mt-48 max-w-7xl mx-auto px-4 w-full relative">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {[
                            { 
                                icon: <Cpu className="w-6 h-6" />, 
                                title: "CPU Intelligence", 
                                desc: "Track per-core loads, thermal metrics, and process overhead in real-time.",
                                color: "text-orange-500",
                                bg: "bg-orange-50"
                            },
                            { 
                                icon: <Layers className="w-6 h-6" />, 
                                title: "Memory Dynamics", 
                                desc: "Visualize RAM pooling, swap usage, and leak detection across units.",
                                color: "text-emerald-500",
                                bg: "bg-emerald-50"
                            },
                            { 
                                icon: <Zap className="w-6 h-6" />, 
                                title: "GPU Acceleration", 
                                desc: "Full NVIDIA/CUDA workload monitoring for compute-heavy node clusters.",
                                color: "text-blue-500",
                                bg: "bg-blue-50"
                            },
                            { 
                                icon: <Network className="w-6 h-6" />, 
                                title: "Network Flux", 
                                desc: "High-precision bandwidth analysis and packet-loss tracking for remote nodes.",
                                color: "text-purple-500",
                                bg: "bg-purple-50"
                            }
                        ].map((metric, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 30 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.1, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                                className="group p-8 rounded-[2.5rem] bg-white ring-1 ring-zinc-200 shadow-sm hover:shadow-xl hover:ring-zinc-300 transition-all duration-500"
                            >
                                <div className={`w-14 h-14 rounded-2xl ${metric.bg} flex items-center justify-center ${metric.color} mb-6 group-hover:scale-110 transition-transform`}>
                                    {metric.icon}
                                </div>
                                <h3 className="text-lg font-black text-zinc-900 uppercase tracking-widest mb-3">{metric.title}</h3>
                                <p className="text-zinc-500 font-medium text-sm leading-relaxed">{metric.desc}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>

                {/* Architecture Highlights */}
                <div className="mt-48 max-w-7xl mx-auto px-4 w-full text-left">
                    <div className="flex flex-col lg:flex-row gap-12 lg:gap-24 items-center">
                        <div className="flex-1 lg:max-w-md">
                            <motion.div
                                initial={{ opacity: 0, x: -30 }}
                                whileInView={{ opacity: 1, x: 0 }}
                                viewport={{ once: true }}
                                className="space-y-8"
                            >
                                <div className="space-y-4">
                                    <span className="text-[10px] font-black uppercase tracking-[0.3em] text-orange-500">Fleet Architecture</span>
                                    <h2 className="text-4xl md:text-6xl font-black tracking-tighter text-zinc-900 leading-none">
                                        Scale from One <br /> to <span className="text-zinc-400">Thousands.</span>
                                    </h2>
                                </div>
                                
                                <div className="space-y-6">
                                    {[
                                        { title: "One-Click Deployment", desc: "Native installers for Windows and Linux ensure your fleet is online in seconds.", icon: <ChevronRight className="w-4 h-4" /> },
                                        { title: "Real-Time Sync", desc: "Ultra-low latency telemetry powered by WebSocket synchronization.", icon: <ChevronRight className="w-4 h-4" /> },
                                        { title: "Multi-Tenant Isolation", desc: "Securely manage multiple organizations and departments from a single hub.", icon: <ChevronRight className="w-4 h-4" /> }
                                    ].map((feature, i) => (
                                        <div key={i} className="flex gap-4 group">
                                            <div className="mt-1 w-5 h-5 rounded-full bg-zinc-900 flex items-center justify-center text-white shrink-0 group-hover:bg-orange-500 transition-colors">
                                                {feature.icon}
                                            </div>
                                            <div className="space-y-1">
                                                <h4 className="font-bold text-zinc-900 uppercase tracking-widest text-xs">{feature.title}</h4>
                                                <p className="text-zinc-500 text-sm leading-relaxed">{feature.desc}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>
                        </div>
                        
                        <div className="flex-[1.5] w-full relative">
                            <motion.div
                                initial={{ opacity: 0, scale: 0.9, rotate: -2 }}
                                whileInView={{ opacity: 1, scale: 1, rotate: 0 }}
                                viewport={{ once: true }}
                                className="relative p-3 bg-white ring-1 ring-zinc-200 rounded-[3rem] shadow-2xl overflow-hidden aspect-video flex items-center justify-center scale-105"
                            >
                                <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 to-emerald-500/5" />
                                <MockFleetGraphs />
                            </motion.div>
                        </div>
                    </div>
                </div>

                {/* Cross-Platform Support */}
                <div className="mt-48 max-w-5xl mx-auto px-4 w-full">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="bg-zinc-900 rounded-[3rem] p-12 md:p-20 relative overflow-hidden text-center"
                    >
                        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(249,115,22,0.15),transparent_70%)]" />
                        <div className="relative z-10 space-y-8">
                            <h2 className="text-3xl md:text-5xl font-black tracking-tight text-white uppercase">Universal Compatibility</h2>
                            <p className="text-zinc-400 max-w-2xl mx-auto text-lg leading-relaxed">
                                Our lightweight monitor agent runs everywhere. Deploy across your hybrid infrastructure with native support for all major operating systems.
                            </p>
                            <div className="flex flex-wrap justify-center gap-8 pt-8">
                                {[
                                    { name: "Windows", detail: "Full GPU/CPU/RAM Tracking" },
                                    { name: "Linux", detail: "Server & Edge Optimization" },
                                    { name: "macOS", detail: "Precision Core Monitoring" }
                                ].map((os, i) => (
                                    <div key={i} className="space-y-2">
                                        <div className="text-white font-black text-xl tracking-tighter italic">{os.name}</div>
                                        <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">{os.detail}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </motion.div>
                </div>

                {/* Pricing Section */}
                <div id="pricing" className="mt-40 max-w-6xl mx-auto px-4 w-full">
                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="mb-16"
                    >
                        <h2 className="text-3xl md:text-5xl font-black tracking-tight text-zinc-900 mb-4 uppercase">Plans & Pricing</h2>
                        <div className="w-20 h-1.5 bg-orange-500 mx-auto rounded-full" />
                    </motion.div>

                    <div className="flex flex-col md:flex-row justify-center gap-8 items-stretch max-w-5xl mx-auto">
                        {plans.map((plan, idx) => (
                            <motion.div
                                key={plan.plan_id}
                                    initial={{ opacity: 0, y: 20 }}
                                    whileInView={{ opacity: 1, y: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: idx * 0.1 }}
                                    className={`relative group p-8 rounded-[2.5rem] bg-white ring-1 ring-zinc-200 shadow-sm hover:shadow-xl hover:ring-orange-500/30 transition-all duration-500 overflow-hidden w-full max-w-sm ${plan.slug === 'pro' ? 'md:scale-105 z-10 ring-orange-200' : ''}`}
                                >
                                    {plan.slug === 'pro' && (
                                        <div className="absolute top-0 right-0 px-6 py-2 bg-gradient-to-r from-orange-500 to-orange-600 text-white text-[10px] font-black uppercase tracking-widest rounded-bl-3xl shadow-sm">
                                            Most Popular
                                        </div>
                                    )}
                                    
                                    <div className="text-left h-full flex flex-col">
                                        <h3 className="text-xl font-black text-zinc-900 uppercase tracking-wider mb-2">{plan.name}</h3>
                                        <div className="flex items-baseline gap-1 mb-6">
                                            <span className="text-4xl font-black text-zinc-900">₹{plan.price_monthly}</span>
                                            <span className="text-zinc-400 font-bold text-sm">/mo</span>
                                        </div>

                                        <div className="space-y-4 mb-10 flex-1">
                                            {Array.isArray(plan.features) && plan.features.map((feature, i) => (
                                                <div key={i} className="flex items-center gap-3 text-zinc-600">
                                                    <div className="w-5 h-5 rounded-full bg-orange-50 flex items-center justify-center shrink-0">
                                                        <div className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                                                    </div>
                                                    <span className="text-sm font-medium">{feature}</span>
                                                </div>
                                            ))}
                                        </div>

                                        <button 
                                            onClick={() => handlePayment(plan)}
                                            disabled={paymentLoading === plan.slug}
                                            className={`mt-auto w-full py-4 rounded-2xl font-black uppercase tracking-widest text-[10px] transition-all transform hover:scale-[1.02] active:scale-[0.98] ${plan.slug === 'pro' ? 'bg-zinc-900 text-white shadow-lg shadow-orange-500/10' : 'bg-zinc-50 text-zinc-600 ring-1 ring-zinc-200 hover:bg-white'}`}
                                        >
                                            {paymentLoading === plan.slug ? 'Processing...' : 'Join Now'}
                                        </button>
                                    </div>
                                </motion.div>
                            ))}
                    </div>
                </div>
            </main>

            {/* Minimalist Footer Dock */}
            <motion.footer
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1.2, delay: 0.8 }}
                className="py-12 relative z-10 flex flex-col items-center gap-8 mb-6"
            >
                <div className="flex items-center gap-8 px-8 py-0 bg-white/60 backdrop-blur-xl ring-1 ring-zinc-200/80 rounded-[2.5rem] shadow-[0_8px_40px_rgba(0,0,0,0.06)]">
                    <img src="/krishishayogi.png" alt="Krishi" className="h-28 object-contain opacity-60 hover:opacity-100 transition-opacity grayscale hover:grayscale-0 duration-300 mix-blend-multiply" />
                    <div className="w-[1px] h-10 bg-zinc-200" />
                    <img src="/Nielit_logo.jpeg" alt="NIELIT" className="h-10 object-contain opacity-40 hover:opacity-80 transition-opacity grayscale hover:grayscale-0 duration-300 mix-blend-multiply" />
                    <div className="w-[1px] h-10 bg-zinc-200" />
                    <img src="/India-AI_logo.jpeg" alt="India AI" className="h-8 object-contain opacity-40 hover:opacity-80 transition-opacity grayscale hover:grayscale-0 duration-300 mix-blend-multiply" />
                </div>
                <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.3em]">© 2026 System Logger • Precision Monitoring</p>
            </motion.footer>

        </div>
    )
}