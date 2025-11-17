interface UsageData {
  timestamp: string
  cpu: number
  ram: number
  gpu: string
  gpu_load?: number
}

export type { UsageData }