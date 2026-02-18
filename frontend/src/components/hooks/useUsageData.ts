import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { UsageData } from '../types'
import { apiFetch, getApiUrl } from './apiUtils'
import { io, Socket } from 'socket.io-client'

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

  // Use Ref to track selectedUnitId inside socket listener without re-binding
  const selectedUnitIdRef = useRef<string | null>(null)

  useEffect(() => {
    selectedUnitIdRef.current = selectedUnitId
    // Clear data when switching units to avoid mixed graphs
    setData([])
    setLoading(true)
    // Re-fetch historical data for the new unit immediately
    fetchData()
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
        // If 404 or others, just return empty list
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
      // setError(`Failed to connect to backend. Error: ${err}`)
      setLoading(false)
    }
  }, [orgId, selectedUnitId]) // Re-fetch when unit changes // Removed selectedUnitId dependency to prevent loop, using ref

  // Socket.IO Integration - Stable Effect
  useEffect(() => {
    // If getApiUrl returns '' (HTTPS), we use '/' to indicate relative path
    const socketUrl = getApiUrl() || '/'
    console.log('Initializing Socket.IO connection to:', socketUrl)

    const socket: Socket = io(socketUrl, {
      path: '/socket.io/', // Explicitly set path to match Next.js rewrite
      transports: ['polling'], // FORCE polling to bypass potential proxy WebSocket issues
    })

    socket.on('connect', () => {
      console.log('Connected to WebSocket')
      if (orgId) {
        socket.emit('join_org', { org_id: orgId })
      }
    })

    socket.on('connect_error', (err) => {
      console.error('WebSocket Connection Error:', err)
    })

    socket.on('usage_update', (payload: { unit_id: string, data: any }) => {
      // console.log('Socket received usage_update:', payload)

      // Strict Org Filtering if orgId is active (Case-Insensitive)
      if (orgId && payload.data?.org_id && payload.data.org_id.toLowerCase() !== orgId.toLowerCase()) {
        return
      }

      const currentSelectedId = selectedUnitIdRef.current

      // Case-insensitive comparison if ID exists
      if (currentSelectedId && payload.unit_id.toLowerCase() !== currentSelectedId.toLowerCase()) {
        return;
      }

      setData(prevData => {
        const newLog = processLog(payload.data)
        const newData = [...prevData, newLog]
        // Keep only last 100 points
        if (newData.length > 200) return newData.slice(-100)
        return newData
      })
    })

    return () => {
      socket.disconnect()
    }
  }, [orgId]) // Socket doesn't restart on unit selection change anymore!

  // Initial Fetch & Polling Fallback
  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
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