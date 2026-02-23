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
    fetchUnits()
    fetchAlerts()
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
      })
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

  const deleteUnit = useCallback(async (unitId: string) => {
    try {
      const response = await apiFetch(`/api/units/${unitId}`, {
        method: 'DELETE'
      })
      if (!response.ok) throw new Error('Failed to delete unit')
      await fetchUnits()
      return true
    } catch (err) {
      console.error('Error deleting unit:', err)
      return false
    }
  }, [fetchUnits])

  const updateUnit = useCallback(async (unitId: string, data: Partial<Unit>) => {
    try {
      const response = await apiFetch(`/api/units/${unitId}`, {
        method: 'PUT',
        body: JSON.stringify(data)
      })
      if (!response.ok) throw new Error('Failed to update unit')
      await fetchUnits()
      return true
    } catch (err) {
      console.error('Error updating unit:', err)
      return false
    }
  }, [fetchUnits])

  const deleteOrg = useCallback(async (orgId: string) => {
    try {
      const response = await apiFetch(`/api/orgs/${orgId}`, {
        method: 'DELETE'
      })
      if (!response.ok) throw new Error('Failed to delete organization')
      await fetchUnits()
      return true
    } catch (err) {
      console.error('Error deleting organization:', err)
      return false
    }
  }, [fetchUnits])

  const updateOrg = useCallback(async (orgId: string, newOrgId: string) => {
    try {
      const response = await apiFetch(`/api/orgs/${orgId}`, {
        method: 'PUT',
        body: JSON.stringify({ new_org_id: newOrgId })
      })
      if (!response.ok) throw new Error('Failed to rename organization')
      await fetchUnits()
      return true
    } catch (err) {
      console.error('Error updating organization:', err)
      return false
    }
  }, [fetchUnits])

  return {
    units,
    alerts,
    loading,
    error,
    isConnected,
    refetchUnits: fetchUnits,
    refetchAlerts: fetchAlerts,
    acknowledgeAlert,
    deleteUnit,
    updateUnit,
    deleteOrg,
    updateOrg
  }
}
