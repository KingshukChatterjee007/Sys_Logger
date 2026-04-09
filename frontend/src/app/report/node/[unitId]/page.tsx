'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area 
} from 'recharts';
import { 
  Activity, Shield, Download, Printer, ArrowLeft, AlertCircle, CheckCircle2, 
  Info, TrendingUp, Cpu, HardDrive, Wifi, Zap, Clock, Globe
} from 'lucide-react';

interface ReportData {
  system: {
    name: string;
    os: string;
    ip: string;
    cpu_model: string;
    ram_gb: number;
  };
  summary: {
    avg_cpu: number;
    max_cpu: number;
    avg_ram: number;
    max_ram: number;
    total_rx: number;
    total_tx: number;
  };
  health_score: number;
  insights: Array<{
    type: string;
    title: string;
    text: string;
  }>;
  timeline: Array<any>;
}

export default function NodeReportPage() {
  const { unitId } = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const range = searchParams.get('range') || '7d';
  
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`/api/reports/node/${unitId}?range=${range}`);
        if (!response.ok) throw new Error('Failed to fetch report data');
        const json = await response.json();
        setData(json);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [unitId, range]);

  const handlePrint = () => window.print();

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-50">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-orange-500 border-t-transparent rounded-full animate-spin" />
        <p className="font-black text-zinc-900 uppercase tracking-widest text-xs">Generating Intelligent Report...</p>
      </div>
    </div>
  );

  if (error || !data) return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-50 p-6">
      <div className="max-w-md w-full bg-white p-8 rounded-[2rem] shadow-xl text-center">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-black text-zinc-900 mb-2">Report Generation Failed</h2>
        <p className="text-zinc-500 text-sm mb-6">{error || 'Data could not be processed.'}</p>
        <button onClick={() => router.push('/')} className="px-6 py-3 bg-zinc-900 text-white rounded-xl font-bold uppercase tracking-widest text-[10px]">Go Back</button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-zinc-100 p-4 md:p-8 lg:p-12 print:bg-white print:p-0">
      {/* Top Navigation - Hidden on Print */}
      <div className="max-w-6xl mx-auto flex justify-between items-center mb-8 print:hidden">
        <button 
          onClick={() => router.push('/')}
          className="flex items-center gap-2 text-zinc-500 hover:text-zinc-900 font-bold transition-colors group"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          <span className="text-xs uppercase tracking-widest">Dashboard</span>
        </button>
        <div className="flex gap-3">
           <button 
            onClick={handlePrint}
            className="px-6 py-3 bg-white border border-zinc-200 text-zinc-900 rounded-2xl font-black uppercase tracking-widest text-[10px] flex items-center gap-2 hover:bg-zinc-50 transition-all shadow-sm"
          >
            <Printer size={16} /> Save as PDF
          </button>
        </div>
      </div>

      {/* Main Report Container */}
      <div className="max-w-6xl mx-auto bg-white rounded-[3rem] shadow-2xl overflow-hidden print:shadow-none print:rounded-none relative">
        <div className="absolute top-0 left-0 w-full h-3 bg-gradient-to-r from-orange-500 via-zinc-900 to-emerald-500" />
        
        {/* Report Header */}
        <header className="p-10 lg:p-16 border-b border-zinc-100 flex flex-col md:flex-row justify-between items-start md:items-center gap-8">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-zinc-900 rounded-xl">
                <Shield size={24} className="text-orange-500" />
              </div>
              <h1 className="text-3xl font-black text-zinc-900 tracking-tight uppercase">Audit Report</h1>
            </div>
            <div className="flex flex-wrap gap-4 text-xs font-bold text-zinc-500">
              <div className="flex items-center gap-1.5 uppercase tracking-widest bg-zinc-50 px-3 py-1.5 rounded-lg border border-zinc-100">
                <Clock size={12} className="text-zinc-400" /> {new Date().toLocaleDateString()}
              </div>
              <div className="flex items-center gap-1.5 uppercase tracking-widest bg-zinc-50 px-3 py-1.5 rounded-lg border border-zinc-100">
                <Globe size={12} className="text-zinc-400" /> Range: {range === '1d' ? '24 Hours' : range === '7d' ? '7 Days' : range === '30d' ? '30 Days' : '1 Year'}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-8">
            <div className="hidden lg:flex items-center gap-4 mr-8 border-r border-zinc-100 pr-8">
               <img src="/krishishayogi.png" alt="Logo" className="h-12 lg:h-14 object-contain mix-blend-multiply" />
               <img src="/Nielit_logo.jpeg" alt="Logo" className="h-14 object-contain mix-blend-multiply" />
               <img src="/India-AI_logo.jpeg" alt="Logo" className="h-14 object-contain mix-blend-multiply" />
            </div>
            <div className="text-right">
              <p className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-1">Health Score</p>
              <div className="flex items-baseline gap-1">
                <span className={`text-5xl font-black ${data.health_score > 80 ? 'text-emerald-500' : data.health_score > 50 ? 'text-orange-500' : 'text-red-500'}`}>
                  {data.health_score}
                </span>
                <span className="text-zinc-400 font-bold">/100</span>
              </div>
            </div>
          </div>
        </header>

        {/* System Details Bar */}
        <div className="bg-zinc-50/50 p-10 border-b border-zinc-100 grid grid-cols-2 lg:grid-cols-4 gap-8">
           <div>
            <p className="text-[9px] font-black text-zinc-400 uppercase tracking-[0.2em] mb-2">Hostname</p>
            <p className="text-sm font-black text-zinc-900 break-all uppercase">{data.system.name}</p>
          </div>
          <div>
            <p className="text-[9px] font-black text-zinc-400 uppercase tracking-[0.2em] mb-2">Platform</p>
            <p className="text-sm font-bold text-zinc-600 uppercase italic">{data.system.os || 'UNKNOWN'}</p>
          </div>
          <div>
            <p className="text-[9px] font-black text-zinc-400 uppercase tracking-[0.2em] mb-2">IP Address</p>
            <p className="text-sm font-mono font-bold text-zinc-600">{data.system.ip || '---.---.---.---'}</p>
          </div>
          <div>
            <p className="text-[9px] font-black text-zinc-400 uppercase tracking-[0.2em] mb-2">Resources</p>
            <p className="text-sm font-bold text-zinc-600">{data.system.ram_gb}GB Physical Mem</p>
          </div>
        </div>

        <div className="p-10 lg:p-16 space-y-16">
          {/* Intelligence Section */}
          <section>
            <div className="flex items-center gap-2 mb-8">
              <Zap className="w-5 h-5 text-orange-500" />
              <h2 className="text-xl font-black text-zinc-900 tracking-tight uppercase">Intelligent Analysis</h2>
            </div>
            <div className="grid md:grid-cols-2 gap-6">
              {data.insights.map((insight, idx) => (
                <div key={idx} className={`p-6 rounded-[2rem] border transition-all ${
                  insight.type === 'critical' ? 'bg-red-50 border-red-100' :
                  insight.type === 'warning' ? 'bg-orange-50 border-orange-100' :
                  insight.type === 'optimization' ? 'bg-emerald-50 border-emerald-100' :
                  'bg-zinc-50 border-zinc-100'
                }`}>
                  <div className="flex items-start gap-4">
                    <div className={`p-2 rounded-xl shrink-0 ${
                      insight.type === 'critical' ? 'bg-red-500 text-white' :
                      insight.type === 'warning' ? 'bg-orange-500 text-white' :
                      insight.type === 'optimization' ? 'bg-emerald-500 text-white' :
                      'bg-zinc-200 text-zinc-600'
                    }`}>
                      {insight.type === 'critical' ? <AlertCircle size={20} /> :
                       insight.type === 'warning' ? <AlertCircle size={20} /> :
                       insight.type === 'optimization' ? <CheckCircle2 size={20} /> :
                       <Info size={20} />}
                    </div>
                    <div>
                      <h3 className={`font-black text-sm uppercase tracking-wide mb-1 ${
                        insight.type === 'critical' ? 'text-red-700' :
                        insight.type === 'warning' ? 'text-orange-700' :
                        insight.type === 'optimization' ? 'text-emerald-700' :
                        'text-zinc-700'
                      }`}>{insight.title}</h3>
                      <p className="text-sm text-zinc-600 font-medium leading-relaxed">{insight.text}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Visualization Section */}
          <section>
             <div className="flex items-center gap-2 mb-8">
              <TrendingUp className="w-5 h-5 text-orange-500" />
              <h2 className="text-xl font-black text-zinc-900 tracking-tight uppercase">Fleet Telemetry Timeline</h2>
            </div>
            
            {data.timeline.length === 0 ? (
              <div className="bg-zinc-50 border border-dashed border-zinc-200 rounded-[2.5rem] p-20 text-center">
                <AlertCircle className="w-10 h-10 text-zinc-300 mx-auto mb-4" />
                <p className="text-sm font-bold text-zinc-400 uppercase tracking-widest">No timeline data available for this period</p>
              </div>
            ) : (
              <div className="space-y-10">
                {/* CPU Chart */}
                <div className="bg-zinc-50/50 p-8 rounded-[2.5rem] border border-zinc-100 relative">
                  <div className="flex justify-between items-center mb-8">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-white rounded-xl shadow-sm flex items-center justify-center border border-zinc-100">
                        <Cpu className="w-5 h-5 text-zinc-400" />
                      </div>
                      <div>
                        <h3 className="text-xs font-black text-zinc-900 uppercase tracking-widest">CPU Processor Load</h3>
                        <p className="text-[10px] text-zinc-400 font-bold">AVG: {data.summary.avg_cpu.toFixed(1)}% | MAX: {data.summary.max_cpu.toFixed(1)}%</p>
                      </div>
                    </div>
                  </div>
                  <div className="w-full overflow-x-auto pb-4 custom-scrollbar">
                    <div style={{ width: Math.max(100, (data.timeline.length / 100) * 10) + '%' }} className="h-[250px] min-w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data.timeline} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                          <defs>
                            <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#f97316" stopOpacity={0.1}/>
                              <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E4E4E7" />
                          <XAxis 
                            dataKey="timestamp" 
                            tick={{fontSize: 8, fontWeight: 'bold', fill: '#A1A1AA'}}
                            tickFormatter={(val) => new Date(val).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            axisLine={false}
                            tickLine={false}
                            minTickGap={100}
                          />
                          <YAxis 
                            tick={{fontSize: 10, fontWeight: 'bold', fill: '#A1A1AA'}}
                            unit="%"
                            domain={[0, 100]}
                            axisLine={false}
                            tickLine={false}
                          />
                          <Tooltip 
                            contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)', fontSize: '10px', fontWeight: 'bold'}}
                          />
                          <Area type="monotone" dataKey="cpu_usage" name="CPU Usage" stroke="#f97316" strokeWidth={2} fillOpacity={1} fill="url(#colorCpu)" animationDuration={500} connectNulls />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                {/* RAM Chart */}
                <div className="bg-zinc-50/50 p-8 rounded-[2.5rem] border border-zinc-100 relative">
                  <div className="flex justify-between items-center mb-8">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-white rounded-xl shadow-sm flex items-center justify-center border border-zinc-100">
                        <HardDrive className="w-5 h-5 text-zinc-400" />
                      </div>
                      <div>
                        <h3 className="text-xs font-black text-zinc-900 uppercase tracking-widest">Memory Utilization</h3>
                        <p className="text-[10px] text-zinc-400 font-bold">AVG: {data.summary.avg_ram.toFixed(1)}% | MAX: {data.summary.max_ram.toFixed(1)}%</p>
                      </div>
                    </div>
                  </div>
                  <div className="w-full overflow-x-auto pb-4 custom-scrollbar">
                    <div style={{ width: Math.max(100, (data.timeline.length / 100) * 10) + '%' }} className="h-[250px] min-w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data.timeline} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                          <defs>
                            <linearGradient id="colorRam" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                              <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E4E4E7" />
                          <XAxis 
                            dataKey="timestamp" 
                            tick={{fontSize: 8, fontWeight: 'bold', fill: '#A1A1AA'}}
                            tickFormatter={(val) => new Date(val).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            axisLine={false}
                            tickLine={false}
                            minTickGap={100}
                          />
                          <YAxis tick={{fontSize: 10, fontWeight: 'bold', fill: '#A1A1AA'}} unit="%" domain={[0, 100]} axisLine={false} tickLine={false} />
                          <Tooltip contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)', fontSize: '10px', fontWeight: 'bold'}} />
                          <Area type="monotone" dataKey="ram_usage" name="RAM Usage" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorRam)" animationDuration={500} connectNulls />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                {/* GPU Chart */}
                <div className="bg-zinc-50/50 p-8 rounded-[2.5rem] border border-zinc-100 relative">
                  <div className="flex justify-between items-center mb-8">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-white rounded-xl shadow-sm flex items-center justify-center border border-zinc-100">
                        <Zap className="w-5 h-5 text-zinc-400" />
                      </div>
                      <div>
                        <h3 className="text-xs font-black text-zinc-900 uppercase tracking-widest">GPU Cloud Compute</h3>
                        <p className="text-[10px] text-zinc-400 font-bold">Accelerator Load Profile (%)</p>
                      </div>
                    </div>
                  </div>
                  <div className="w-full overflow-x-auto pb-4 custom-scrollbar">
                    <div style={{ width: Math.max(100, (data.timeline.length / 100) * 10) + '%' }} className="h-[250px] min-w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data.timeline} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                          <defs>
                            <linearGradient id="colorGpu" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#ec4899" stopOpacity={0.1}/>
                              <stop offset="95%" stopColor="#ec4899" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E4E4E7" />
                          <XAxis 
                            dataKey="timestamp" 
                            tick={{fontSize: 8, fontWeight: 'bold', fill: '#A1A1AA'}}
                            tickFormatter={(val) => new Date(val).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            axisLine={false}
                            tickLine={false}
                            minTickGap={100}
                          />
                          <YAxis tick={{fontSize: 10, fontWeight: 'bold', fill: '#A1A1AA'}} unit="%" domain={[0, 100]} axisLine={false} tickLine={false} />
                          <Tooltip contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)', fontSize: '10px', fontWeight: 'bold'}} />
                          <Area type="monotone" dataKey="gpu_usage" name="GPU Usage" stroke="#ec4899" strokeWidth={2} fillOpacity={1} fill="url(#colorGpu)" animationDuration={500} connectNulls />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                {/* Network Chart */}
                <div className="bg-zinc-50/50 p-8 rounded-[2.5rem] border border-zinc-100 relative">
                  <div className="flex justify-between items-center mb-8">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-white rounded-xl shadow-sm flex items-center justify-center border border-zinc-100">
                        <Wifi className="w-5 h-5 text-zinc-400" />
                      </div>
                      <div>
                        <h3 className="text-xs font-black text-zinc-900 uppercase tracking-widest">Network Throughput</h3>
                        <p className="text-[10px] text-zinc-400 font-bold">Inbound (RX) vs Outbound (TX)</p>
                      </div>
                    </div>
                  </div>
                  <div className="w-full overflow-x-auto pb-4 custom-scrollbar">
                    <div style={{ width: Math.max(100, (data.timeline.length / 100) * 10) + '%' }} className="h-[300px] min-w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data.timeline} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                          <defs>
                            <linearGradient id="colorRx" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#10b981" stopOpacity={0.1}/>
                              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                            </linearGradient>
                            <linearGradient id="colorTx" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.1}/>
                              <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E4E4E7" />
                          <XAxis 
                            dataKey="timestamp" 
                            tick={{fontSize: 8, fontWeight: 'bold', fill: '#A1A1AA'}}
                            tickFormatter={(val) => new Date(val).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            axisLine={false}
                            tickLine={false}
                            minTickGap={100}
                          />
                          <YAxis tick={{fontSize: 10, fontWeight: 'bold', fill: '#A1A1AA'}} unit=" MB" axisLine={false} tickLine={false} />
                          <Tooltip contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)', fontSize: '10px', fontWeight: 'bold'}} />
                          <Area type="monotone" dataKey="network_rx_mb" name="Download (RX)" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorRx)" animationDuration={500} connectNulls />
                          <Area type="monotone" dataKey="network_tx_mb" name="Upload (TX)" stroke="#4f46e5" strokeWidth={2} fillOpacity={1} fill="url(#colorTx)" animationDuration={500} connectNulls />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </section>

          {/* Bottom Summary Table */}
          <section className="bg-zinc-900 text-white rounded-[2.5rem] p-12 overflow-hidden relative">
             <div className="absolute top-0 right-0 w-64 h-64 bg-orange-500/10 rounded-full blur-3xl pointer-events-none" />
             <div className="relative z-10 grid grid-cols-2 lg:grid-cols-4 gap-12 text-center">
                <div>
                  <p className="text-[9px] font-black text-zinc-500 uppercase tracking-[0.2em] mb-4">Network Inbound</p>
                  <p className="text-3xl font-black text-white">{data.summary.total_rx > 1024 ? (data.summary.total_rx/1024).toFixed(2) + ' GB' : data.summary.total_rx.toFixed(2) + ' MB'}</p>
                </div>
                <div>
                  <p className="text-[9px] font-black text-zinc-500 uppercase tracking-[0.2em] mb-4">Network Outbound</p>
                  <p className="text-3xl font-black text-white">{data.summary.total_tx > 1024 ? (data.summary.total_tx/1024).toFixed(2) + ' GB' : data.summary.total_tx.toFixed(2) + ' MB'}</p>
                </div>
                <div>
                  <p className="text-[9px] font-black text-zinc-500 uppercase tracking-[0.2em] mb-4">Peak CPU Workload</p>
                  <p className="text-3xl font-black text-white">{data.summary.max_cpu.toFixed(1)}<span className="text-orange-500 text-sm">%</span></p>
                </div>
                <div>
                  <p className="text-[9px] font-black text-zinc-500 uppercase tracking-[0.2em] mb-4">Data Points Scanned</p>
                  <p className="text-3xl font-black text-white">{data.timeline.length}</p>
                </div>
             </div>
          </section>
        </div>

        <footer className="p-10 text-center border-t border-zinc-100">
           <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.3em]">Built for Sys_Logger Intelligent Network Monitor</p>
        </footer>
      </div>
    </div>
  );
}
