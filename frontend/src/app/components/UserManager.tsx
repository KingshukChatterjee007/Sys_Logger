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
            const timestamp = new Date().getTime();
            const [orgsResp, usersResp] = await Promise.all([
                apiFetch(`/api/orgs?t=${timestamp}`),
                apiFetch(`/api/users?t=${timestamp}`)
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
                // Sort by descending user_id so newest users appear first
                setUsers(data.sort((a: any, b: any) => b.user_id - a.user_id));
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
        <div className="bg-white/40 backdrop-blur-2xl rounded-[2.5rem] p-8 ring-[1px] ring-white/60 shadow-[0_8px_32px_0_rgba(59,130,246,0.15)] mt-6 relative overflow-hidden border border-blue-100/20">
            <div className="absolute -top-32 -left-32 w-96 h-96 bg-gradient-to-br from-blue-500/20 via-indigo-500/10 to-transparent rounded-full blur-3xl pointer-events-none" />
            
            <div className="flex items-center gap-4 mb-8 relative z-10">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-50 to-blue-100/50 rounded-2xl flex items-center justify-center ring-1 ring-blue-200/50 shadow-sm">
                    <UserPlus className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                    <h2 className="text-2xl font-black text-zinc-900 tracking-tight">Identity Management</h2>
                    <p className="text-zinc-500 text-sm font-medium mt-0.5">Provision single users for organizations</p>
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
                            className="w-full bg-white/50 backdrop-blur-md border border-blue-200/50 shadow-inner rounded-2xl p-4 pl-12 text-sm font-bold text-zinc-900 focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all hover:bg-white/80"
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
                            className="w-full bg-white/50 backdrop-blur-md border border-blue-200/50 shadow-inner rounded-2xl p-4 pl-12 text-sm font-bold text-zinc-900 focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all hover:bg-white/80"
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
                            className="w-full bg-white/50 backdrop-blur-md border border-blue-200/50 shadow-inner rounded-2xl p-4 pl-12 text-sm font-bold text-zinc-900 focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all hover:bg-white/80"
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
                        className="w-full bg-white/50 backdrop-blur-md border border-blue-200/50 shadow-inner rounded-2xl p-4 text-sm font-bold text-zinc-900 focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all hover:bg-white/80"
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
                            className="w-full bg-white/50 backdrop-blur-md border border-blue-200/50 shadow-inner rounded-2xl p-4 pl-12 text-sm font-bold text-zinc-900 focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all hover:bg-white/80"
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
                        className="w-full bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-2xl p-4 font-black uppercase tracking-widest text-[11px] flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(59,130,246,0.4)] hover:shadow-[0_0_30px_rgba(59,130,246,0.6)] hover:scale-[1.02] active:scale-95 transition-all duration-300 disabled:opacity-50 disabled:hover:scale-100 disabled:hover:shadow-none"
                    >
                        <UserPlus className="w-5 h-5 text-white" />
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
                <div className="flex flex-col gap-3">
                    {users.slice(0, showAllUsers ? undefined : 5).map(u => (
                        <div key={u.user_id} className="relative bg-white/60 backdrop-blur-md rounded-2xl p-3.5 ring-1 ring-blue-200/50 shadow-sm hover:shadow-md hover:bg-white/90 hover:ring-blue-300 transition-all duration-300 group overflow-hidden flex items-center justify-between gap-4">
                            <div className="absolute -left-10 w-20 h-full bg-blue-400/5 blur-xl group-hover:bg-blue-400/10 transition-all pointer-events-none" />
                            
                            <div className="flex items-center gap-4 relative z-10 w-full">
                                {/* Left side: Role Badge */}
                                <div className="w-12 h-10 rounded-xl bg-zinc-900 text-white flex items-center justify-center text-[9px] font-black tracking-widest uppercase shadow-md flex-shrink-0">
                                    {u.role}
                                </div>
                                
                                {/* Middle: User Details */}
                                <div className="flex-1 min-w-0 flex flex-col justify-center">
                                    <div className="text-[13px] font-black text-zinc-900 group-hover:text-blue-600 transition-colors truncate">{u.username}</div>
                                    <div className="text-[10px] font-bold text-zinc-500 truncate mt-0.5">{u.email}</div>
                                </div>

                                {/* Right side: Org and ID */}
                                <div className="flex items-center gap-3 text-right">
                                    <div className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50/50 rounded-lg ring-1 ring-blue-100/50">
                                        <Building className="w-3 h-3 text-blue-400" />
                                        <span className="text-[9px] font-black text-zinc-600 uppercase tracking-tight truncate max-w-[120px]">{u.org_name || 'No Org'}</span>
                                    </div>
                                    <div className="text-[9px] font-black text-zinc-400 uppercase tracking-tight w-8">
                                        #{u.user_id}
                                    </div>
                                </div>
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
