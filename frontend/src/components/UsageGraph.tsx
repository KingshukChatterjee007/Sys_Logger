'use client'

import { useMemo, useState, useEffect } from 'react'
import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TooltipItem } from 'chart.js'
import { UsageData } from './types'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

type TimeRange = '30s' | '1m' | '5m' | '15m' | '30m' | '1h' | '3h' | '6h' | '12h' | '1d'

interface UsageGraphProps {
  data: UsageData[]
  metric: 'cpu' | 'ram' | 'gpu'
  loading?: boolean
  error?: string | null
  onRetry?: () => void
  className?: string
  timeRange?: TimeRange
}

export const UsageGraph: React.FC<UsageGraphProps> = ({
  data,
  metric,
  loading = false,
  error = null,
  onRetry,
  className = '',
  timeRange = '1m'
}) => {
  const [selectedTimeRange, setSelectedTimeRange] = useState<TimeRange>(timeRange)
  const [currentTime, setCurrentTime] = useState(() => Date.now())

  // Update current time every second to force re-filtering
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(Date.now())
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const filteredData = useMemo(() => {
    if (!data.length) return []

    // Sort data by timestamp to ensure chronological order
    const sortedData = [...data].sort((a, b) => {
      const timeA = new Date(a.timestamp).getTime()
      const timeB = new Date(b.timestamp).getTime()
      return timeA - timeB
    })

    const timeRanges = {
      '30s': 30 * 1000,
      '1m': 60 * 1000,
      '5m': 5 * 60 * 1000,
      '15m': 15 * 60 * 1000,
      '30m': 30 * 60 * 1000,
      '1h': 60 * 60 * 1000,
      '3h': 3 * 60 * 60 * 1000,
      '6h': 6 * 60 * 60 * 1000,
      '12h': 12 * 60 * 60 * 1000,
      '1d': 24 * 60 * 60 * 1000
    }

    // Get the most recent timestamp from data
    const latestTimestamp = sortedData.length > 0 
      ? new Date(sortedData[sortedData.length - 1].timestamp).getTime()
      : currentTime

    // Use the latest data timestamp as reference point instead of currentTime
    // This handles timezone differences and system clock issues
    const referenceTime = latestTimestamp > currentTime ? latestTimestamp : currentTime
    const cutoff = referenceTime - timeRanges[selectedTimeRange]
    
    const filtered = sortedData.filter(log => {
      const logTime = new Date(log.timestamp).getTime()
      return logTime >= cutoff
    })
    
    // If no data after filtering, show last N data points (fallback)
    // This ensures graphs always show something if data exists
    if (filtered.length === 0 && sortedData.length > 0) {
      const maxPoints = Math.min(sortedData.length, Math.ceil(timeRanges[selectedTimeRange] / 4000)) // 4s per point
      return sortedData.slice(-maxPoints)
    }
    
    return filtered
  }, [data, selectedTimeRange, currentTime])

  const chartData = useMemo(() => {
    if (!filteredData.length) {
      // Return empty chart data structure
      return {
        labels: [],
        datasets: [{
          label: 'Usage',
          data: [],
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 4,
          borderWidth: 2,
          pointHoverBorderWidth: 2,
        }]
      }
    }

    const labels = filteredData.map(log => {
      try {
        return new Date(log.timestamp).toLocaleTimeString()
      } catch {
        return new Date(log.timestamp).toString()
      }
    })

    let dataset: { label: string; data: number[]; borderColor: string; backgroundColor: string; fill: boolean; tension: number; pointRadius: number; pointHoverRadius: number; borderWidth?: number; pointHoverBorderWidth?: number }

    switch (metric) {
      case 'cpu':
        dataset = {
          label: 'CPU Usage',
          data: filteredData.map(log => log.cpu),
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 4,
          borderWidth: 2,
          pointHoverBorderWidth: 2,
        }
        break
      case 'ram':
        dataset = {
          label: 'RAM Usage',
          data: filteredData.map(log => log.ram),
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 4,
          borderWidth: 2,
          pointHoverBorderWidth: 2,
        }
        break
      case 'gpu':
        dataset = {
          label: 'GPU Usage',
          data: filteredData.map(log => log.gpu_load || 0),
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 4,
          borderWidth: 2,
          pointHoverBorderWidth: 2,
        }
        break
    }

    return {
      labels,
      datasets: [dataset],
    }
  }, [filteredData, metric])

  const chartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 200,
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        titleColor: '#e2e8f0',
        bodyColor: '#cbd5e1',
        borderColor: '#475569',
        borderWidth: 1,
        cornerRadius: 4,
        padding: 8,
        titleFont: {
          size: 11,
        },
        bodyFont: {
          size: 10,
        },
        callbacks: {
          title: (context: TooltipItem<'line'>[]) => {
            const index = context[0].dataIndex
            return new Date(filteredData[index].timestamp).toLocaleString()
          },
          label: (context: TooltipItem<'line'>) => {
            const value = context.parsed.y
            if (value === null) return ''
            return `${context.dataset.label || 'Usage'}: ${value.toFixed(1)}%`
          },
        },
      },
    },
    scales: {
      x: {
        display: true,
        ticks: {
          color: '#94a3b8',
          font: {
            size: 9,
          },
        },
        grid: {
          color: 'rgba(71, 85, 105, 0.3)',
        },
      },
      y: {
        display: true,
        ticks: {
          color: '#94a3b8',
          font: {
            size: 9,
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
  }), [filteredData])

  const timeRangeOptions: { value: TimeRange; label: string }[] = [
    { value: '30s', label: '30s' },
    { value: '1m', label: '1m' },
    { value: '5m', label: '5m' },
    { value: '15m', label: '15m' },
    { value: '30m', label: '30m' },
    { value: '1h', label: '1h' },
    { value: '3h', label: '3h' },
    { value: '6h', label: '6h' },
    { value: '12h', label: '12h' },
    { value: '1d', label: '1d' }
  ]

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-500 border-t-transparent mx-auto mb-2"></div>
          <p className="text-slate-400 text-xs">Loading...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`p-4 ${className}`}>
        <div className="text-center">
          <p className="text-red-400 text-xs mb-2">{error}</p>
          <button
            onClick={onRetry}
            className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={className}>
      {/* Time Range Selector */}
      <div className="flex flex-wrap gap-1 mb-3">
        {timeRangeOptions.map((option) => (
          <button
            key={option.value}
            onClick={() => setSelectedTimeRange(option.value)}
            className={`px-2 py-0.5 text-xs rounded transition-colors ${
              selectedTimeRange === option.value
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>
      <div className="h-36">
        <Line data={chartData} options={chartOptions} />
      </div>
    </div>
  )
}