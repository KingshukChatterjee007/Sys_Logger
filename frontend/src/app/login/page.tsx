'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, Lock, User, Eye, EyeOff, AlertCircle, ArrowRight } from 'lucide-react'
import Link from 'next/link'
import { useAuth } from '../components/AuthContext'

export default function LoginPage() {
    const { login } = useAuth()
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        const result = await login(username, password)
        if (!result.success) {
            setError(result.error || 'Invalid credentials')
        }
        setLoading(false)
    }

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-zinc-900 font-sans flex flex-col relative selection:bg-orange-500/30 overflow-hidden">
            {/* Ambient Lighting */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,0,0,0.03)_1px,transparent_1px)] bg-[size:24px_24px]" />
                <motion.div
                    animate={{ scale: [1, 1.1, 1], opacity: [0.05, 0.1, 0.05] }}
                    transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                    className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-orange-500 rounded-full blur-[160px]"
                />
                <motion.div
                    animate={{ scale: [1, 1.2, 1], opacity: [0.03, 0.08, 0.03] }}
                    transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                    className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-emerald-500 rounded-full blur-[160px]"
                />
            </div>

            {/* Header */}
            <motion.header
                initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                className="px-6 lg:px-12 py-6 flex justify-between items-center z-20"
            >
                <Link href="/" className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white backdrop-blur-md ring-1 ring-zinc-200/80 rounded-xl flex items-center justify-center shadow-sm">
                        <Activity className="w-5 h-5 text-orange-500" />
                    </div>
                    <span className="font-bold tracking-widest text-sm text-zinc-500 uppercase">
                        System Logger <span className="text-zinc-900">PRO</span>
                    </span>
                </Link>
            </motion.header>

            {/* Login Form */}
            <main className="flex-1 flex items-center justify-center px-4 relative z-10">
                <motion.div
                    initial={{ opacity: 0, y: 20, filter: 'blur(10px)' }}
                    animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                    className="w-full max-w-md"
                >
                    <div className="bg-white rounded-3xl ring-1 ring-zinc-200/80 shadow-[0_8px_30px_rgba(0,0,0,0.06)] p-8 lg:p-10">
                        <div className="text-center mb-8">
                            <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-orange-500/20">
                                <Lock className="w-8 h-8 text-white" />
                            </div>
                            <h1 className="text-2xl font-black tracking-tight uppercase">Sign In</h1>
                            <p className="text-sm text-zinc-500 mt-2">Access your monitoring dashboard</p>
                        </div>

                        {error && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
                                className="flex items-center gap-2 bg-red-50 text-red-600 rounded-xl px-4 py-3 mb-6 ring-1 ring-red-200/50"
                            >
                                <AlertCircle className="w-4 h-4 shrink-0" />
                                <span className="text-sm font-bold">{error}</span>
                            </motion.div>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-5">
                            <div>
                                <label className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em] mb-2 block">Username</label>
                                <div className="relative">
                                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                                    <input
                                        type="text"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        className="w-full bg-zinc-50 ring-1 ring-zinc-200 rounded-xl pl-11 pr-4 py-3.5 text-sm font-bold text-zinc-800 focus:ring-orange-500 focus:bg-white outline-none transition-all"
                                        placeholder="Enter username"
                                        required
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em] mb-2 block">Password</label>
                                <div className="relative">
                                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="w-full bg-zinc-50 ring-1 ring-zinc-200 rounded-xl pl-11 pr-12 py-3.5 text-sm font-bold text-zinc-800 focus:ring-orange-500 focus:bg-white outline-none transition-all"
                                        placeholder="Enter password"
                                        required
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 transition-colors"
                                    >
                                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                    </button>
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full bg-zinc-900 hover:bg-zinc-800 text-white rounded-xl py-3.5 text-xs font-black uppercase tracking-widest flex items-center justify-center gap-2 transition-all hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed group"
                            >
                                {loading ? (
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                ) : (
                                    <>
                                        Sign In
                                        <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                    </>
                                )}
                            </button>
                        </form>

                        <div className="mt-6 text-center">
                            <Link href="/reset-password" className="text-xs font-bold text-zinc-500 hover:text-orange-600 transition-colors uppercase tracking-wider">
                                Forgot Password?
                            </Link>
                        </div>
                    </div>
                </motion.div>
            </main>
        </div>
    )
}
