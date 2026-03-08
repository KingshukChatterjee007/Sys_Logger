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
}

// Polling interval in ms (2 seconds for near-real-time on live site)
const POLL_INTERVAL = 2000

export const useUsageData = (orgId?: string): UseUsageDataReturn => {
  const [data, setData] = useState<UsageData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null)

  useEffect(() => {
    // Clear data when switching units to avoid mixed graphs
    setData([])
    setLoading(true)
  }, [selectedUnitId])

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
        endpoint = `/api/units/${selectedUnitId}/usage`
      } else if (orgId) {
        endpoint = '/api/usage'
      } else {
        endpoint = '/api/usage'
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
      setData([]) // Clear stale telemetry on error
      setLoading(false)
    }
  }, [orgId, selectedUnitId])

  // HTTP Polling (works reliably through Vercel HTTPS proxy)
  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, POLL_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchData])

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
    filteredData
  }
}