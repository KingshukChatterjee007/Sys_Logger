import React, { useMemo, useState, useEffect } from 'react'
import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TooltipItem } from 'chart.js'
import { UsageData } from './types'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

type TimeRange = '30s' | '1m' | '5m' | '15m' | '30m' | '1h' | '3h' | '6h' | '12h' | '1d'

interface UsageGraphProps {
  data: UsageData[]
  metric: 'cpu' | 'ram' | 'gpu' | 'temperature' | 'network_rx' | 'network_tx'
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

  // Navigation & Time Helper: Standardize UTC to Local
  const toLocalTime = (timestamp: string) => {
    if (!timestamp) return 0
    // Fix: Only append Z if it looks like a naive string (no Z, no +/-, T separator)
    let iso = timestamp
    if (!iso.endsWith('Z') && !iso.includes('+') && (iso.match(/-/g) || []).length < 3) {
      // rough check: if only 2 hyphens (YYYY-MM-DD), and no +, assume naive UTC -> append Z
      // If it has offset (+05:30 or -05:00), Date() handles it.
      iso = timestamp + 'Z'
    }
    return new Date(iso).getTime()
  }

  const filteredData = useMemo(() => {
    if (!data.length) return []

    // Sort data by timestamp (Local Time) to ensure chronological order
    const sortedData = [...data].sort((a, b) => {
      return toLocalTime(a.timestamp) - toLocalTime(b.timestamp)
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

    // Get the most recent timestamp from data in Local Time
    const latestTimestamp = sortedData.length > 0
      ? toLocalTime(sortedData[sortedData.length - 1].timestamp)
      : currentTime

    const referenceTime = latestTimestamp > currentTime ? latestTimestamp : currentTime
    const cutoff = referenceTime - timeRanges[selectedTimeRange]

    const filtered = sortedData.filter(log => {
      return toLocalTime(log.timestamp) >= cutoff
    })

    if (filtered.length === 0 && sortedData.length > 0) {
      const maxPoints = Math.min(sortedData.length, Math.ceil(timeRanges[selectedTimeRange] / 4000))
      return sortedData.slice(-maxPoints)
    }

    return filtered
  }, [data, selectedTimeRange, currentTime])

  const chartData = useMemo(() => {
    if (!filteredData.length) {
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
        let iso = log.timestamp
        if (!iso.endsWith('Z') && !iso.includes('+') && (iso.match(/-/g) || []).length < 3) {
          iso = log.timestamp + 'Z'
        }
        return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
      } catch {
        return 'N/A'
      }
    })

    let dataset: any

    switch (metric) {
      case 'cpu':
        dataset = {
          label: 'CPU Usage',
          data: filteredData.map(log => log.cpu ?? log.cpu_usage ?? 0),
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
          data: filteredData.map(log => log.ram ?? log.ram_usage ?? 0),
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
          data: filteredData.map(log => {
            // Handle complex objects or usage keys
            if (typeof log.gpu === 'number') return log.gpu
            return log.gpu_load ?? log.gpu_usage ?? 0
          }),
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
      case 'temperature':
        dataset = {
          label: 'Temperature',
          data: filteredData.map(log => log.temperature || 0),
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 4,
          borderWidth: 2,
          pointHoverBorderWidth: 2,
        }
        break
      case 'network_rx':
        dataset = {
          label: 'Network RX (KB/s)',
          data: filteredData.map(log => log.network_rx || 0),
          borderColor: '#8b5cf6',
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 4,
          borderWidth: 2,
          pointHoverBorderWidth: 2,
        }
        break
      case 'network_tx':
        dataset = {
          label: 'Network TX (KB/s)',
          data: filteredData.map(log => log.network_tx || 0),
          borderColor: '#06b6d4',
          backgroundColor: 'rgba(6, 182, 212, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 4,
          borderWidth: 2,
          pointHoverBorderWidth: 2,
        }
        break
    }

    return { labels, datasets: [dataset] }
  }, [filteredData, metric])

  const chartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 200 },
    plugins: {
      legend: { display: false },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        titleColor: '#e2e8f0',
        bodyColor: '#cbd5e1',
        borderColor: '#475569',
        borderWidth: 1,
        cornerRadius: 4,
        padding: 8,
        callbacks: {
          title: (context: TooltipItem<'line'>[]) => {
            const index = context[0].dataIndex
            const dataPoint = filteredData[index]
            if (!dataPoint || !dataPoint.timestamp) return 'N/A'
            let iso = dataPoint.timestamp
            if (!iso.endsWith('Z') && !iso.includes('+') && (iso.match(/-/g) || []).length < 3) {
              iso = dataPoint.timestamp + 'Z'
            }
            return new Date(iso).toLocaleString()
          },
          label: (context: TooltipItem<'line'>) => {
            const value = context.parsed.y
            if (value === null) return ''
            // The data mapping already handles fallback to 0 for cpu/ram/gpu if undefined.
            // The 'value' here is already the processed number.
            const unit = (metric === 'cpu' || metric === 'ram' || metric === 'gpu') ? '%' :
              (metric === 'temperature') ? '°C' : ' KB/s'
            return `${context.dataset.label || 'Usage'}: ${value.toFixed(1)}${unit}`
          },
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: '#94a3b8',
          font: { size: 9 },
          autoSkip: true,
          maxTicksLimit: 8
        },
        grid: { color: 'rgba(71, 85, 105, 0.1)' },
      },
      y: {
        ticks: {
          color: '#94a3b8',
          font: { size: 9 },
          callback: (value: any) => {
            if (metric === 'cpu' || metric === 'ram' || metric === 'gpu') return `${value}%`
            return value
          }
        },
        grid: { color: 'rgba(71, 85, 105, 0.1)' },
        min: 0,
        max: (metric === 'cpu' || metric === 'ram' || metric === 'gpu') ? 100 : undefined,
      },
    },
    interaction: { intersect: false, mode: 'index' as const },
  }), [filteredData, metric])

  if (loading) return <div className="p-8 text-center text-slate-500">Loading Fleet Data...</div>
  if (error) return <div className="p-8 text-center text-red-400">{error}</div>

  return (
    <div className={className}>
      <div className="flex flex-wrap gap-1 mb-4">
        {['30s', '1m', '5m', '15m', '30m', '1h', '3h', '6h', '12h', '1d'].map((range) => (
          <button
            key={range}
            onClick={() => setSelectedTimeRange(range as TimeRange)}
            className={`px-3 py-1 text-[10px] font-bold rounded-lg transition-all ${selectedTimeRange === range
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
              : 'bg-slate-800 text-slate-500 hover:text-slate-300 hover:bg-slate-700'
              }`}
          >
            {range.toUpperCase()}
          </button>
        ))}
      </div>
      <div className="h-48">
        <Line data={chartData} options={chartOptions} />
      </div>
    </div>
  )
}