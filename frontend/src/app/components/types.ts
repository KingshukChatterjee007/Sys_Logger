export interface UsageData {
  timestamp: string
  cpu: number
  ram: number
  gpu: any
  gpu_load?: number
  temperature?: number
  network_rx?: number
  network_tx?: number
  unit_id: string
  org_id?: string
  comp_id?: string
  cpu_usage?: number
  ram_usage?: number
  gpu_usage?: number
}

export interface Unit {
  id: string
  name: string
  org_id?: string
  org_name?: string
  org_slug?: string
  comp_id?: string
  status: 'online' | 'offline' | 'warning' | 'pending'
  last_seen: string | null
  ip?: string
  alerts?: Alert[]
}

export interface Alert {
  id: string
  unit_id: string
  type: 'cpu' | 'ram' | 'gpu' | 'temperature' | 'network'
  message: string
  severity: 'low' | 'medium' | 'high'
  timestamp: string
  acknowledged: boolean
}