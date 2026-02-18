'use client'

import React, { useMemo, useState, useEffect, useRef } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TooltipItem,
  ScriptableContext
} from 'chart.js'
import { UsageData } from './types'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

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
  const chartRef = useRef<any>(null)

  // Update current time every second to force re-filtering
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(Date.now())
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const parseTimestamp = (timestamp: string) => {
    if (!timestamp) return 0
    try {
      // If it's a naive ISO string from Python (2026-02-18T...), 
      // new Date() treats it as local time correctly.
      // If we want to be safe against different browser behaviors:
      const d = new Date(timestamp)
      return isNaN(d.getTime()) ? 0 : d.getTime()
    } catch {
      return 0
    }
  }

  const filteredData = useMemo(() => {
    if (!data.length) return []

    const sortedData = [...data].sort((a, b) => {
      return parseTimestamp(a.timestamp) - parseTimestamp(b.timestamp)
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

    const latestTimestamp = sortedData.length > 0
      ? parseTimestamp(sortedData[sortedData.length - 1].timestamp)
      : currentTime

    const referenceTime = latestTimestamp > currentTime ? latestTimestamp : currentTime
    const cutoff = referenceTime - timeRanges[selectedTimeRange]

    const filtered = sortedData.filter(log => {
      return parseTimestamp(log.timestamp) >= cutoff
    })

    // If no data in range, show last few points to avoid blank screen
    if (filtered.length === 0 && sortedData.length > 0) {
      return sortedData.slice(-20)
    }

    return filtered
  }, [data, selectedTimeRange, currentTime])

  const chartData = useMemo(() => {
    const labels = filteredData.map(log => {
      const d = new Date(log.timestamp)
      if (isNaN(d.getTime())) return 'N/A'
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
    })

    const getMetricColor = () => {
      switch (metric) {
        case 'cpu': return { border: '#3b82f6', bg: 'rgba(59, 130, 246, 0.2)' }
        case 'ram': return { border: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.2)' }
        case 'gpu': return { border: '#10b981', bg: 'rgba(16, 185, 129, 0.2)' }
        case 'network_rx': return { border: '#06b6d4', bg: 'rgba(6, 182, 212, 0.2)' }
        case 'network_tx': return { border: '#0ea5e9', bg: 'rgba(14, 165, 233, 0.2)' }
        case 'temperature': return { border: '#f59e0b', bg: 'rgba(245, 158, 11, 0.2)' }
        default: return { border: '#64748b', bg: 'rgba(100, 116, 139, 0.2)' }
      }
    }

    const colors = getMetricColor()

    const dataset = {
      label: metric.toUpperCase(),
      data: filteredData.map(log => {
        if (metric === 'cpu') return log.cpu ?? log.cpu_usage ?? 0
        if (metric === 'ram') return log.ram ?? log.ram_usage ?? 0
        if (metric === 'gpu') return typeof log.gpu === 'number' ? log.gpu : (log.gpu_load ?? log.gpu_usage ?? 0)
        return (log as any)[metric] ?? 0
      }),
      borderColor: colors.border,
      backgroundColor: (context: ScriptableContext<'line'>) => {
        const chart = context.chart
        const { ctx, chartArea } = chart
        if (!chartArea) return 'transparent'
        const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom)
        gradient.addColorStop(0, colors.bg)
        gradient.addColorStop(1, 'transparent')
        return gradient
      },
      fill: true,
      tension: 0.4,
      pointRadius: 0,
      pointHoverRadius: 4,
      pointHoverBackgroundColor: colors.border,
      pointHoverBorderColor: '#fff',
      pointHoverBorderWidth: 2,
      borderWidth: 2,
    }

    return { labels, datasets: [dataset] }
  }, [filteredData, metric])

  const chartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 400, easing: 'easeOutQuart' as const },
    plugins: {
      legend: { display: false },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(2, 6, 23, 0.9)',
        titleColor: '#94a3b8',
        bodyColor: '#fff',
        titleFont: { size: 10, weight: 'bold' as const },
        bodyFont: { size: 12, family: 'monospace', weight: 'bold' as const },
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        cornerRadius: 8,
        padding: 12,
        displayColors: false,
        callbacks: {
          title: (context: TooltipItem<'line'>[]) => {
            const index = context[0].dataIndex
            const dataPoint = filteredData[index]
            if (!dataPoint?.timestamp) return 'UPLINK LOST'
            return new Date(dataPoint.timestamp).toLocaleString()
          },
          label: (context: TooltipItem<'line'>) => {
            const value = context.parsed.y
            if (value === null || value === undefined) return '➤ DATA UNAVAILABLE'
            const unit = (metric === 'cpu' || metric === 'ram' || metric === 'gpu') ? '%' :
              (metric === 'temperature') ? '°C' : ' KB/s'
            return `➤ ${value.toFixed(1)}${unit}`
          },
        },
      },
    },
    scales: {
      x: {
        display: false,
        grid: { display: false },
      },
      y: {
        position: 'right' as const,
        ticks: {
          color: 'rgba(148, 163, 184, 0.4)',
          font: { size: 8, family: 'monospace' },
          maxTicksLimit: 5,
          callback: (value: any) => {
            if (metric === 'cpu' || metric === 'ram' || metric === 'gpu') return `${value}%`
            return value
          }
        },
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        min: 0,
        max: (metric === 'cpu' || metric === 'ram' || metric === 'gpu') ? 100 : undefined,
      },
    },
    interaction: { intersect: false, mode: 'index' as const },
  }), [filteredData, metric])

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-full gap-2">
      <div className="w-4 h-4 border-2 border-blue-500/20 border-t-blue-400 rounded-full animate-spin" />
      <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">Hydrating...</span>
    </div>
  )
  if (error) return <div className="p-8 text-center text-red-400 font-bold text-[10px] uppercase">{error}</div>

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div className="flex flex-wrap gap-1 mb-2">
        {['30s', '1m', '5m', '15m', '30m', '1h', '6h', '1d'].map((range) => (
          <button
            key={range}
            onClick={() => setSelectedTimeRange(range as TimeRange)}
            className={cn(
              "px-2 py-0.5 text-[8px] font-black rounded-md transition-all uppercase tracking-widest border",
              selectedTimeRange === range
                ? 'bg-white/10 text-white border-white/20'
                : 'text-slate-600 border-transparent hover:text-slate-400 hover:bg-white/5'
            )}
          >
            {range}
          </button>
        ))}
      </div>
      <div className="flex-1 min-h-0 relative">
        <Line ref={chartRef} data={chartData} options={chartOptions} />
      </div>
    </div>
  )
}