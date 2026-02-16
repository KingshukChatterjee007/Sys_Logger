'use client'

import React from 'react'
import { Package, Monitor, Server, Globe, ChevronLeft, ShieldCheck, Zap, Terminal, CheckCircle2 } from 'lucide-react'
import Link from 'next/link'

export default function DeploymentPage() {
    return (
        <div className="min-h-screen bg-slate-900 text-slate-200 font-sans selection:bg-blue-500/30">
            {/* Header */}
            <header className="bg-slate-800/80 border-b border-slate-700 sticky top-0 z-20 backdrop-blur-xl">
                <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link
                            href="/"
                            className="p-2 hover:bg-slate-700 rounded-xl transition-colors text-slate-400 hover:text-white"
                        >
                            <ChevronLeft className="w-5 h-5" />
                        </Link>
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-600/20">
                                <Package className="w-5 h-5 text-white" />
                            </div>
                            <h1 className="text-xl font-black tracking-tighter uppercase text-white">Deployment Hub</h1>
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-5xl mx-auto px-6 py-12">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">

                    {/* Sidebar / Quick Links */}
                    <div className="lg:col-span-1 space-y-8">
                        <div className="bg-slate-800/40 border border-slate-700/50 rounded-3xl p-8 sticky top-28">
                            <h2 className="text-xs font-black text-slate-500 uppercase tracking-[0.3em] mb-6">Quick Actions</h2>
                            <div className="space-y-4">
                                <a href="#client" className="flex items-center gap-3 text-sm font-bold text-slate-400 hover:text-blue-400 transition-colors py-2 border-b border-slate-700/50">
                                    <Monitor className="w-4 h-4" /> Client Installation
                                </a>
                                <a href="#server" className="flex items-center gap-3 text-sm font-bold text-slate-400 hover:text-blue-400 transition-colors py-2 border-b border-slate-700/50">
                                    <Server className="w-4 h-4" /> Server Setup
                                </a>
                                <a href="#remote" className="flex items-center gap-3 text-sm font-bold text-slate-400 hover:text-blue-400 transition-colors py-2">
                                    <Globe className="w-4 h-4" /> Remote Access
                                </a>
                            </div>

                            <div className="mt-12 p-6 bg-blue-600/10 rounded-2xl border border-blue-500/20">
                                <Zap className="w-6 h-6 text-blue-500 mb-3" />
                                <h3 className="text-xs font-black text-blue-400 uppercase tracking-widest mb-1">Pro Tip</h3>
                                <p className="text-[11px] text-slate-400 leading-relaxed font-medium">Use Organization IDs to group computers by department or location automatically.</p>
                            </div>
                        </div>
                    </div>

                    {/* Content Section */}
                    <div className="lg:col-span-2 space-y-16 pb-24">

                        {/* Section 1: Client */}
                        <section id="client" className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                            <div className="flex items-center gap-4">
                                <div className="p-4 bg-green-500/10 rounded-2xl">
                                    <Monitor className="w-8 h-8 text-green-500" />
                                </div>
                                <div>
                                    <h2 className="text-3xl font-black text-white uppercase tracking-tighter">Client Installation</h2>
                                    <p className="text-slate-500 font-bold text-xs uppercase tracking-widest">End-User Application Setup</p>
                                </div>
                            </div>

                            <div className="bg-slate-800/40 border border-slate-700 rounded-3xl overflow-hidden">
                                <div className="p-8 border-b border-slate-700/50">
                                    <h3 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-4">Required Files</h3>
                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                        {['unit_client.py', 'requirements_client.txt', 'install_client.ps1'].map(f => (
                                            <div key={f} className="bg-slate-900/50 p-4 rounded-xl border border-slate-700/50 text-[11px] font-mono text-blue-400 flex items-center gap-3 leading-none">
                                                <Terminal className="w-3.5 h-3.5 text-slate-600" /> {f}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                <div className="p-8 space-y-6">
                                    <h3 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-2">Step-by-Step Guide</h3>
                                    {[
                                        "Extract the Sys_Logger_Client folder on the target computer.",
                                        "Right-click install_client.ps1 and select 'Run with PowerShell' (Administrator).",
                                        "During first run, enter the Organization ID and Computer ID when prompted.",
                                        "Verify registration on the central dashboard."
                                    ].map((step, i) => (
                                        <div key={i} className="flex gap-4">
                                            <div className="flex-shrink-0 w-6 h-6 bg-slate-700 rounded-full flex items-center justify-center text-[10px] font-black text-white">{i + 1}</div>
                                            <p className="text-sm text-slate-300 font-medium leading-relaxed">{step}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </section>

                        {/* Section 2: Server */}
                        <section id="server" className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-150">
                            <div className="flex items-center gap-4">
                                <div className="p-4 bg-blue-500/10 rounded-2xl">
                                    <Server className="w-8 h-8 text-blue-500" />
                                </div>
                                <div>
                                    <h2 className="text-3xl font-black text-white uppercase tracking-tighter">Server Deployment</h2>
                                    <p className="text-slate-500 font-bold text-xs uppercase tracking-widest">Central API & Dashboard Hub</p>
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div className="bg-slate-800/40 border border-slate-700 rounded-3xl p-8">
                                    <h3 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-6">Backend Initialization</h3>
                                    <div className="bg-slate-900 rounded-2xl p-6 font-mono text-xs border border-slate-700 shadow-inner space-y-2">
                                        <div className="text-slate-500"># Install dependencies</div>
                                        <div className="text-blue-400">pip install -r backend/requirements.txt</div>
                                        <div className="text-slate-500 mt-4"># Start the monitoring pulse</div>
                                        <div className="text-green-500">python backend/sys_logger.py</div>
                                    </div>
                                </div>

                                <div className="bg-slate-800/40 border border-slate-700 rounded-3xl p-8">
                                    <h3 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-6">Frontend Dashboard</h3>
                                    <div className="bg-slate-900 rounded-2xl p-6 font-mono text-xs border border-slate-700 shadow-inner space-y-2">
                                        <div className="text-slate-500"># Building the interface</div>
                                        <div className="text-blue-400">npm install && npm run build</div>
                                        <div className="text-slate-500 mt-4"># Launching production hub</div>
                                        <div className="text-green-500">npm run start</div>
                                    </div>
                                </div>
                            </div>
                        </section>

                        {/* Section 3: More Info */}
                        <section className="bg-gradient-to-br from-blue-600/20 to-cyan-600/20 border border-blue-500/20 rounded-3xl p-10 relative overflow-hidden group">
                            <div className="absolute top-0 right-0 p-10 opacity-5 group-hover:opacity-10 transition-opacity">
                                <ShieldCheck className="w-32 h-32 text-blue-500" />
                            </div>
                            <div className="relative z-10 flex flex-col items-center text-center space-y-6">
                                <div className="p-4 bg-blue-500 rounded-2xl shadow-xl shadow-blue-500/20">
                                    <CheckCircle2 className="w-10 h-10 text-white" />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-black text-white uppercase tracking-tighter mb-2">Systems Ready for Duty</h2>
                                    <p className="text-blue-200/60 max-w-lg mx-auto text-sm leading-relaxed font-medium">
                                        Your multi-tenant infrastructure is now ready for massive scaling. Start onboarding clients to see the pulse of your fleet.
                                    </p>
                                </div>
                                <Link href="/" className="px-8 py-3 bg-white text-blue-600 rounded-full font-black uppercase text-sm hover:scale-105 transition-transform">
                                    Return to Hub
                                </Link>
                            </div>
                        </section>
                    </div>
                </div>
            </main>
        </div>
    )
}
