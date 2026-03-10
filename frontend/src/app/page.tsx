'use client'

import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { Activity, Globe, ChevronRight } from 'lucide-react'

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

    useEffect(() => {
        setCurrentTime(new Date().toLocaleTimeString())
        const interval = setInterval(() => setCurrentTime(new Date().toLocaleTimeString()), 1000)
        
        // Fetch Dynamic Pricing
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5010'}/api/pricing`)
            .then(res => res.json())
            .then(data => {
                if (Array.isArray(data)) setPlans(data)
            })
            .catch(err => console.error("Error fetching pricing:", err))

        return () => clearInterval(interval)
    }, [])

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
                        System Logger <span className="text-zinc-900">PRO</span>
                    </span>
                </div>
                <div className="flex items-center gap-2 text-zinc-500 font-mono text-xs font-bold tracking-widest uppercase bg-white/60 backdrop-blur-md px-4 py-2 rounded-full ring-1 ring-zinc-200/80 shadow-sm">
                    <Globe className="w-3.5 h-3.5 animate-pulse text-emerald-500" />
                    {currentTime || "SYNCING..."}
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
                        <Link href="/login">
                            <button className="group relative px-8 py-4 bg-zinc-900 text-white rounded-full font-black uppercase tracking-widest text-xs flex items-center gap-3 transition-all hover:scale-105 hover:bg-zinc-800 hover:shadow-[0_8px_30px_rgba(0,0,0,0.12)] overflow-hidden">
                                <span className="relative z-10 flex items-center gap-2">
                                    Initialize Fleet Hub
                                    <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </span>
                                <div className="absolute inset-0 bg-gradient-to-r from-orange-500/20 to-emerald-500/20 translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-500 ease-in-out" />
                            </button>
                        </Link>
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

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {plans.map((plan, idx) => (
                            <motion.div
                                key={plan.plan_id}
                                    initial={{ opacity: 0, y: 20 }}
                                    whileInView={{ opacity: 1, y: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: idx * 0.1 }}
                                    className={`relative group p-8 rounded-[2.5rem] bg-white ring-1 ring-zinc-200 shadow-sm hover:shadow-xl hover:ring-orange-500/30 transition-all duration-500 overflow-hidden ${plan.slug === 'pro' ? 'md:scale-105 z-10 ring-orange-200' : ''}`}
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

                                        <Link href="/login" className="mt-auto block w-full">
                                            <button className={`w-full py-4 rounded-2xl font-black uppercase tracking-widest text-[10px] transition-all transform hover:scale-[1.02] active:scale-[0.98] ${plan.slug === 'pro' ? 'bg-zinc-900 text-white shadow-lg shadow-orange-500/10' : 'bg-zinc-50 text-zinc-600 ring-1 ring-zinc-200 hover:bg-white'}`}>
                                                Join Now
                                            </button>
                                        </Link>
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
                <div className="flex items-center gap-8 px-8 py-4 bg-white/60 backdrop-blur-xl ring-1 ring-zinc-200/80 rounded-3xl shadow-[0_4px_20px_rgba(0,0,0,0.04)]">
                    <img src="/krishishayogi.png" alt="Krishi" className="h-6 object-contain opacity-60 hover:opacity-100 transition-opacity grayscale hover:grayscale-0 duration-300 mix-blend-multiply" />
                    <div className="w-[1px] h-6 bg-zinc-200" />
                    <img src="/Nielit_logo.jpeg" alt="NIELIT" className="h-6 object-contain opacity-60 hover:opacity-100 transition-opacity grayscale hover:grayscale-0 duration-300 mix-blend-multiply" />
                    <div className="w-[1px] h-6 bg-zinc-200" />
                    <img src="/India-AI_logo.jpeg" alt="India AI" className="h-6 object-contain opacity-60 hover:opacity-100 transition-opacity grayscale hover:grayscale-0 duration-300 mix-blend-multiply" />
                </div>
                <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.3em]">© 2026 System Logger Pro • Precision Monitoring</p>
            </motion.footer>

        </div>
    )
}