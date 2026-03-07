import { useState, useEffect, useCallback, useMemo } from 'react'
import { UsageData } from '../types'
import { apiFetch } from './apiUtils'

interface UseUsageDataReturn {
  data: UsageData[]
  loading: boolean
  error: string | null
  refetch: () => void
  selectedUnitId: string | null
  setSelectedUnitId: (id: string | null) => void
  filteredData: UsageData[]
  orgId?: string
  timeRange?: string
}

// Polling intervals scale depending on selected time range
const getPollIntervalForRange = (range: string) => {
  const map: Record<string, number> = {
    '30s': 2000,
    '1m': 2000,
    '5m': 5000,
    '15m': 10000,
    '30m': 15000,
    '1h': 30000,
    '3h': 60000,
    '6h': 120000,
    '12h': 300000,
    '1d': 300000, // Every 5 minutes for daily data
  }
  return map[range] || 2000
}

export const useUsageData = (orgId?: string, timeRange: string = '1m'): UseUsageDataReturn => {
  const [data, setData] = useState<UsageData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null)

  useEffect(() => {
    // Clear data when switching units or time range to avoid mixed graphs
    setData([])
    setLoading(true)
  }, [selectedUnitId, timeRange])

  const processLog = (log: any): UsageData => {
    let gpu_load = 0
    if (log.gpu_load !== undefined && log.gpu_load !== null) {
      gpu_load = typeof log.gpu_load === 'number' ? log.gpu_load : 0
    } else if (log.gpu_usage !== undefined && log.gpu_usage !== null) {
      gpu_load = typeof log.gpu_usage === 'number' ? log.gpu_usage : 0
    } else if (log.gpu !== undefined && log.gpu !== null) {
      const gpuData = log.gpu
      if (typeof gpuData === 'number') {
        gpu_load = gpuData
      } else if (typeof gpuData === 'string') {
        if (gpuData.includes('GPU Usage: ')) {
          try {
            const usageMatch = gpuData.split('GPU Usage: ')[1].split('%')[0].trim()
            gpu_load = parseFloat(usageMatch)
          } catch {
            gpu_load = 0
          }
        }
      } else if (typeof gpuData === 'object' && gpuData !== null) {
        const gpuObj = gpuData as Record<string, unknown>
        gpu_load = (gpuObj.overall_gpu_usage as number) || (gpuObj.gpu_load as number) || 0
      }
    }

    return {
      ...log,
      cpu: (log.cpu !== undefined) ? log.cpu : (log.cpu_usage || 0),
      ram: (log.ram !== undefined) ? log.ram : (log.ram_usage || 0),
      gpu_load: gpu_load || 0,
      network_rx: (log.network_rx !== undefined) ? log.network_rx : 0,
      network_tx: (log.network_tx !== undefined) ? log.network_tx : 0
    }
  }

  const fetchData = useCallback(async () => {
    try {
      let endpoint = ''
      if (selectedUnitId) {
        endpoint = `/api/units/${selectedUnitId}/usage?range=${timeRange}`
      } else if (orgId) {
        endpoint = `/api/usage?range=${timeRange}`
      } else {
        endpoint = `/api/usage?range=${timeRange}`
      }

      const response = await apiFetch(endpoint)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        console.warn('Fetch warning:', errorData)
        setData([])
        setLoading(false)
        return
      }

      const logs: UsageData[] = await response.json()
      const processedLogs = logs.map(processLog)

      setData(processedLogs)
      setLoading(false)
      setError(null)
    } catch (err) {
      console.error('Error fetching data:', err)
      setLoading(false)
    }
  }, [orgId, selectedUnitId, timeRange])

  // HTTP Polling (works reliably through Vercel HTTPS proxy)
  useEffect(() => {
    fetchData()
    const pollInterval = getPollIntervalForRange(timeRange)
    const interval = setInterval(fetchData, pollInterval)
    return () => clearInterval(interval)
  }, [fetchData, timeRange])

  const filteredData = useMemo(() => {
    return data
  }, [data])

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    selectedUnitId,
    setSelectedUnitId,
    filteredData,
    orgId,
    timeRange
  }
}