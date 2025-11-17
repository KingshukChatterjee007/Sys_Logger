'use client'

import { useState } from 'react'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'
import { UsageGraph } from '../components/UsageGraph'
import { useUsageData } from '../components/hooks/useUsageData'
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

export default function Dashboard() {
  const [dataSource, setDataSource] = useState<'local' | 'gist'>('local')
  const { data, loading, error, refetch } = useUsageData(dataSource)
  const [switchingSource, setSwitchingSource] = useState(false)

  const switchDataSource = (source: 'local' | 'gist') => {
    if (source !== dataSource) {
      setSwitchingSource(true)
      setDataSource(source)
      setTimeout(() => setSwitchingSource(false), 1000)
    }
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex">
        <div className="w-64 bg-slate-800 border-r border-slate-700"></div>
        <div className="flex-1 ml-64 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent mx-auto mb-3"></div>
            <p className="text-slate-400 text-sm">Loading system data...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 flex">
        <div className="w-64 bg-slate-800 border-r border-slate-700"></div>
        <div className="flex-1 ml-64 flex items-center justify-center">
          <div className="text-center bg-red-900/20 border border-red-700/50 rounded p-6 max-w-md">
            <p className="text-red-400 text-sm mb-3">{error}</p>
            <button
              onClick={refetch}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded text-sm transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  const currentData = data.length > 0 ? data[data.length - 1] : null

  return (
    <div className="min-h-screen bg-slate-900 flex">
      {/* Left Sidebar - Fixed */}
      <div className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col fixed h-screen">
        {/* Sidebar Header */}
        <div className="p-6 border-b border-slate-700">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Lab Monitoring</h1>
              <p className="text-xs text-slate-400">System Analytics</p>
            </div>
          </div>
        </div>

        {/* Data Source Selector */}
        <div className="p-4 border-b border-slate-700">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Data Source</div>
          <div className="space-y-2">
            <button
              onClick={() => switchDataSource('local')}
              disabled={switchingSource}
              className={`w-full px-4 py-3 rounded-lg transition-colors text-left flex items-center space-x-3 ${
                dataSource === 'local'
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-300 hover:bg-slate-700'
              } ${switchingSource ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
              </svg>
              <span className="font-medium">Local</span>
            </button>
            <button
              onClick={() => switchDataSource('gist')}
              disabled={switchingSource}
              className={`w-full px-4 py-3 rounded-lg transition-colors text-left flex items-center space-x-3 ${
                dataSource === 'gist'
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-300 hover:bg-slate-700'
              } ${switchingSource ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.374 0 0 5.373 0 12 0 17.302 3.438 21.8 8.207 23.387c.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
              </svg>
              <span className="font-medium">Gist</span>
            </button>
          </div>
          {switchingSource && (
            <div className="mt-4 flex items-center space-x-2 text-blue-400 text-sm">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-400 border-t-transparent"></div>
              <span>Switching...</span>
            </div>
          )}
        </div>

        {/* Summary Stats in Sidebar */}
        <div className="p-4 overflow-y-auto flex-1">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Current Status</div>
          <div className="space-y-3">
            <div className="bg-slate-700/50 rounded-lg p-3 border border-slate-600">
              <div className="text-xs text-slate-400 mb-1">CPU</div>
              <div className="text-xl font-semibold text-white mb-2">
                {currentData ? `${currentData.cpu.toFixed(1)}%` : '0%'}
              </div>
              <div className="h-1.5 bg-slate-600 rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-500 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(currentData?.cpu || 0, 100)}%` }}
                ></div>
              </div>
            </div>

            <div className="bg-slate-700/50 rounded-lg p-3 border border-slate-600">
              <div className="text-xs text-slate-400 mb-1">Memory</div>
              <div className="text-xl font-semibold text-white mb-2">
                {currentData ? `${currentData.ram.toFixed(1)}%` : '0%'}
              </div>
              <div className="h-1.5 bg-slate-600 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(currentData?.ram || 0, 100)}%` }}
                ></div>
              </div>
            </div>

            <div className="bg-slate-700/50 rounded-lg p-3 border border-slate-600">
              <div className="text-xs text-slate-400 mb-1">GPU</div>
              <div className="text-xl font-semibold text-white mb-2">
                {currentData ? `${(currentData.gpu_load || 0).toFixed(1)}%` : '0%'}
              </div>
              <div className="h-1.5 bg-slate-600 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(currentData?.gpu_load || 0, 100)}%` }}
                ></div>
              </div>
            </div>

            <div className="bg-slate-700/50 rounded-lg p-3 border border-slate-600">
              <div className="text-xs text-slate-400 mb-1">Data Points</div>
              <div className="text-xl font-semibold text-white mb-1">{data.length}</div>
              <div className="text-xs text-slate-400">
                {currentData ? formatTimestamp(currentData.timestamp) : 'N/A'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area - Scrollable */}
      <div className="flex-1 ml-64 overflow-y-auto">
        {/* Header Bar */}
        <div className="bg-slate-800 border-b border-slate-700 sticky top-0 z-10">
          <div className="px-6 py-4">
            <h2 className="text-xl font-semibold text-white">Performance</h2>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-6 py-3">
        {/* Performance Graphs - Task Manager Style */}
        <div className="space-y-3">
          {/* CPU Usage */}
          <div className="bg-slate-800 border border-slate-700 rounded">
            <div className="px-4 py-2 border-b border-slate-700 bg-slate-800/50">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-white">CPU</h2>
                <span className="text-xs text-slate-400">
                  {currentData ? `${currentData.cpu.toFixed(1)}%` : '0%'}
                </span>
              </div>
            </div>
            <div className="p-3">
              <UsageGraph
                data={data}
                metric="cpu"
                loading={loading}
                error={error}
                onRetry={refetch}
                timeRange="1m"
              />
            </div>
          </div>

          {/* GPU Usage */}
          <div className="bg-slate-800 border border-slate-700 rounded">
            <div className="px-4 py-2 border-b border-slate-700 bg-slate-800/50">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-white">GPU</h2>
                <span className="text-xs text-slate-400">
                  {currentData ? `${(currentData.gpu_load || 0).toFixed(1)}%` : '0%'}
                </span>
              </div>
            </div>
            <div className="p-3">
              <UsageGraph
                data={data}
                metric="gpu"
                loading={loading}
                error={error}
                onRetry={refetch}
                timeRange="1m"
              />
            </div>
          </div>

          {/* Memory Usage */}
          <div className="bg-slate-800 border border-slate-700 rounded">
            <div className="px-4 py-2 border-b border-slate-700 bg-slate-800/50">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-white">Memory</h2>
                <span className="text-xs text-slate-400">
                  {currentData ? `${currentData.ram.toFixed(1)}%` : '0%'}
                </span>
              </div>
            </div>
            <div className="p-3">
              <UsageGraph
                data={data}
                metric="ram"
                loading={loading}
                error={error}
                onRetry={refetch}
                timeRange="1m"
              />
            </div>
          </div>
        </div>
        </div>
      </div>
    </div>
  )
}
