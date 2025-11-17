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
      
      // Try both ports 5000 and 5001 for compatibility
      const tryFetch = async (url: string): Promise<Response> => {
        return fetch(`${url}${endpoint}`, {
          mode: 'cors',
          headers: {
            'Content-Type': 'application/json',
          },
        })
      }

      let response: Response | null = null
      let apiUrl = ''

      // If NEXT_PUBLIC_API_URL is set, use it
      if (process.env.NEXT_PUBLIC_API_URL) {
        apiUrl = process.env.NEXT_PUBLIC_API_URL
        response = await tryFetch(apiUrl)
      } else {
        // Try 5001 first, then fallback to 5000
        const ports = ['5001', '5000']
        for (const port of ports) {
          try {
            apiUrl = `http://localhost:${port}`
            response = await tryFetch(apiUrl)
            if (response.ok) {
              break
            }
          } catch {
            // Continue to next port
            continue
          }
        }
      }

      if (!response || !response.ok) {
        const errorData = await response?.json().catch(() => ({}))
        throw new Error(errorData.error || `HTTP error! status: ${response?.status || 'Connection failed'}`)
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
          // Look for "GPU Usage: X%" pattern
          if (gpuData.includes('GPU Usage: ')) {
            try {
              const usageMatch = gpuData.split('GPU Usage: ')[1].split('%')[0].trim()
              gpu_load = parseFloat(usageMatch)
            } catch {
              // Silently fail and use 0
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
    const interval = setInterval(fetchData, 1000) // Update every 1 second
    return () => clearInterval(interval)
  }, [fetchData])

  return {
    data,
    loading,
    error,
    refetch: fetchData
  }
}