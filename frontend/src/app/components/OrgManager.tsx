'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Building2, Plus, ArrowRight, Server, Shield, Globe, Check, AlertCircle } from 'lucide-react';
import { apiFetch } from './hooks/apiUtils';
import { UserManager } from './UserManager';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface Org {
    org_id: number;
    name: string;
    slug: string;
    tier?: string;
}

interface Unit {
    id: string;
    name: string;
    hostname: string;
    org_id: string;
    status: string;
    last_seen: string | null;
    ip: string | null;
}

export function OrgManager() {
    const [orgs, setOrgs] = useState<Org[]>([]);
    const [units, setUnits] = useState<Unit[]>([]);
    const [loading, setLoading] = useState(true);

    const [newOrgId, setNewOrgId] = useState('');
    const [newOrgName, setNewOrgName] = useState('');
    const [newOrgTier, setNewOrgTier] = useState('FREE');
    const [createLoading, setCreateLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [showAllOrgs, setShowAllOrgs] = useState(false);

    const fetchData = async () => {
        setLoading(true);
        try {
            const orgsResp = await apiFetch('/api/orgs');
            const unitsResp = await apiFetch('/api/units');

            if (orgsResp.ok) {
                const orgsData = await orgsResp.json();
                setOrgs(orgsData);
            }
            if (unitsResp.ok) {
                const unitsData = await unitsResp.json();
                setUnits(unitsData);
            }
        } catch (err) {
            console.error('Failed to fetch org management data:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleCreateOrg = async (e: React.FormEvent) => {
        e.preventDefault();
        setCreateLoading(true);
        setError('');
        setSuccess('');
        try {
            const resp = await apiFetch('/api/orgs', {
                method: 'POST',
                body: JSON.stringify({ 
                    org_id: newOrgId, 
                    name: newOrgName,
                    tier: newOrgTier
                })
            });
            
            let data;
            const contentType = resp.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await resp.json();
            } else {
                const text = await resp.text();
                throw new Error(text || `Server error: ${resp.status}`);
            }

            if (!resp.ok) throw new Error(data.error || data.message || 'Failed to create organization');

            setNewOrgId('');
            setNewOrgName('');
            setSuccess(`Organization "${newOrgName}" registered successfully!`);
            await fetchData();
        } catch (err: any) {
            console.error('Org creation error:', err);
            setError(err.message || 'Failed to create organization');
        } finally {
            setCreateLoading(false);
        }
    };

    const handleUpdateUnitOrg = async (unitId: string, newOrgId: string) => {
        try {
            await apiFetch(`/api/units/${unitId}/org`, {
                method: 'PUT',
                body: JSON.stringify({ org_id: newOrgId })
            });
            await fetchData();
        } catch (err) {
            console.error('Failed to move unit:', err);
        }
    };

    const formatLastSeen = (isoString: string | null) => {
        if (!isoString) return 'Never';
        const date = new Date(isoString);
        const now = new Date();
        const diff = Math.floor((now.getTime() - date.getTime()) / 1000);

        if (diff < 60) return 'Just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return date.toLocaleDateString();
    };

    if (loading) return (
        <div className="flex items-center justify-center p-20 text-zinc-400 font-bold uppercase tracking-widest text-xs">
            Loading System Registry...
        </div>
    );

    return (
        <div className="space-y-8 p-1">
            {/* Create Org Section */}
            <div className="bg-white rounded-3xl p-8 ring-1 ring-zinc-200/80 shadow-sm">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-orange-500/10 rounded-xl flex items-center justify-center">
                        <Building2 className="w-5 h-5 text-orange-500" />
                    </div>
                    <div>
                        <h2 className="text-xl font-black text-zinc-900 tracking-tight">System Registry</h2>
                        <p className="text-zinc-500 text-xs font-medium">Create and manage organizational hubs</p>
                    </div>
                </div>

                <form onSubmit={handleCreateOrg} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <input
                        placeholder="ORG_ID (e.g. NIELIT)"
                        value={newOrgId}
                        onChange={e => setNewOrgId(e.target.value.toUpperCase())}
                        className="bg-zinc-50 border-none ring-1 ring-zinc-200 rounded-2xl p-4 text-sm font-bold text-zinc-900 focus:ring-2 focus:ring-orange-500/20"
                        required
                    />
                    <input
                        placeholder="Organization Name"
                        value={newOrgName}
                        onChange={e => setNewOrgName(e.target.value)}
                        className="bg-zinc-50 border-none ring-1 ring-zinc-200 rounded-2xl p-4 text-sm font-bold text-zinc-900 focus:ring-2 focus:ring-orange-500/20"
                        required
                    />
                    <select
                        value={newOrgTier}
                        onChange={e => setNewOrgTier(e.target.value)}
                        className="bg-zinc-50 border-none ring-1 ring-zinc-200 rounded-2xl p-4 text-sm font-bold text-zinc-900 focus:ring-2 focus:ring-orange-500/20"
                        required
                    >
                        <option value="FREE">Free Tier (1 Node)</option>
                        <option value="PRO">Pro Tier (10 Nodes)</option>
                        <option value="BUSINESS">Business Tier (50)</option>
                    </select>
                    <button
                        type="submit"
                        disabled={createLoading}
                        className="bg-zinc-900 text-white rounded-2xl p-4 font-black uppercase tracking-widest text-[10px] flex items-center justify-center gap-2 hover:bg-zinc-800 disabled:opacity-50"
                    >
                        <Plus className="w-4 h-4" />
                        {createLoading ? 'Executing...' : 'Register Organization'}
                    </button>
                </form>
                {error && <div className="mt-4 text-red-500 text-[10px] font-black uppercase flex items-center gap-2 bg-red-50 p-3 rounded-xl ring-1 ring-red-100">
                    <AlertCircle className="w-4 h-4" /> {error}
                </div>}
                
                {success && <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-4 text-emerald-500 text-[10px] font-black uppercase flex items-center gap-2 bg-emerald-50 p-3 rounded-xl ring-1 ring-emerald-100 shadow-sm"
                >
                    <Check className="w-4 h-4" /> {success}
                </motion.div>}

                {/* Org List Sub-section */}
                <div className="mt-10 pt-8 border-t border-zinc-100">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <div className="text-[10px] font-black text-zinc-400 uppercase tracking-widest pl-1">Active Registrations</div>
                            <p className="text-zinc-500 text-[10px] font-medium pl-1">Verified organizational hubs</p>
                        </div>
                        <div className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{orgs.length} total</div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {orgs.slice(0, showAllOrgs ? undefined : 3).map(org => (
                            <div key={org.org_id} className="bg-zinc-50 rounded-2xl p-4 ring-1 ring-zinc-100 hover:ring-orange-500/20 transition-all group">
                                <div className="flex items-center justify-between mb-2">
                                    <div className="px-2 py-0.5 bg-zinc-900 text-white rounded-md text-[8px] font-black tracking-widest uppercase">
                                        ID: {org.org_id}
                                    </div>
                                    <div className="px-2 py-0.5 bg-orange-50 text-orange-600 rounded-md text-[8px] font-black tracking-widest uppercase ring-1 ring-orange-100">
                                        {org.tier}
                                    </div>
                                </div>
                                <div className="text-sm font-black text-zinc-900 group-hover:text-orange-600 transition-colors line-clamp-1">{org.name}</div>
                                <div className="text-[9px] font-bold text-zinc-400 font-mono tracking-tight mt-0.5">slug: {org.slug}</div>
                            </div>
                        ))}
                    </div>

                    {orgs.length > 3 && (
                        <div className="mt-6 flex justify-center">
                            <button 
                                onClick={() => setShowAllOrgs(!showAllOrgs)}
                                className="px-6 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest text-zinc-500 hover:text-orange-600 hover:bg-orange-50 ring-1 ring-zinc-200 hover:ring-orange-200 transition-all active:scale-95"
                            >
                                {showAllOrgs ? 'Show Less' : `Show All (${orgs.length})`}
                            </button>
                        </div>
                    )}
                </div>
            </div>

            <UserManager />

            {/* Unit Mapping Table */}
            <div className="bg-white rounded-3xl overflow-hidden ring-1 ring-zinc-200/80 shadow-sm">
                <div className="p-8 border-b border-zinc-100 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-zinc-900/5 rounded-xl flex items-center justify-center">
                            <Server className="w-5 h-5 text-zinc-900" />
                        </div>
                        <div>
                            <h2 className="text-xl font-black text-zinc-900 tracking-tight">Active Fleet Mapping</h2>
                            <p className="text-zinc-500 text-xs font-medium">Assign machines to specific organizations</p>
                        </div>
                    </div>
                    <div className="px-4 py-2 bg-zinc-50 rounded-full border border-zinc-100 text-[10px] font-black text-zinc-500 uppercase tracking-widest">
                        {units.length} System(s) Detected
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-zinc-50/50">
                                <th className="px-8 py-4 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Machine Identity</th>
                                <th className="px-8 py-4 text-[10px] font-black text-zinc-400 uppercase tracking-widest text-center">Status</th>
                                <th className="px-8 py-4 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Last Activity</th>
                                <th className="px-8 py-4 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Org Assignment</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-100">
                            {units.map(unit => (
                                <tr key={unit.id} className="hover:bg-zinc-50/50 transition-colors">
                                    <td className="px-8 py-5">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 bg-zinc-900 rounded-lg flex items-center justify-center text-orange-500">
                                                <Globe className="w-4 h-4" />
                                            </div>
                                            <div>
                                                <div className="text-sm font-black text-zinc-900">{unit.name}</div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[10px] font-bold text-zinc-400 font-mono tracking-tight">{unit.hostname}</span>
                                                    <span className="text-[10px] font-medium text-zinc-300">•</span>
                                                    <span className="text-[10px] font-bold text-blue-500/70 font-mono tracking-tight">{unit.ip || '0.0.0.0'}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-8 py-5 text-center">
                                        <div className="flex justify-center">
                                            <div className={clsx(
                                                "px-2 py-0.5 rounded-full text-[9px] font-black tracking-widest uppercase flex items-center gap-1.5",
                                                unit.status === 'online' 
                                                    ? "bg-emerald-50 text-emerald-600 ring-1 ring-emerald-200" 
                                                    : "bg-zinc-50 text-zinc-400 ring-1 ring-zinc-200"
                                            )}>
                                                <div className={clsx(
                                                    "w-1 h-1 rounded-full",
                                                    unit.status === 'online' ? "bg-emerald-500 animate-pulse" : "bg-zinc-300"
                                                )} />
                                                {unit.status}
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-8 py-5">
                                        <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">
                                            {formatLastSeen(unit.last_seen)}
                                        </div>
                                    </td>
                                    <td className="px-8 py-5 text-right">
                                        <div className="flex items-center gap-3 justify-end">
                                            <span className="px-2 py-1 bg-zinc-50 text-zinc-500 rounded-lg text-[10px] font-black tracking-widest uppercase ring-1 ring-zinc-100">
                                                {unit.org_id || 'UNASSIGNED'}
                                            </span>
                                            <ArrowRight className="w-3 h-3 text-zinc-300" />
                                            <select
                                                value={unit.org_id || ''}
                                                onChange={(e) => handleUpdateUnitOrg(unit.id, e.target.value)}
                                                className="bg-zinc-50 border-none ring-1 ring-zinc-200 rounded-xl px-4 py-2 text-xs font-bold text-zinc-900 focus:ring-2 focus:ring-orange-500/20"
                                            >
                                                <option value="" disabled>Select Org</option>
                                                {orgs.map(org => (
                                                    <option key={org.org_id} value={org.org_id}>{org.slug} - {org.name}</option>
                                                ))}
                                            </select>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
