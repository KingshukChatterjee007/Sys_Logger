'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Building2, Plus, ArrowRight, Server, Shield, Globe, Check, AlertCircle, Activity } from 'lucide-react';
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

interface PricingPlan {
    plan_id: number;
    name: string;
    slug: string;
    price_monthly: number;
    node_limit: number;
    features: string[];
    is_active: boolean;
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
    const [newOrgTier, setNewOrgTier] = useState('PRO');
    const [createLoading, setCreateLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [showAllOrgs, setShowAllOrgs] = useState(false);
    const [plans, setPlans] = useState<PricingPlan[]>([]);
    const [editingPlan, setEditingPlan] = useState<PricingPlan | null>(null);
    const [updateLoading, setUpdateLoading] = useState(false);

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

            // Fetch Pricing Plans
            const pricingResp = await apiFetch('/api/pricing');
            if (pricingResp.ok) {
                const pricingData = await pricingResp.json();
                setPlans(pricingData);
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

    const handleUpdatePricing = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingPlan) return;
        setUpdateLoading(true);
        try {
            const resp = await apiFetch('/api/pricing', {
                method: 'PUT',
                body: JSON.stringify({
                    plan_id: editingPlan.plan_id,
                    price_monthly: editingPlan.price_monthly,
                    node_limit: editingPlan.node_limit,
                    features: Array.isArray(editingPlan.features) ? editingPlan.features : (editingPlan.features as any).split(',').map((f: string) => f.trim()),
                    is_active: editingPlan.is_active
                })
            });
            if (resp.ok) {
                setSuccess(`Plan "${editingPlan.name}" updated successfully!`);
                setEditingPlan(null);
                await fetchData();
            } else {
                const data = await resp.json();
                throw new Error(data.error || 'Failed to update pricing');
            }
        } catch (err: any) {
            setError(err.message);
        } finally {
            setUpdateLoading(false);
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
            <div className="bg-white/40 backdrop-blur-2xl rounded-[2.5rem] p-8 ring-[1px] ring-white/60 shadow-[0_8px_32px_0_rgba(249,115,22,0.15)] relative overflow-hidden border border-orange-100/20">
                <div className="absolute -top-32 -right-32 w-96 h-96 bg-gradient-to-br from-orange-500/20 via-amber-500/10 to-transparent rounded-full blur-3xl pointer-events-none" />
                
                <div className="flex items-center gap-4 mb-8 relative z-10">
                    <div className="w-12 h-12 bg-gradient-to-br from-orange-50 to-orange-100/50 rounded-2xl flex items-center justify-center ring-1 ring-orange-200/50 shadow-sm">
                        <Building2 className="w-6 h-6 text-orange-600" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-zinc-900 tracking-tight">System Registry</h2>
                        <p className="text-zinc-500 text-sm font-medium mt-0.5">Create and manage organizational hubs</p>
                    </div>
                </div>

                <form onSubmit={handleCreateOrg} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <input
                        placeholder="ORG_ID (e.g. NIELIT)"
                        value={newOrgId}
                        onChange={e => setNewOrgId(e.target.value.toUpperCase())}
                        className="bg-white/50 backdrop-blur-md border border-orange-200/50 shadow-inner rounded-2xl p-4 text-sm font-bold text-zinc-900 focus:ring-4 focus:ring-orange-500/20 focus:border-orange-500 transition-all hover:bg-white/80"
                        required
                    />
                    <input
                        placeholder="Organization Name"
                        value={newOrgName}
                        onChange={e => setNewOrgName(e.target.value)}
                        className="bg-white/50 backdrop-blur-md border border-orange-200/50 shadow-inner rounded-2xl p-4 text-sm font-bold text-zinc-900 focus:ring-4 focus:ring-orange-500/20 focus:border-orange-500 transition-all hover:bg-white/80"
                        required
                    />
                    <select
                        value={newOrgTier}
                        onChange={e => setNewOrgTier(e.target.value)}
                        className="bg-white/50 backdrop-blur-md border border-orange-200/50 shadow-inner rounded-2xl p-4 text-sm font-bold text-zinc-900 focus:ring-4 focus:ring-orange-500/20 focus:border-orange-500 transition-all hover:bg-white/80"
                        required
                    >
                        {plans.map(plan => (
                             <option key={plan.plan_id} value={plan.slug.toUpperCase()}>
                                {plan.name} Tier ({plan.node_limit === 99999 ? 'Unlimited' : `${plan.node_limit} Nodes`})
                             </option>
                        ))}
                    </select>
                    <button
                        type="submit"
                        disabled={createLoading}
                        className="bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-2xl p-4 font-black uppercase tracking-widest text-[11px] flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(249,115,22,0.4)] hover:shadow-[0_0_30px_rgba(249,115,22,0.6)] hover:scale-[1.02] active:scale-95 transition-all duration-300 disabled:opacity-50 disabled:hover:scale-100 disabled:hover:shadow-none"
                    >
                        <Plus className="w-5 h-5" />
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

                {/* Pricing Management Logic (Admin only view - will show if plans exist) */}
                {plans.length > 0 && (
                    <div className="mt-10 pt-8 border-t border-zinc-100">
                        <div className="flex items-center gap-4 mb-8">
                            <div className="w-10 h-10 bg-gradient-to-br from-emerald-50 to-emerald-100/50 rounded-xl flex items-center justify-center ring-1 ring-emerald-200/50 shadow-sm">
                                <Shield className="w-5 h-5 text-emerald-600" />
                            </div>
                            <div>
                                <h3 className="text-lg font-black text-zinc-900 uppercase tracking-tight">Revenue & Plan Control</h3>
                                <p className="text-zinc-500 text-[11px] font-bold uppercase tracking-widest mt-0.5">Live financial configuration</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {plans.map(plan => (
                                <div key={plan.plan_id} className="relative p-6 rounded-[2rem] bg-gradient-to-br from-white/80 to-emerald-50/20 shadow-xl ring-1 ring-emerald-200/50 hover:ring-2 hover:ring-emerald-400 hover:shadow-[0_0_40px_rgba(16,185,129,0.25)] hover:-translate-y-2 transition-all duration-300 overflow-hidden backdrop-blur-xl group">
                                    <div className="absolute -top-20 -right-20 w-40 h-40 bg-emerald-400/20 rounded-full blur-2xl group-hover:bg-emerald-400/30 transition-all duration-500" />
                                    <div className="flex justify-between items-start mb-4 relative z-10">
                                        <div>
                                            <div className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em] mb-1">{plan.name} {plan.is_active ? <span className="text-emerald-500">(LIVE)</span> : <span className="text-red-500">(INACTIVE)</span>}</div>
                                            <div className="text-xl font-black text-zinc-900">₹{plan.price_monthly} <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest">/ mo</span></div>
                                        </div>
                                        <button 
                                            onClick={() => setEditingPlan(plan)}
                                            className="px-3 py-1.5 bg-zinc-900 text-white rounded-lg text-[9px] font-black uppercase tracking-widest hover:bg-zinc-800 hover:scale-105 transition-all shadow-sm flex items-center gap-1.5 cursor-pointer relative z-20"
                                        >
                                            <Activity className="w-3 h-3" />
                                            Edit
                                        </button>
                                    </div>
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-[9px] font-black uppercase tracking-widest text-zinc-500">
                                            <span>Limit</span>
                                            <span className="text-zinc-900">{plan.node_limit === 99999 ? 'Unlimited' : `${plan.node_limit} Nodes`}</span>
                                        </div>
                                        <div className="text-[9px] font-medium text-zinc-400 line-clamp-1 italic">
                                            {plan.features.join(', ')}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Edit Plan Modal/Overlay */}
                        {editingPlan && (
                            <motion.div 
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="fixed inset-0 z-[100] flex items-center justify-center bg-zinc-950/20 backdrop-blur-sm p-4"
                            >
                                <motion.div 
                                    initial={{ scale: 0.95, opacity: 0 }}
                                    animate={{ scale: 1, opacity: 1 }}
                                    className="bg-white rounded-[2.5rem] w-full max-w-md p-8 shadow-2xl ring-1 ring-zinc-200"
                                >
                                    <div className="flex justify-between items-center mb-8">
                                        <h3 className="text-xl font-black text-zinc-900 uppercase tracking-tight">Modify {editingPlan.name} Plan</h3>
                                        <button onClick={() => setEditingPlan(null)} className="p-2 hover:bg-zinc-100 rounded-full transition-colors">
                                            <Plus className="w-5 h-5 rotate-45 text-zinc-400" />
                                        </button>
                                    </div>

                                    <form onSubmit={handleUpdatePricing} className="space-y-6">
                                        <div>
                                            <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-2 block ml-1">Price (USD / Month)</label>
                                            <input 
                                                type="number"
                                                value={editingPlan.price_monthly}
                                                onChange={e => setEditingPlan({...editingPlan, price_monthly: parseFloat(e.target.value)})}
                                                className="w-full bg-zinc-50 border-none ring-1 ring-zinc-200 rounded-2xl p-4 text-sm font-bold text-zinc-900 focus:ring-2 focus:ring-emerald-500/20"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-2 block ml-1 flex items-center gap-1.5"><Activity className="w-3.5 h-3.5"/> Node Limit</label>
                                            <input 
                                                type="number"
                                                value={editingPlan.node_limit}
                                                onChange={e => setEditingPlan({...editingPlan, node_limit: parseInt(e.target.value)})}
                                                className="w-full bg-zinc-50 border-none ring-1 ring-zinc-200 rounded-2xl p-4 text-sm font-bold text-zinc-900 focus:ring-2 focus:ring-emerald-500/20"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-2 block ml-1">Features (Comma Separated)</label>
                                            <textarea 
                                                value={Array.isArray(editingPlan.features) ? editingPlan.features.join(', ') : editingPlan.features}
                                                onChange={e => setEditingPlan({...editingPlan, features: e.target.value as any})}
                                                className="w-full bg-zinc-50 border-none ring-1 ring-zinc-200 rounded-2xl p-4 text-sm font-bold text-zinc-900 focus:ring-2 focus:ring-emerald-500/20 h-32"
                                            />
                                        </div>

                                        <div className="flex items-center gap-3 bg-zinc-50 p-4 rounded-2xl ring-1 ring-zinc-200">
                                            <input 
                                                type="checkbox"
                                                id="is_active"
                                                checked={editingPlan.is_active}
                                                onChange={e => setEditingPlan({...editingPlan, is_active: e.target.checked})}
                                                className="w-4 h-4 rounded text-emerald-500 focus:ring-emerald-500"
                                            />
                                            <label htmlFor="is_active" className="text-xs font-black text-zinc-700 uppercase tracking-widest cursor-pointer">
                                                Plan is Active (Visible on Live Site)
                                            </label>
                                        </div>

                                        <div className="flex gap-3">
                                            <button 
                                                type="button"
                                                onClick={() => {
                                                    if (confirm("Are you sure you want to deactivate (remove) this plan from public view?")) {
                                                        setEditingPlan({...editingPlan, is_active: false});
                                                        // Note: The form submit will handle the actual API call
                                                    }
                                                }}
                                                className="px-6 py-4 bg-red-50 text-red-600 rounded-2xl font-black uppercase tracking-widest text-[10px] ring-1 ring-red-100 hover:bg-red-100 transition-all"
                                            >
                                                Remove/Deactivate
                                            </button>
                                            <button 
                                                type="submit"
                                                disabled={updateLoading}
                                                className="flex-1 bg-zinc-900 text-white rounded-2xl p-4 font-black uppercase tracking-widest text-xs flex items-center justify-center gap-2 hover:bg-zinc-800 shadow-lg shadow-zinc-500/10 disabled:opacity-50"
                                            >
                                                {updateLoading ? 'Updating...' : 'Apply Changes'}
                                            </button>
                                        </div>
                                    </form>
                                </motion.div>
                            </motion.div>
                        )}
                    </div>
                )}

                {/* Org List Sub-section */}
                <div className="mt-10 pt-8 border-t border-zinc-100">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <div className="text-[10px] font-black text-zinc-400 uppercase tracking-widest pl-1">Active Registrations</div>
                            <p className="text-zinc-500 text-[10px] font-medium pl-1">Verified organizational hubs</p>
                        </div>
                        <div className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{orgs.length} total</div>
                    </div>
                    <div className="flex flex-col gap-3">
                        {orgs.slice(0, showAllOrgs ? undefined : 5).map(org => (
                            <div key={org.org_id} className="relative bg-white/60 backdrop-blur-md rounded-2xl p-3.5 ring-1 ring-orange-200/50 shadow-sm hover:shadow-md hover:bg-white/90 hover:ring-orange-300 transition-all duration-300 group overflow-hidden flex items-center justify-between">
                                <div className="absolute -left-10 w-20 h-full bg-orange-400/5 blur-xl group-hover:bg-orange-400/10 transition-all pointer-events-none" />
                                
                                <div className="flex items-center gap-4 relative z-10 w-full">
                                    {/* Left side: ID block */}
                                    <div className="w-10 h-10 rounded-xl bg-zinc-900 text-white flex items-center justify-center text-[10px] font-black shadow-md flex-shrink-0">
                                        #{org.org_id}
                                    </div>
                                    
                                    {/* Middle: Name and Slug */}
                                    <div className="flex-1 min-w-0 flex flex-col justify-center">
                                        <div className="text-[13px] font-black text-zinc-900 group-hover:text-orange-600 transition-colors truncate">{org.name}</div>
                                        <div className="text-[9px] font-bold text-zinc-400 font-mono tracking-tight truncate mt-0.5">{org.slug}</div>
                                    </div>

                                    {/* Right side: Tier */}
                                    <div className="px-3 py-1.5 bg-gradient-to-r from-orange-100 to-orange-50 text-orange-600 rounded-lg text-[9px] font-black tracking-widest uppercase ring-1 ring-orange-200/80 shadow-sm whitespace-nowrap">
                                        {org.tier}
                                    </div>
                                </div>
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
            <div className="bg-white/40 backdrop-blur-2xl rounded-[2.5rem] overflow-hidden ring-[1px] ring-white/60 shadow-[0_8px_32px_0_rgba(14,165,233,0.15)] mt-6 border border-blue-100/20">
                <div className="p-8 border-b border-white/40 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative">
                    <div className="absolute -top-20 -right-20 w-64 h-64 bg-gradient-to-bl from-blue-500/20 via-sky-500/10 to-transparent rounded-full blur-3xl pointer-events-none" />
                    <div className="flex items-center gap-4 relative z-10">
                        <div className="w-14 h-14 bg-gradient-to-br from-white/80 to-white/40 backdrop-blur-md rounded-2xl flex items-center justify-center ring-1 ring-white/80 shadow-[0_4px_15px_rgba(0,0,0,0.05)]">
                            <Server className="w-7 h-7 text-sky-600" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-br from-zinc-900 to-zinc-600 tracking-tight">Active Fleet Mapping</h2>
                            <p className="text-zinc-500 text-sm font-bold mt-1 uppercase tracking-widest">Assign machines to specific organizations</p>
                        </div>
                    </div>
                    <div className="px-6 py-3 bg-white/80 backdrop-blur-md rounded-2xl ring-1 ring-white/80 text-[11px] font-black text-zinc-700 uppercase tracking-widest shadow-[0_8px_30px_rgba(0,0,0,0.08)] flex items-center gap-3 relative z-10 hover:scale-105 transition-transform">
                        <div className="w-2 h-2 rounded-full bg-emerald-500 ring-4 ring-emerald-500/20 animate-pulse" />
                        {units.length} System(s) Detected
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-white/40 backdrop-blur-sm border-b border-white/60">
                                <th className="px-8 py-5 text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em]">Machine Identity</th>
                                <th className="px-8 py-5 text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em] text-center">Status</th>
                                <th className="px-8 py-5 text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em]">Last Activity</th>
                                <th className="px-8 py-5 text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em]">Org Assignment</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/40">
                            {units.map(unit => (
                                <tr key={unit.id} className="hover:bg-white/60 hover:shadow-[0_4px_20px_rgba(0,0,0,0.03)] transition-all duration-300 relative group">
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
                                                className="bg-white/60 backdrop-blur-md border border-white/80 ring-1 ring-zinc-200/50 shadow-inner rounded-xl px-4 py-2 text-xs font-black text-zinc-900 focus:ring-4 focus:ring-sky-500/20 focus:border-sky-500 outline-none transition-all hover:bg-white/90 cursor-pointer"
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
