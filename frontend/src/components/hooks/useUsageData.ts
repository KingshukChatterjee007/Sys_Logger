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

export const useUsageData = (orgId?: string): UseUsageDataReturn => {
  const [data, setData] = useState<UsageData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      let endpoint = ''
      if (selectedUnitId) {
        endpoint = `/api/unit/${selectedUnitId}/usage`
      } else if (orgId) {
        endpoint = `/api/orgs/${orgId}/usage`
      } else {
        endpoint = '/api/all-units-usage'
      }

      const response = await apiFetch(endpoint)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `HTTP error! status: ${response.status || 'Connection failed'}`)
      }

      const logs: UsageData[] = await response.json()

      // Process GPU data to extract load for charting
      const processedLogs = logs.map(log => {
        let gpu_load = 0

        if (log.gpu_load !== undefined && log.gpu_load !== null) {
          gpu_load = typeof log.gpu_load === 'number' ? log.gpu_load : 0
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
          gpu_load: gpu_load || 0
        }
      })

      setData(processedLogs)
      setLoading(false)
      setError(null)
    } catch (err) {
      console.error('Error fetching data:', err)
      setError(`Failed to connect to backend. Error: ${err}`)
      setLoading(false)
    }
  }, [orgId, selectedUnitId])

  const filteredData = useMemo(() => {
    return data
  }, [data])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 1000)
    return () => clearInterval(interval)
  }, [fetchData])

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