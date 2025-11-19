import { useState, useEffect, useCallback, useRef } from 'react'
import { Unit, Alert } from '../types'

export const useUnits = () => {
  const [units, setUnits] = useState<Unit[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  const fetchUnits = useCallback(async () => {
    try {
      const response = await fetch('/api/units')
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
      const response = await fetch('/api/alerts')
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
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return

    // Try to connect to the backend WebSocket directly
    const wsUrls = [
      'ws://localhost:5000/socket.io/?EIO=4&transport=websocket',
      'ws://127.0.0.1:5000/socket.io/?EIO=4&transport=websocket',
      'ws://localhost:5001/socket.io/?EIO=4&transport=websocket',
      'ws://127.0.0.1:5001/socket.io/?EIO=4&transport=websocket'
    ]

    let connected = false
    for (const wsUrl of wsUrls) {
      if (connected) break

      try {
        console.log('Attempting WebSocket connection to:', wsUrl)
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      setError(null)
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        if (message.type === 'units_update') {
          setUnits(message.data)
        } else if (message.type === 'alerts_update') {
          setAlerts(message.data)
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setError('WebSocket connection error')
      setIsConnected(false)
    }

    ws.onclose = () => {
      setIsConnected(false)
      // Auto-reconnect after 5 seconds
      setTimeout(() => {
        connectWebSocket()
      }, 5000)
    }
  }, [])

  useEffect(() => {
    const init = async () => {
      setLoading(true)
      await Promise.all([fetchUnits(), fetchAlerts()])
      setLoading(false)
    }
    init()
    connectWebSocket()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [fetchUnits, fetchAlerts, connectWebSocket])

  const acknowledgeAlert = useCallback(async (alertId: string) => {
    try {
      const response = await fetch(`/api/alerts/${alertId}/acknowledge`, {
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