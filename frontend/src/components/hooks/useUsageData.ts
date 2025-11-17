import { useState, useEffect, useCallback } from 'react'
import { UsageData } from '../types'

interface UseUsageDataReturn {
  data: UsageData[]
  loading: boolean
  error: string | null
  refetch: () => void
}

export const useUsageData = (dataSource: 'local' | 'gist' = 'local'): UseUsageDataReturn => {
  const [data, setData] = useState<UsageData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      const endpoint = dataSource === 'gist' ? '/api/gist-logs' : '/api/logs'
      const response = await fetch(`http://localhost:5000${endpoint}`, {
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
      }
      const logs: UsageData[] = await response.json()

      // Process GPU data to extract load for charting
      const processedLogs = logs.map(log => {
        const gpuData = log.gpu
        let gpu_load = 0

        if (log.gpu_load !== undefined && log.gpu_load !== null && log.gpu_load > 0) {
          // Use the already parsed gpu_load from API
          gpu_load = log.gpu_load
        } else if (gpuData) {
          // Parse from raw GPU data if API parsing failed
          console.log('Parsing from raw GPU data:', gpuData)
          // Look for "GPU Usage: X%" pattern
          if (gpuData.includes('GPU Usage: ')) {
            try {
              const usageMatch = gpuData.split('GPU Usage: ')[1].split('%')[0].trim()
              gpu_load = parseFloat(usageMatch)
              console.log('Parsed GPU usage:', gpu_load)
            } catch (e) {
              console.log('Failed to parse GPU usage:', e)
              gpu_load = 0
            }
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
      setError(`Failed to connect to backend. Make sure the backend is running. Error: ${err}`)
      setLoading(false)
    }
  }, [dataSource])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000) // Update every 5 seconds
    return () => clearInterval(interval)
  }, [fetchData])

  return {
    data,
    loading,
    error,
    refetch: fetchData
  }
}