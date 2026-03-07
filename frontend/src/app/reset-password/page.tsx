'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, Lock, Mail, ArrowLeft, CheckCircle, AlertCircle } from 'lucide-react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'

export default function ResetPasswordPage() {
    const searchParams = useSearchParams()
    const token = searchParams.get('token')

    // If token present → reset form, else → forgot password (email) form
    return token ? <ResetForm token={token} /> : <ForgotForm />
}

function ForgotForm() {
    const [email, setEmail] = useState('')
    const [loading, setLoading] = useState(false)
    const [sent, setSent] = useState(false)
    const [error, setError] = useState('')

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        try {
            const res = await fetch('/api/auth/forgot-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            })
            if (res.ok) setSent(true)
            else {
                const data = await res.json()
                setError(data.error || 'Failed to send reset email')
            }
        } catch {
            setError('Network error')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-zinc-900 font-sans flex flex-col relative overflow-hidden">
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,0,0,0.03)_1px,transparent_1px)] bg-[size:24px_24px]" />
                <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-orange-500/5 rounded-full blur-[160px]" />
            </div>

            <header className="px-6 lg:px-12 py-6 z-20">
                <Link href="/login" className="flex items-center gap-2 text-zinc-500 hover:text-orange-600 transition-colors text-sm font-bold">
                    <ArrowLeft className="w-4 h-4" /> Back to Login
                </Link>
            </header>

            <main className="flex-1 flex items-center justify-center px-4 relative z-10">
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
                    <div className="bg-white rounded-3xl ring-1 ring-zinc-200/80 shadow-[0_8px_30px_rgba(0,0,0,0.06)] p-8">
                        <div className="text-center mb-6">
                            <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-orange-500/20">
                                <Mail className="w-8 h-8 text-white" />
                            </div>
                            <h1 className="text-2xl font-black tracking-tight uppercase">Forgot Password</h1>
                            <p className="text-sm text-zinc-500 mt-2">Enter your email to receive a reset link</p>
                        </div>

                        {sent ? (
                            <div className="text-center py-4">
                                <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
                                <p className="font-bold text-zinc-700">Check your email</p>
                                <p className="text-xs text-zinc-500 mt-1">If an account with that email exists, a reset link has been sent.</p>
                            </div>
                        ) : (
                            <>
                                {error && (
                                    <div className="flex items-center gap-2 bg-red-50 text-red-600 rounded-xl px-4 py-3 mb-4 ring-1 ring-red-200/50">
                                        <AlertCircle className="w-4 h-4 shrink-0" />
                                        <span className="text-sm font-bold">{error}</span>
                                    </div>
                                )}
                                <form onSubmit={handleSubmit} className="space-y-5">
                                    <div>
                                        <label className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em] mb-2 block">Email Address</label>
                                        <div className="relative">
                                            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                                            <input
                                                type="email" value={email} onChange={e => setEmail(e.target.value)}
                                                className="w-full bg-zinc-50 ring-1 ring-zinc-200 rounded-xl pl-11 pr-4 py-3.5 text-sm font-bold text-zinc-800 focus:ring-orange-500 focus:bg-white outline-none transition-all"
                                                placeholder="your@email.com" required
                                            />
                                        </div>
                                    </div>
                                    <button type="submit" disabled={loading} className="w-full bg-zinc-900 hover:bg-zinc-800 text-white rounded-xl py-3.5 text-xs font-black uppercase tracking-widest transition-all disabled:opacity-50">
                                        {loading ? 'Sending...' : 'Send Reset Link'}
                                    </button>
                                </form>
                            </>
                        )}
                    </div>
                </motion.div>
            </main>
        </div>
    )
}

function ResetForm({ token }: { token: string }) {
    const [password, setPassword] = useState('')
    const [confirm, setConfirm] = useState('')
    const [loading, setLoading] = useState(false)
    const [success, setSuccess] = useState(false)
    const [error, setError] = useState('')

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (password !== confirm) { setError('Passwords do not match'); return }
        if (password.length < 6) { setError('Password must be at least 6 characters'); return }
        setError('')
        setLoading(true)
        try {
            const res = await fetch('/api/auth/reset-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, password }),
            })
            const data = await res.json()
            if (res.ok) setSuccess(true)
            else setError(data.error || 'Failed to reset password')
        } catch {
            setError('Network error')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-zinc-900 font-sans flex flex-col relative overflow-hidden">
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,0,0,0.03)_1px,transparent_1px)] bg-[size:24px_24px]" />
                <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-orange-500/5 rounded-full blur-[160px]" />
            </div>

            <main className="flex-1 flex items-center justify-center px-4 relative z-10">
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
                    <div className="bg-white rounded-3xl ring-1 ring-zinc-200/80 shadow-[0_8px_30px_rgba(0,0,0,0.06)] p-8">
                        <div className="text-center mb-6">
                            <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-orange-500/20">
                                <Lock className="w-8 h-8 text-white" />
                            </div>
                            <h1 className="text-2xl font-black tracking-tight uppercase">Reset Password</h1>
                        </div>

                        {success ? (
                            <div className="text-center py-4">
                                <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
                                <p className="font-bold text-zinc-700">Password updated!</p>
                                <Link href="/login" className="inline-block mt-4 text-xs font-black text-orange-600 uppercase tracking-widest hover:underline">
                                    Go to Login →
                                </Link>
                            </div>
                        ) : (
                            <>
                                {error && (
                                    <div className="flex items-center gap-2 bg-red-50 text-red-600 rounded-xl px-4 py-3 mb-4 ring-1 ring-red-200/50">
                                        <AlertCircle className="w-4 h-4 shrink-0" /><span className="text-sm font-bold">{error}</span>
                                    </div>
                                )}
                                <form onSubmit={handleSubmit} className="space-y-5">
                                    <div>
                                        <label className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em] mb-2 block">New Password</label>
                                        <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                                            className="w-full bg-zinc-50 ring-1 ring-zinc-200 rounded-xl px-4 py-3.5 text-sm font-bold focus:ring-orange-500 outline-none transition-all"
                                            placeholder="Min 6 characters" required />
                                    </div>
                                    <div>
                                        <label className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em] mb-2 block">Confirm Password</label>
                                        <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)}
                                            className="w-full bg-zinc-50 ring-1 ring-zinc-200 rounded-xl px-4 py-3.5 text-sm font-bold focus:ring-orange-500 outline-none transition-all"
                                            placeholder="Repeat password" required />
                                    </div>
                                    <button type="submit" disabled={loading} className="w-full bg-zinc-900 hover:bg-zinc-800 text-white rounded-xl py-3.5 text-xs font-black uppercase tracking-widest transition-all disabled:opacity-50">
                                        {loading ? 'Updating...' : 'Update Password'}
                                    </button>
                                </form>
                            </>
                        )}
                    </div>
                </motion.div>
            </main>
        </div>
    )
}
