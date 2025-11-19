interface UsageData {
  timestamp: string
  cpu: number
  ram: number
  gpu: string
  gpu_load?: number
  temperature?: number
  network_rx?: number
  network_tx?: number
  unit_id: string
}

interface Unit {
  id: string
  name: string
  status: 'online' | 'offline' | 'warning'
  last_seen: string
  alerts?: Alert[]
}

interface Alert {
  id: string
  unit_id: string
  type: 'cpu' | 'ram' | 'gpu' | 'temperature' | 'network'
  message: string
  severity: 'low' | 'medium' | 'high'
  timestamp: string
  acknowledged: boolean
}

export type { UsageData, Unit, Alert }