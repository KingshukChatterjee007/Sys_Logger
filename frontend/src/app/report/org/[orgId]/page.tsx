'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { 
  Shield, Printer, ArrowLeft, AlertCircle, Info, Server, Layers, Cpu, HardDrive, LayoutDashboard
} from 'lucide-react';

interface OrgReportData {
  org_id: string;
  fleet_size: number;
  node_summaries: Array<{
    name: string;
    avg_cpu: number;
    avg_ram: number;
  }>;
  insights: Array<{
    type: string;
    title: string;
    text: string;
  }>;
}

export default function OrgReportPage() {
  const { orgId } = useParams();
  const router = useRouter();
  const [data, setData] = useState<OrgReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`/api/reports/org/${orgId}`);
        if (!response.ok) throw new Error('Failed to fetch fleet report');
        const json = await response.json();
        setData(json);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [orgId]);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-50">
       <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-zinc-900 border-t-orange-500 rounded-full animate-spin" />
        <p className="font-black text-zinc-900 uppercase tracking-widest text-xs">Aggregating Fleet Intelligence...</p>
      </div>
    </div>
  );

  if (error || !data) return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-md w-full text-center">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-black text-zinc-900 mb-2">Fleet Audit Failed</h2>
        <p className="text-zinc-500 text-sm mb-6">{error}</p>
        <button onClick={() => router.push('/')} className="px-6 py-3 bg-zinc-900 text-white rounded-xl font-bold uppercase tracking-widest text-[10px]">Go Back</button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-zinc-100 p-4 md:p-8 lg:p-12 print:bg-white print:p-0">
      <div className="max-w-6xl mx-auto flex justify-between items-center mb-8 print:hidden">
        <button onClick={() => router.push('/')} className="flex items-center gap-2 text-zinc-500 hover:text-zinc-900 font-bold transition-colors uppercase tracking-widest text-[10px]">
          <ArrowLeft size={16} /> Back to Dashboard
        </button>
        <button onClick={() => window.print()} className="px-6 py-3 bg-zinc-900 text-white rounded-2xl font-black uppercase tracking-widest text-[10px] flex items-center gap-2 shadow-xl hover:bg-zinc-800 transition-all">
          <Printer size={16} /> Print Fleet Audit
        </button>
      </div>

      <div className="max-w-6xl mx-auto bg-white rounded-[3rem] shadow-2xl relative overflow-hidden print:shadow-none print:rounded-none">
        <div className="absolute top-0 left-0 w-full h-3 bg-zinc-900" />
        
        <header className="p-12 lg:p-20 border-b border-zinc-100 flex flex-col md:flex-row justify-between items-start md:items-center gap-10">
           <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-orange-500 rounded-xl shadow-lg shadow-orange-500/30">
                  <Layers size={24} className="text-white" />
                </div>
                <h1 className="text-4xl font-black text-zinc-900 tracking-tighter uppercase">Organization Audit</h1>
              </div>
              <p className="text-sm font-bold text-zinc-400 uppercase tracking-[0.2em]">Fleet Intelligence Report • {new Date().toLocaleDateString()}</p>
           </div>
           
            <div className="flex items-center gap-8">
               <div className="hidden lg:flex items-center gap-4 mr-8 border-r border-zinc-100 pr-8">
                  <img src="/krishishayogi.png" alt="Logo" className="h-10 object-contain" />
                  <img src="/Nielit_logo.jpeg" alt="Logo" className="h-12 object-contain mix-blend-multiply" />
                  <img src="/India-AI_logo.jpeg" alt="Logo" className="h-12 object-contain mix-blend-multiply" />
               </div>
               <div className="bg-zinc-50 border border-zinc-100 p-8 rounded-[2rem] flex items-center gap-10 min-w-[250px]">
                  <div>
                    <p className="text-[9px] font-black text-zinc-400 uppercase tracking-widest mb-1">Active Nodes</p>
                    <p className="text-4xl font-black text-zinc-900">{data.fleet_size}</p>
                  </div>
                  <div className="h-12 w-[1px] bg-zinc-200" />
                  <div>
                    <p className="text-[9px] font-black text-zinc-400 uppercase tracking-widest mb-1">Status</p>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse" />
                      <span className="text-sm font-black text-emerald-600 uppercase tracking-tighter">Healthy</span>
                    </div>
                  </div>
               </div>
            </div>
        </header>

        <div className="p-12 lg:p-20 space-y-20">
          {/* Intelligent Insights */}
          <section>
            <div className="flex items-center gap-3 mb-10">
               <LayoutDashboard className="text-orange-500" />
               <h2 className="text-xl font-black text-zinc-900 uppercase tracking-tight">Fleet Governance Analysis</h2>
            </div>
            <div className="grid md:grid-cols-2 gap-8">
               {data.insights.map((insight, idx) => (
                  <div key={idx} className="p-8 bg-zinc-50 border border-zinc-100 rounded-[2.5rem] flex gap-5">
                    <div className="p-3 bg-white rounded-2xl shadow-sm border border-zinc-100 h-fit">
                      {insight.type === 'info' ? <Info className="text-blue-500" /> : <AlertCircle className="text-orange-500" />}
                    </div>
                    <div>
                      <h3 className="font-black text-zinc-900 uppercase tracking-wide text-xs mb-2">{insight.title}</h3>
                      <p className="text-sm text-zinc-500 font-medium leading-relaxed">{insight.text}</p>
                    </div>
                  </div>
               ))}
            </div>
          </section>

          {/* Comparative Metrics */}
          <section>
            <div className="flex items-center gap-3 mb-10">
               <Server className="text-zinc-400" />
               <h2 className="text-xl font-black text-zinc-900 uppercase tracking-tight">Node Load Comparison</h2>
            </div>
            
            {data.node_summaries.length === 0 ? (
              <div className="bg-zinc-50 border border-dashed border-zinc-200 rounded-[2.5rem] p-16 text-center">
                <p className="text-sm font-bold text-zinc-400 uppercase tracking-widest">No node data available for comparison</p>
              </div>
            ) : (
              <div className="grid lg:grid-cols-2 gap-10">
                {/* CPU Comparison */}
                <div className="bg-zinc-50/50 p-10 rounded-[3rem] border border-zinc-100">
                  <div className="flex items-center gap-3 mb-8">
                    <div className="p-2 bg-white rounded-xl shadow-sm border border-zinc-100">
                      <Cpu size={18} className="text-zinc-400" />
                    </div>
                    <h3 className="text-sm font-black text-zinc-900 uppercase tracking-widest">Average CPU Load (%)</h3>
                  </div>
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={data.node_summaries} layout="vertical" margin={{ left: 20, right: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e4e4e7" />
                        <XAxis type="number" hide domain={[0, 100]} />
                        <YAxis dataKey="name" type="category" width={80} tick={{fontSize: 10, fontWeight: 'black', fill: '#71717a'}} axisLine={false} tickLine={false} />
                        <Tooltip cursor={{fill: 'transparent'}} contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'}} />
                        <Bar dataKey="avg_cpu" radius={[0, 10, 10, 0]} barSize={20}>
                          {data.node_summaries.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.avg_cpu > 70 ? '#f97316' : '#18181b'} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* RAM Comparison */}
                <div className="bg-zinc-50/50 p-10 rounded-[3rem] border border-zinc-100">
                  <div className="flex items-center gap-3 mb-8">
                    <div className="p-2 bg-white rounded-xl shadow-sm border border-zinc-100">
                      <HardDrive size={18} className="text-zinc-400" />
                    </div>
                    <h3 className="text-sm font-black text-zinc-900 uppercase tracking-widest">Average RAM Usage (%)</h3>
                  </div>
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={data.node_summaries} layout="vertical" margin={{ left: 20, right: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e4e4e7" />
                        <XAxis type="number" hide domain={[0, 100]} />
                        <YAxis dataKey="name" type="category" width={80} tick={{fontSize: 10, fontWeight: 'black', fill: '#71717a'}} axisLine={false} tickLine={false} />
                        <Tooltip cursor={{fill: 'transparent'}} contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'}} />
                        <Bar dataKey="avg_ram" radius={[0, 10, 10, 0]} barSize={20}>
                          {data.node_summaries.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.avg_ram > 70 ? '#6366f1' : '#3f3f46'} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            )}
          </section>

          {/* Node Metadata Table */}
          <section>
             <div className="bg-white border border-zinc-100 rounded-[2.5rem] overflow-hidden">
                <table className="w-full text-left">
                  <thead className="bg-zinc-50 border-b border-zinc-100">
                    <tr>
                      <th className="px-10 py-5 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Node Name</th>
                      <th className="px-10 py-5 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Avg CPU</th>
                      <th className="px-10 py-5 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Avg RAM</th>
                      <th className="px-10 py-5 text-[10px] font-black text-zinc-400 uppercase tracking-widest">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.node_summaries.map((node, i) => (
                      <tr key={i} className="border-b border-zinc-50 last:border-0">
                        <td className="px-10 py-6 font-black text-zinc-900">{node.name}</td>
                        <td className="px-10 py-6 font-mono font-bold text-zinc-600">{node.avg_cpu.toFixed(1)}%</td>
                        <td className="px-10 py-6 font-mono font-bold text-zinc-600">{node.avg_ram.toFixed(1)}%</td>
                        <td className="px-10 py-6">
                           <span className="px-3 py-1 bg-emerald-50 text-emerald-600 text-[9px] font-black uppercase tracking-widest rounded-lg">Operational</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
             </div>
          </section>
        </div>

        <footer className="p-16 text-center border-t border-zinc-100 bg-zinc-50/50">
           <p className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.3em]">Fleet Management & Intelligence Dashboard</p>
        </footer>
      </div>
    </div>
  );
}
