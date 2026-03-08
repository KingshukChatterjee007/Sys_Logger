'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Activity, Lock, Mail, ChevronRight, AlertCircle } from 'lucide-react';
import { useAuth } from '../components/AuthContext';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (response.ok) {
                login(data.token, data.user);
            } else {
                setError(data.message || 'Invalid email or password');
            }
        } catch (err) {
            setError('Connection failed. Please check your backend.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#FAFAFA] flex items-center justify-center p-4 relative overflow-hidden">
            {/* Background Glows */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] bg-orange-500/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] left-[-10%] w-[50%] h-[50%] bg-emerald-500/10 rounded-full blur-[120px]" />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md relative z-10"
            >
                <div className="bg-white/70 backdrop-blur-2xl ring-1 ring-zinc-200/80 rounded-[2.5rem] shadow-[0_24px_48px_-12px_rgba(0,0,0,0.08)] p-10">
                    <div className="flex flex-col items-center mb-10">
                        <div className="w-16 h-16 bg-zinc-900 rounded-2xl flex items-center justify-center mb-6 shadow-xl shadow-zinc-900/20">
                            <Activity className="w-8 h-8 text-orange-500" />
                        </div>
                        <h1 className="text-3xl font-black tracking-tight text-zinc-900 mb-2">Welcome Back.</h1>
                        <p className="text-zinc-500 font-medium">Log in to the management system</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-1.5">
                            <label className="text-[10px] font-black uppercase tracking-widest text-zinc-400 ml-4">Email Address</label>
                            <div className="relative">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full bg-zinc-50 border-none ring-1 ring-zinc-200/80 rounded-2xl py-4 pl-12 pr-4 text-sm text-zinc-900 focus:ring-2 focus:ring-orange-500/20 transition-all font-medium"
                                    placeholder="Email"
                                    required
                                />
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-[10px] font-black uppercase tracking-widest text-zinc-400 ml-4">Password</label>
                            <div className="relative">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full bg-zinc-50 border-none ring-1 ring-zinc-200/80 rounded-2xl py-4 pl-12 pr-4 text-sm text-zinc-900 focus:ring-2 focus:ring-orange-500/20 transition-all font-medium"
                                    placeholder="Password"
                                    required
                                />
                            </div>
                        </div>

                        {error && (
                            <motion.div
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="flex items-center gap-2 bg-red-50 text-red-600 p-4 rounded-2xl text-xs font-bold ring-1 ring-red-200"
                            >
                                <AlertCircle className="w-4 h-4" />
                                {error}
                            </motion.div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-zinc-900 text-white rounded-2xl py-4 font-black uppercase tracking-widest text-xs flex items-center justify-center gap-2 hover:bg-zinc-800 transition-all disabled:opacity-50 mt-4 group shadow-xl shadow-zinc-900/10"
                        >
                            {loading ? 'Authenticating...' : (
                                <>
                                    Enter Fleet Hub
                                    <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>

                    <footer className="mt-12 pt-8 border-t border-zinc-100 flex justify-center items-center gap-8 opacity-80">
                        <img src="/Nielit_logo.jpeg" className="h-8 object-contain" />
                        <img src="/krishishayogi.png" className="h-8 object-contain" />
                        <img src="/India-AI_logo.jpeg" className="h-8 object-contain" />
                    </footer>
                </div>
            </motion.div>
        </div>
    );
}
