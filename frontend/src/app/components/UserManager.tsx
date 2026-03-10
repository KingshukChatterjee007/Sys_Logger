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
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('USER');
    const [orgId, setOrgId] = useState('');

    interface User {
        user_id: number;
        username: string;
        email: string;
        role: string;
        org_name: string;
    }

    const [users, setUsers] = useState<User[]>([]);
    const [showAllUsers, setShowAllUsers] = useState(false);
    const [createLoading, setCreateLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const fetchData = async () => {
        try {
            const [orgsResp, usersResp] = await Promise.all([
                apiFetch('/api/orgs'),
                apiFetch('/api/users')
            ]);

            if (orgsResp.ok) {
                const data = await orgsResp.json();
                setOrgs(data);
                if (data.length > 0 && !orgId) {
                    const rootOrg = data.find((o: any) => o.slug === 'root');
                    setOrgId(rootOrg ? rootOrg.org_id.toString() : data[0].org_id.toString());
                }
            }

            if (usersResp.ok) {
                const data = await usersResp.json();
                setUsers(data);
            }
        } catch (err) {
            console.error('Failed to fetch user management data:', err);
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
            await fetchData();
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

            {/* User List Sub-section */}
            <div className="mt-10 pt-8 border-t border-zinc-100">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <div className="text-[10px] font-black text-zinc-400 uppercase tracking-widest pl-1">Active Accounts</div>
                        <p className="text-zinc-500 text-[10px] font-medium pl-1">Verified system identities</p>
                    </div>
                    <div className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{users.length} total</div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {users.slice(0, showAllUsers ? undefined : 3).map(u => (
                        <div key={u.user_id} className="bg-zinc-50 rounded-2xl p-4 ring-1 ring-zinc-100 hover:ring-blue-500/20 transition-all group">
                            <div className="flex items-center justify-between mb-2">
                                <div className="px-2 py-0.5 bg-zinc-900 text-white rounded-md text-[8px] font-black tracking-widest uppercase">
                                    {u.role}
                                </div>
                                <div className="text-[8px] font-black text-zinc-400 uppercase tracking-tight">
                                    ID: {u.user_id}
                                </div>
                            </div>
                            <div className="text-sm font-black text-zinc-900 group-hover:text-blue-600 transition-colors line-clamp-1">{u.username}</div>
                            <div className="text-[10px] font-bold text-zinc-400 truncate">{u.email}</div>
                            <div className="mt-2 pt-2 border-t border-zinc-200/50 flex items-center gap-1.5">
                                <Building className="w-3 h-3 text-zinc-300" />
                                <span className="text-[9px] font-black text-zinc-500 uppercase tracking-tight truncate">{u.org_name || 'No Org'}</span>
                            </div>
                        </div>
                    ))}
                </div>

                {users.length > 3 && (
                    <div className="mt-6 flex justify-center">
                        <button 
                            onClick={() => setShowAllUsers(!showAllUsers)}
                            className="px-6 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest text-zinc-500 hover:text-blue-600 hover:bg-blue-50 ring-1 ring-zinc-200 hover:ring-blue-200 transition-all active:scale-95"
                        >
                            {showAllUsers ? 'Show Less' : `Show All (${users.length})`}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
