'use client'

import { useMemo } from 'react'
import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'
import { UsageData } from './types'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

interface UsageGraphProps {
  data: UsageData[]
  metric: 'cpu' | 'ram' | 'gpu'
  loading?: boolean
  error?: string | null
  onRetry?: () => void
  className?: string
}

export const UsageGraph: React.FC<UsageGraphProps> = ({
  data,
  metric,
  loading = false,
  error = null,
  onRetry,
  className = ''
}) => {
  const chartData = useMemo(() => {
    const labels = data.map(log => new Date(log.timestamp).toLocaleTimeString())

    let dataset: { label: string; data: number[]; borderColor: string; backgroundColor: string; fill: boolean; tension: number; pointRadius: number; pointHoverRadius: number }

    switch (metric) {
      case 'cpu':
        dataset = {
          label: 'CPU Usage',
          data: data.map(log => log.cpu),
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 5,
        }
        break
      case 'ram':
        dataset = {
          label: 'RAM Usage',
          data: data.map(log => log.ram),
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 5,
        }
        break
      case 'gpu':
        dataset = {
          label: 'GPU Usage',
          data: data.map(log => log.gpu_load || 0),
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 5,
        }
        break
    }

    return {
      labels,
      datasets: [dataset],
    }
  }, [data, metric])

  const chartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          color: '#e2e8f0',
          font: {
            size: 12,
          },
        },
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        titleColor: '#f1f5f9',
        bodyColor: '#cbd5e1',
        borderColor: 'rgba(71, 85, 105, 0.5)',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          title: (context: any) => {
            const index = context[0].dataIndex
            return new Date(data[index].timestamp).toLocaleString()
          },
          label: (context: any) => {
            return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`
          },
        },
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Time',
          color: '#94a3b8',
          font: {
            size: 14,
          },
        },
        ticks: {
          color: '#94a3b8',
          font: {
            size: 11,
          },
        },
        grid: {
          color: 'rgba(71, 85, 105, 0.3)',
        },
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Usage (%)',
          color: '#94a3b8',
          font: {
            size: 14,
          },
        },
        ticks: {
          color: '#94a3b8',
          font: {
            size: 11,
          },
          callback: (value: string | number) => `${value}%`,
        },
        grid: {
          color: 'rgba(71, 85, 105, 0.3)',
        },
        min: 0,
        max: 100,
      },
    },
    interaction: {
      intersect: false,
      mode: 'index' as const,
    },
  }), [data])

  if (loading) {
    return (
      <div className={`flex items-center justify-center bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-cyan-400 border-t-transparent mx-auto mb-6"></div>
          <h3 className="text-2xl font-semibold text-white mb-2">Loading Chart</h3>
          <p className="text-slate-300">Fetching usage data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center bg-red-900/20 backdrop-blur-sm rounded-2xl p-8 max-w-md border border-red-700/50 ${className}`}>
        <div className="text-center">
          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">Chart Error</h3>
          <p className="text-red-200 text-sm mb-4">{error}</p>
          <button
            onClick={onRetry}
            className="bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 transform hover:scale-105 shadow-lg"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  const getMetricTitle = (metric: string) => {
    switch (metric) {
      case 'cpu': return 'CPU Usage'
      case 'ram': return 'RAM Usage'
      case 'gpu': return 'GPU Usage'
      default: return 'Usage'
    }
  }

  const getMetricIcon = (metric: string) => {
    switch (metric) {
      case 'cpu':
        return (
          <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        )
      case 'ram':
        return (
          <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
          </svg>
        )
      case 'gpu':
        return (
          <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        )
      default:
        return null
    }
  }

  return (
    <div className={`bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 shadow-2xl border border-slate-700/50 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          {getMetricIcon(metric)}
          <div className="ml-3">
            <h3 className="text-xl font-semibold text-white">{getMetricTitle(metric)}</h3>
            <p className="text-slate-400 text-sm">Real-time performance metrics</p>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-sm text-slate-400">
          <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
          <span>Live</span>
        </div>
      </div>
      <div className="h-64">
        <Line data={chartData} options={chartOptions} />
      </div>
    </div>
  )
}