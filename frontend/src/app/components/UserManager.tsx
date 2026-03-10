'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { UserPlus, Mail, Key, Shield, Building, AlertCircle } from 'lucide-react';
import { apiFetch } from './hooks/apiUtils';

interface Org {
    org_id: number;
    name: string;
    slug: string;
    tier?: string;
}

export function UserManager() {
    const [orgs, setOrgs] = useState<Org[]>([]);
    const [loading, setLoading] = useState(true);
    
    // Form state
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('USER');
    const [orgId, setOrgId] = useState('');
    
    const [createLoading, setCreateLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const fetchData = async () => {
        try {
            const resp = await apiFetch('/api/orgs');
            if (resp.ok) {
                const data = await resp.json();
                setOrgs(data);
                if (data.length > 0 && !orgId) {
                    // Set default org to the first one (usually root)
                    const rootOrg = data.find((o: any) => o.slug === 'root');
                    setOrgId(rootOrg ? rootOrg.org_id.toString() : data[0].org_id.toString());
                }
            }
        } catch (err) {
            console.error('Failed to fetch orgs for user management:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        setCreateLoading(true);
        setError('');
        setSuccess('');
        
        try {
            const resp = await apiFetch('/api/users', {
                method: 'POST',
                body: JSON.stringify({
                    username,
                    email,
                    password,
                    role,
                    org_id: parseInt(orgId)
                })
            });

            const data = await resp.json();
            if (!resp.ok) throw new Error(data.error || 'Failed to create user');

            setSuccess(`User ${username} created successfully!`);
            setUsername('');
            setEmail('');
            setPassword('');
        } catch (err: any) {
            setError(err.message || 'Failed to create user');
        } finally {
            setCreateLoading(false);
        }
    };

    if (loading) return null;

    return (
        <div className="bg-white rounded-3xl p-8 ring-1 ring-zinc-200/80 shadow-sm mt-8">
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 bg-blue-500/10 rounded-xl flex items-center justify-center">
                    <UserPlus className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                    <h2 className="text-xl font-black text-zinc-900 tracking-tight">Identity Management</h2>
                    <p className="text-zinc-500 text-xs font-medium">Provision single users for organizations</p>
                </div>
            </div>

            <form onSubmit={handleCreateUser} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="space-y-2">
                    <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest pl-1">Username</label>
                    <div className="relative">
                        <input
                            placeholder="e.g. john_doe"
                            value={username}
                            onChange={e => setUsername(e.target.value)}
                            className="w-full bg-zinc-50 border-none ring-1 ring-zinc-200 rounded-2xl p-4 pl-12 text-sm font-bold text-zinc-900 focus:ring-2 focus:ring-blue-500/20"
                            required
                        />
                        <Shield className="w-4 h-4 text-zinc-400 absolute left-4 top-1/2 -translate-y-1/2" />
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest pl-1">Email Address</label>
                    <div className="relative">
                        <input
                            type="email"
                            placeholder="user@example.com"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                            className="w-full bg-zinc-50 border-none ring-1 ring-zinc-200 rounded-2xl p-4 pl-12 text-sm font-bold text-zinc-900 focus:ring-2 focus:ring-blue-500/20"
                            required
                        />
                        <Mail className="w-4 h-4 text-zinc-400 absolute left-4 top-1/2 -translate-y-1/2" />
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest pl-1">Password</label>
                    <div className="relative">
                        <input
                            type="password"
                            placeholder="••••••••"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            className="w-full bg-zinc-50 border-none ring-1 ring-zinc-200 rounded-2xl p-4 pl-12 text-sm font-bold text-zinc-900 focus:ring-2 focus:ring-blue-500/20"
                            required
                        />
                        <Key className="w-4 h-4 text-zinc-400 absolute left-4 top-1/2 -translate-y-1/2" />
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest pl-1">System Role</label>
                    <select
                        value={role}
                        onChange={e => setRole(e.target.value)}
                        className="w-full bg-zinc-50 border-none ring-1 ring-zinc-200 rounded-2xl p-4 text-sm font-bold text-zinc-900 focus:ring-2 focus:ring-blue-500/20"
                    >
                        <option value="USER">User (Standard Access)</option>
                        <option value="ADMIN">Admin (Org Manager)</option>
                        <option value="ROOT">Root (System Global)</option>
                    </select>
                </div>

                <div className="space-y-2">
                    <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest pl-1">Assign Organization</label>
                    <div className="relative">
                        <select
                            value={orgId}
                            onChange={e => setOrgId(e.target.value)}
                            className="w-full bg-zinc-50 border-none ring-1 ring-zinc-200 rounded-2xl p-4 pl-12 text-sm font-bold text-zinc-900 focus:ring-2 focus:ring-blue-500/20"
                        >
                            {orgs.map(org => (
                                <option key={org.org_id} value={org.org_id}>
                                    {org.name} ({org.slug})
                                </option>
                            ))}
                        </select>
                        <Building className="w-4 h-4 text-zinc-400 absolute left-4 top-1/2 -translate-y-1/2" />
                    </div>
                </div>

                <div className="flex items-end">
                    <button
                        type="submit"
                        disabled={createLoading}
                        className="w-full bg-zinc-900 text-white rounded-2xl p-4 font-black uppercase tracking-widest text-[10px] flex items-center justify-center gap-2 hover:bg-zinc-800 disabled:opacity-50 transition-all active:scale-[0.98]"
                    >
                        <UserPlus className="w-4 h-4 text-blue-400" />
                        {createLoading ? 'Provisioning...' : 'Add Single User'}
                    </button>
                </div>
            </form>

            <div className="flex flex-col gap-2 mt-6">
                {error && (
                    <motion.div 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-red-500 text-[10px] font-black uppercase flex items-center gap-2 bg-red-50 p-4 rounded-2xl ring-1 ring-red-100 shadow-sm"
                    >
                        <AlertCircle className="w-4 h-4" /> {error}
                    </motion.div>
                )}
                {success && (
                    <motion.div 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-emerald-500 text-[10px] font-black uppercase flex items-center gap-2 bg-emerald-50 p-4 rounded-2xl ring-1 ring-emerald-100 shadow-sm"
                    >
                        <AlertCircle className="w-4 h-4" /> {success}
                    </motion.div>
                )}
            </div>
        </div>
    );
}
