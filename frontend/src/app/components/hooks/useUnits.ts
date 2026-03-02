import { useState, useEffect, useCallback, useRef } from 'react'
import { Unit, Alert } from '../types'
import { apiFetch } from './apiUtils'

export const useUnits = (orgId?: string) => {
  const [units, setUnits] = useState<Unit[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  const fetchUnits = useCallback(async () => {
    try {
      const endpoint = orgId ? `/api/orgs/${orgId}/units` : '/api/units'
      const response = await apiFetch(endpoint)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const result: Unit[] = await response.json()
      setUnits(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    }
  }, [])

  const fetchAlerts = useCallback(async () => {
    try {
      const response = await apiFetch('/api/alerts')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const result: Alert[] = await response.json()
      setAlerts(result)
    } catch (err) {
      console.error('Failed to fetch alerts:', err)
    }
  }, [])

  const connectWebSocket = useCallback(() => {
    // HTTP polling instead of WebSocket for reliability
    // This ensures we always get fresh data from the backend
    setTimeout(() => {
      fetchUnits()
      fetchAlerts()
      connectWebSocket()
    }, 1000) // Update every 1 second
  }, [fetchUnits, fetchAlerts])

  useEffect(() => {
    const initFetch = async () => {
      await Promise.all([fetchUnits(), fetchAlerts()])
      setLoading(false)
    }
    initFetch()
    connectWebSocket()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [fetchUnits, fetchAlerts, connectWebSocket])

  const acknowledgeAlert = useCallback(async (alertId: string) => {
    try {
      const response = await apiFetch(`/api/alerts/${alertId}/acknowledge`, {
        method: 'POST'
      } as any)
      if (!response.ok) {
        throw new Error('Failed to acknowledge alert')
      }
      // Update local state
      setAlerts(prev => prev.map(alert =>
        alert.id === alertId
          ? { ...alert, acknowledged: true }
          : alert
      ))
    } catch (err) {
      console.error('Failed to acknowledge alert:', err)
    }
  }, [])

  return {
    units,
    alerts,
    loading,
    error,
    isConnected,
    refetchUnits: fetchUnits,
    refetchAlerts: fetchAlerts,
    acknowledgeAlert
  }
}
