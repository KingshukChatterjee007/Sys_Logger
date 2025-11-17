'use client'

import { useState, useEffect } from 'react'
import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'
import { ResponsiveContainer, LineChart, CartesianGrid, XAxis, YAxis, Tooltip as RechartsTooltip, Legend as RechartsLegend, Line as RechartsLine } from 'recharts'
import { UsageGraph } from '../components/UsageGraph'
import { useUsageData } from '../components/hooks/useUsageData'
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

interface UsageData {
  timestamp: string
  cpu: number
  ram: number
  gpu: string
  gpu_load?: number
}

export default function Dashboard() {
  const [dataSource, setDataSource] = useState<'local' | 'gist'>('local')
  const { data, loading, error, refetch } = useUsageData(dataSource)
  const [switchingSource, setSwitchingSource] = useState(false)

  // The useUsageData hook handles fetching and real-time updates

  // Data fetching is now handled by useUsageData hook

  const switchDataSource = (source: 'local' | 'gist') => {
    if (source !== dataSource) {
      setSwitchingSource(true)
      setDataSource(source)
      // Reset switching state after a short delay
      setTimeout(() => setSwitchingSource(false), 1000)
    }
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="text-center bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50 shadow-2xl">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-cyan-400 border-t-transparent mx-auto mb-6"></div>
          <h2 className="text-2xl font-semibold text-white mb-2">Initializing Dashboard</h2>
          <p className="text-slate-300">Loading system usage data...</p>
          <div className="mt-4 flex justify-center space-x-1">
            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse delay-75"></div>
            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse delay-150"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="text-center bg-red-900/20 backdrop-blur-sm rounded-2xl p-8 max-w-md border border-red-700/50 shadow-2xl">
          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">Connection Failed</h2>
          <p className="text-red-200 text-sm mb-4">{error}</p>
          <button
            onClick={refetch}
            className="bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 transform hover:scale-105 shadow-lg"
          >
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="text-center py-8 mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-xl flex items-center justify-center shadow-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-white via-cyan-200 to-white bg-clip-text text-transparent mb-3">
            System Monitor
          </h1>
          <p className="text-slate-300 text-xl max-w-2xl mx-auto mb-6">
            Advanced real-time monitoring dashboard for CPU, RAM, and GPU performance metrics
          </p>

          {/* Data Source Selector */}
          <div className="inline-flex bg-slate-800/50 backdrop-blur-sm rounded-full p-1 border border-slate-700/50">
            <button
              onClick={() => switchDataSource('local')}
              disabled={switchingSource}
              className={`px-6 py-3 rounded-full font-medium transition-all duration-200 flex items-center space-x-2 ${
                dataSource === 'local'
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              } ${switchingSource ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
              </svg>
              <span>Local Logs</span>
            </button>
            <button
              onClick={() => switchDataSource('gist')}
              disabled={switchingSource}
              className={`px-6 py-3 rounded-full font-medium transition-all duration-200 flex items-center space-x-2 ${
                dataSource === 'gist'
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              } ${switchingSource ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.374 0 0 5.373 0 12 0 17.302 3.438 21.8 8.207 23.387c.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
              </svg>
              <span>Gist</span>
            </button>
          </div>

          {switchingSource && (
            <div className="mt-4 flex items-center justify-center space-x-2 text-cyan-400">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-cyan-400 border-t-transparent"></div>
              <span className="text-sm">Switching data source...</span>
            </div>
          )}
        </header>

        {/* Usage Graphs */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <UsageGraph
            data={data}
            metric="cpu"
            loading={loading}
            error={error}
            onRetry={refetch}
          />
          <UsageGraph
            data={data}
            metric="ram"
            loading={loading}
            error={error}
            onRetry={refetch}
          />
          <UsageGraph
            data={data}
            metric="gpu"
            loading={loading}
            error={error}
            onRetry={refetch}
          />
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Current Stats */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 shadow-2xl border border-slate-700/50">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-red-600 rounded-lg flex items-center justify-center mr-3">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white">Current Usage</h3>
            </div>
            {data.length > 0 && (
              <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-300 font-medium">CPU</span>
                    <div className="flex items-center">
                      <div className="w-16 h-2 bg-slate-600 rounded-full mr-3 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-red-500 to-red-400 rounded-full transition-all duration-300"
                          style={{ width: `${Math.min(data[data.length - 1].cpu, 100)}%` }}
                        ></div>
                      </div>
                      <span className="text-red-400 font-bold text-lg">{data[data.length - 1].cpu.toFixed(1)}%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-300 font-medium">RAM</span>
                    <div className="flex items-center">
                      <div className="w-16 h-2 bg-slate-600 rounded-full mr-3 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full transition-all duration-300"
                          style={{ width: `${Math.min(data[data.length - 1].ram, 100)}%` }}
                        ></div>
                      </div>
                      <span className="text-blue-400 font-bold text-lg">{data[data.length - 1].ram.toFixed(1)}%</span>
                    </div>
                  </div>
                  {(data[data.length - 1].gpu_load ?? 0) > 0 && (
                    <div className="flex justify-between items-center p-3 bg-slate-700/30 rounded-lg">
                      <span className="text-slate-300 font-medium">GPU</span>
                      <div className="flex items-center">
                        <div className="w-16 h-2 bg-slate-600 rounded-full mr-3 overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-green-500 to-green-400 rounded-full transition-all duration-300"
                            style={{ width: `${Math.min(data[data.length - 1].gpu_load ?? 0, 100)}%` }}
                          ></div>
                        </div>
                        <span className="text-green-400 font-bold text-lg">{(data[data.length - 1].gpu_load ?? 0).toFixed(1)}%</span>
                      </div>
                    </div>
                  )}
                </div>
            )}
          </div>


          {/* System Status */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 shadow-2xl border border-slate-700/50">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-lg flex items-center justify-center mr-3">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white">System Status</h3>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-slate-700/30 rounded-lg">
                <span className="text-slate-300 text-sm">Data Points</span>
                <span className="text-cyan-400 font-bold">{data.length}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-slate-700/30 rounded-lg">
                <span className="text-slate-300 text-sm">Last Update</span>
                <span className="text-white font-bold text-sm">
                  {data.length > 0 ? formatTimestamp(data[data.length - 1].timestamp) : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-slate-700/30 rounded-lg">
                <span className="text-slate-300 text-sm">Auto Refresh</span>
                <span className="text-green-400 font-bold text-sm">5s</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="text-center py-8 mt-8 border-t border-slate-700/50">
          <p className="text-slate-400 text-sm">
            System Monitor • Real-time performance tracking • Built with Next.js & Flask
          </p>
        </footer>
      </div>
    </div>
  )
}
