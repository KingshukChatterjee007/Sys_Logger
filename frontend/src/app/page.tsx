'use client'

import { useState } from 'react'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'
import { UsageGraph } from '../components/UsageGraph'
import { useUsageData } from '../components/hooks/useUsageData'
import { useUnits } from '../components/hooks/useUnits'
import { Unit } from '../components/types'
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

export default function Dashboard() {
  const { data, loading, error, refetch, filteredData, setSelectedUnitId } = useUsageData()
  const { units, loading: unitsLoading } = useUnits()
  const [selectedUnit, setSelectedUnit] = useState<Unit | null>(null)
  const [switchingSource, setSwitchingSource] = useState(false)

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
            <p className="text-slate-400 text-sm">Loading system data</p>
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

  const displayData = selectedUnit ? filteredData : data
  const currentData = displayData.length > 0 ? displayData[displayData.length - 1] : null

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

        {/* Unit Selector */}
        <div className="p-4 border-b border-slate-700">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Units</div>
          <div className="space-y-2">
            <button
              onClick={() => {
                setSelectedUnitId(null)
                setSelectedUnit(null)
              }}
              className={`w-full px-4 py-3 rounded-lg transition-colors text-left flex items-center space-x-3 ${
                selectedUnit === null
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-300 hover:bg-slate-700'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <span className="font-medium">All Units</span>
            </button>
            {units.map((unit) => (
              <button
                key={unit.id}
                onClick={() => {
                  setSelectedUnitId(unit.id)
                  setSelectedUnit(unit)
                }}
                className={`w-full px-4 py-3 rounded-lg transition-colors text-left flex items-center space-x-3 ${
                  selectedUnit?.id === unit.id
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-700'
                }`}
              >
                <div className={`w-2 h-2 rounded-full ${unit.status === 'online' ? 'bg-green-400' : 'bg-red-400'}`}></div>
                <span className="font-medium">{unit.name}</span>
              </button>
            ))}
          </div>
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
              <div className="text-xl font-semibold text-white mb-1">{displayData.length}</div>
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
                data={displayData}
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
                data={displayData}
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
                data={displayData}
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
