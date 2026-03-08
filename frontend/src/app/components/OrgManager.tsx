'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Building2, Plus, ArrowRight, Server, Shield, Globe, Check, AlertCircle } from 'lucide-react';
import { apiFetch } from './hooks/apiUtils';

interface Org {
    org_id: string;
    name: string;
}

interface Unit {
    id: string;
    name: string;
    hostname: string;
    org_id: string;
}

export function OrgManager() {
    const [orgs, setOrgs] = useState<Org[]>([]);
    const [units, setUnits] = useState<Unit[]>([]);
    const [loading, setLoading] = useState(true);

    const [newOrgId, setNewOrgId] = useState('');
    const [newOrgName, setNewOrgName] = useState('');
    const [createLoading, setCreateLoading] = useState(false);
    const [error, setError] = useState('');

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
        try {
            const resp = await apiFetch('/api/orgs', {
                method: 'POST',
                body: JSON.stringify({ org_id: newOrgId, name: newOrgName })
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.error || 'Failed to create organization');

            setNewOrgId('');
            setNewOrgName('');
            await fetchData();
        } catch (err: any) {
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
            </div>

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
                                <th className="px-8 py-4 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Current Assignment</th>
                                <th className="px-8 py-4 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Reassign Org</th>
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
                                                <div className="text-[10px] font-bold text-zinc-400 font-mono tracking-tight">{unit.hostname}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-8 py-5">
                                        <span className="px-3 py-1 bg-orange-50 text-orange-600 rounded-lg text-xs font-black tracking-widest uppercase ring-1 ring-orange-200">
                                            {unit.org_id || 'UNASSIGNED'}
                                        </span>
                                    </td>
                                    <td className="px-8 py-5">
                                        <select
                                            value={unit.org_id || ''}
                                            onChange={(e) => handleUpdateUnitOrg(unit.id, e.target.value)}
                                            className="bg-zinc-50 border-none ring-1 ring-zinc-200 rounded-xl px-4 py-2 text-xs font-bold text-zinc-900 focus:ring-2 focus:ring-orange-500/20"
                                        >
                                            <option value="" disabled>Select Org</option>
                                            {orgs.map(org => (
                                                <option key={org.org_id} value={org.org_id}>{org.org_id} - {org.name}</option>
                                            ))}
                                        </select>
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
