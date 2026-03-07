'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, Lock, User, Eye, EyeOff, AlertCircle, ArrowLeft, Building2, CheckCircle2 } from 'lucide-react'
import Link from 'next/link'
import { apiFetch } from '../components/hooks/apiUtils'
import { useRouter } from 'next/navigation'

export default function RegisterPage() {
    const router = useRouter()
    const [formData, setFormData] = useState({
        name: '',
        slug: '',
        contact_email: '',
        username: '',
        password: '',
        tier: 'individual'
    })
    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const [success, setSuccess] = useState(false)

    // Auto-generate slug from name
    const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const name = e.target.value
        setFormData({
            ...formData,
            name,
            slug: name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '')
        })
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        try {
            const res = await apiFetch('/api/register', {
                method: 'POST',
                body: JSON.stringify(formData)
            })

            const data = await res.json()

            if (!res.ok) {
                setError(data.error || 'Failed to create organization')
                setLoading(false)
            } else {
                setSuccess(true)
                // Redirect to login after 2 seconds
                setTimeout(() => {
                    router.push('/login')
                }, 2000)
            }
        } catch (err) {
            setError('Network error. Please try again.')
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-zinc-900 font-sans flex flex-col relative selection:bg-orange-500/30 overflow-hidden">
            {/* Ambient Lighting */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,0,0,0.03)_1px,transparent_1px)] bg-[size:24px_24px]" />
                <motion.div
                    animate={{ scale: [1, 1.1, 1], opacity: [0.03, 0.08, 0.03] }}
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

            {/* Register Form */}
            <main className="flex-1 flex items-center justify-center px-4 relative z-10 py-12">
                <motion.div
                    initial={{ opacity: 0, y: 20, filter: 'blur(10px)' }}
                    animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                    transition={{ duration: 0.8, delay: 0.1 }}
                    className="w-full max-w-lg"
                >
                    <div className="bg-white rounded-3xl ring-1 ring-zinc-200/80 shadow-[0_8px_30px_rgba(0,0,0,0.06)] p-8 lg:p-10">
                        {success ? (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                                className="text-center py-8"
                            >
                                <div className="w-20 h-20 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-6 ring-1 ring-emerald-200">
                                    <CheckCircle2 className="w-10 h-10 text-emerald-500" />
                                </div>
                                <h2 className="text-2xl font-black uppercase tracking-tight text-zinc-900 mb-2">Organization Created!</h2>
                                <p className="text-sm font-bold text-zinc-500 mb-6">Your registration was successful. Redirecting to login...</p>
                            </motion.div>
                        ) : (
                            <>
                                <div className="text-center mb-8">
                                    <div className="flex justify-center mb-6">
                                        <Link href="/login" className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-zinc-400 hover:text-zinc-800 transition-colors bg-zinc-50 px-4 py-2 rounded-full ring-1 ring-zinc-200">
                                            <ArrowLeft className="w-3.5 h-3.5" /> Back to Login
                                        </Link>
                                    </div>
                                    <div className="w-16 h-16 bg-gradient-to-br from-zinc-800 to-zinc-900 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-xl shadow-zinc-900/10">
                                        <Building2 className="w-8 h-8 text-white" />
                                    </div>
                                    <h1 className="text-2xl font-black tracking-tight uppercase">Create Organization</h1>
                                    <p className="text-sm text-zinc-500 mt-2 font-medium">Set up your monitoring fleet</p>
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

                                <form onSubmit={handleSubmit} className="space-y-4">
                                    {/* Organization Details */}
                                    <div className="space-y-4 p-5 bg-zinc-50/50 rounded-2xl ring-1 ring-zinc-200/60">
                                        <h3 className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-1">Organization Profile</h3>

                                        <div>
                                            <label className="text-[10px] font-black text-zinc-600 uppercase tracking-widest mb-1.5 block">Organization Name</label>
                                            <input
                                                type="text"
                                                value={formData.name}
                                                onChange={handleNameChange}
                                                className="w-full bg-white ring-1 ring-zinc-200 rounded-xl px-4 py-3 text-sm font-bold text-zinc-800 focus:ring-orange-500 outline-none transition-all shadow-sm"
                                                placeholder="e.g. Acme Corp"
                                                required
                                            />
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="text-[10px] font-black text-zinc-600 uppercase tracking-widest mb-1.5 block">URL Slug</label>
                                                <input
                                                    type="text"
                                                    value={formData.slug}
                                                    onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                                                    className="w-full bg-zinc-100 ring-1 ring-zinc-200/60 rounded-xl px-4 py-3 text-sm font-bold text-zinc-500 focus:ring-orange-500 outline-none transition-all cursor-not-allowed"
                                                    placeholder="acme-corp"
                                                    required
                                                    readOnly  // Usually it is auto generated!
                                                />
                                            </div>
                                            <div>
                                                <label className="text-[10px] font-black text-zinc-600 uppercase tracking-widest mb-1.5 block">Contact Email</label>
                                                <input
                                                    type="email"
                                                    value={formData.contact_email}
                                                    onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                                                    className="w-full bg-white ring-1 ring-zinc-200 rounded-xl px-4 py-3 text-sm font-bold text-zinc-800 focus:ring-orange-500 outline-none transition-all shadow-sm"
                                                    placeholder="admin@acme.com"
                                                    required
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex justify-center py-2">
                                        <div className="w-12 h-12 rounded-full bg-white ring-1 ring-zinc-200 flex items-center justify-center text-zinc-300 z-10 -my-7 shadow-sm">
                                            <User className="w-5 h-5" />
                                        </div>
                                    </div>

                                    {/* Subscription Tier */}
                                    <div className="space-y-3 p-5 bg-indigo-50/30 rounded-2xl ring-1 ring-indigo-200/50">
                                        <h3 className="text-[10px] font-black uppercase tracking-widest text-indigo-500/70 mb-1">Subscription Tier</h3>
                                        <div className="grid grid-cols-2 gap-3">
                                            <button
                                                type="button"
                                                onClick={() => setFormData({ ...formData, tier: 'individual' })}
                                                className={`p-3 lg:p-4 rounded-xl ring-1 text-left transition-all ${formData.tier === 'individual' ? 'ring-indigo-500 bg-indigo-50 shadow-sm' : 'ring-zinc-200 bg-white hover:ring-zinc-300'}`}
                                            >
                                                <div className="flex items-center justify-between mb-1">
                                                    <div className={`text-xs font-black uppercase tracking-widest ${formData.tier === 'individual' ? 'text-indigo-600' : 'text-zinc-700'}`}>Individual</div>
                                                    {formData.tier === 'individual' && <CheckCircle2 className="w-4 h-4 text-indigo-500" />}
                                                </div>
                                                <div className="text-[10px] font-bold text-zinc-500">1 node max • Free</div>
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setFormData({ ...formData, tier: 'business' })}
                                                className={`p-3 lg:p-4 rounded-xl ring-1 text-left transition-all ${formData.tier === 'business' ? 'ring-indigo-500 bg-indigo-50 shadow-sm' : 'ring-zinc-200 bg-white hover:ring-zinc-300'}`}
                                            >
                                                <div className="flex items-center justify-between mb-1">
                                                    <div className={`text-xs font-black uppercase tracking-widest ${formData.tier === 'business' ? 'text-indigo-600' : 'text-zinc-700'}`}>Business</div>
                                                    {formData.tier === 'business' && <CheckCircle2 className="w-4 h-4 text-indigo-500" />}
                                                </div>
                                                <div className="text-[10px] font-bold text-zinc-500">Unlimited nodes • Premium</div>
                                            </button>
                                        </div>
                                    </div>

                                    {/* Admin Account */}
                                    <div className="space-y-4 p-5 bg-orange-50/30 rounded-2xl ring-1 ring-orange-200/50">
                                        <h3 className="text-[10px] font-black uppercase tracking-widest text-orange-500/70 mb-1">Account Details</h3>

                                        <div>
                                            <label className="text-[10px] font-black text-zinc-600 uppercase tracking-widest mb-1.5 block">Username</label>
                                            <input
                                                type="text"
                                                value={formData.username}
                                                onChange={(e) => setFormData({ ...formData, username: e.target.value.replace(/\s+/g, '') })}
                                                className="w-full bg-white ring-1 ring-zinc-200 rounded-xl px-4 py-3 text-sm font-bold text-zinc-800 focus:ring-orange-500 outline-none transition-all shadow-sm"
                                                placeholder="Choose a username"
                                                required
                                            />
                                        </div>

                                        <div>
                                            <label className="text-[10px] font-black text-zinc-600 uppercase tracking-widest mb-1.5 block">Password</label>
                                            <div className="relative">
                                                <input
                                                    type={showPassword ? 'text' : 'password'}
                                                    value={formData.password}
                                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                                    className="w-full bg-white ring-1 ring-zinc-200 rounded-xl px-4 pr-12 py-3 text-sm font-bold text-zinc-800 focus:ring-orange-500 outline-none transition-all shadow-sm"
                                                    placeholder="Create a strong password"
                                                    required
                                                    minLength={6}
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
                                    </div>

                                    <div className="pt-4">
                                        <button
                                            type="submit"
                                            disabled={loading}
                                            className="w-full bg-orange-600 hover:bg-orange-500 text-white rounded-xl py-4 text-xs font-black uppercase tracking-widest flex items-center justify-center gap-2 transition-all hover:shadow-[0_8px_30px_rgba(234,88,12,0.25)] disabled:opacity-50 disabled:cursor-not-allowed group/btn"
                                        >
                                            {loading ? (
                                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                            ) : (
                                                <>
                                                    Create Organization
                                                </>
                                            )}
                                        </button>
                                        <div className="text-[10px] text-zinc-400 font-bold text-center mt-5 flex flex-wrap items-center justify-center gap-2">
                                            <span>By registering, you agree to our</span>
                                            <Link href="/terms-of-service" className="text-orange-500 hover:text-orange-600 underline decoration-orange-500/30 underline-offset-2">Terms of Service</Link>
                                            <span className="text-zinc-300">•</span>
                                            <Link href="/privacy-policy" className="text-orange-500 hover:text-orange-600 underline decoration-orange-500/30 underline-offset-2">Privacy Policy</Link>
                                            <span className="text-zinc-300">•</span>
                                            <Link href="/cookie-policy" className="text-orange-500 hover:text-orange-600 underline decoration-orange-500/30 underline-offset-2">Cookie Policy</Link>
                                        </div>
                                    </div>
                                </form>
                            </>
                        )}
                    </div>
                </motion.div>
            </main>
        </div>
    )
}
