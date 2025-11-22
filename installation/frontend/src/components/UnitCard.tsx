import React from 'react'
import { Unit } from './types'

interface UnitCardProps {
  unit: Unit
  onClick: (unitId: string) => void
}

export const UnitCard: React.FC<UnitCardProps> = ({ unit, onClick }) => {
  const getStatusColor = (status: Unit['status']) => {
    switch (status) {
      case 'online': return 'bg-green-500'
      case 'offline': return 'bg-red-500'
      case 'warning': return 'bg-yellow-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusText = (status: Unit['status']) => {
    return status.charAt(0).toUpperCase() + status.slice(1)
  }

  const getTimeAgo = (timestamp: string) => {
    const now = new Date()
    const lastSeen = new Date(timestamp)
    const diffMs = now.getTime() - lastSeen.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`

    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`

    const diffDays = Math.floor(diffHours / 24)
    return `${diffDays}d ago`
  }

  return (
    <div
      className="p-4 bg-slate-800 rounded-lg hover:bg-slate-700 cursor-pointer transition-colors"
      onClick={() => onClick(unit.id)}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-white">{unit.name}</h3>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${getStatusColor(unit.status)}`} />
          <span className={`text-xs px-2 py-1 rounded ${
            unit.status === 'online' ? 'bg-green-900 text-green-200' :
            unit.status === 'offline' ? 'bg-red-900 text-red-200' :
            'bg-yellow-900 text-yellow-200'
          }`}>
            {getStatusText(unit.status)}
          </span>
        </div>
      </div>

      <div className="text-xs text-slate-400">
        Last seen: {getTimeAgo(unit.last_seen)}
      </div>

      {unit.alerts && unit.alerts.length > 0 && (
        <div className="mt-2">
          <span className="text-xs text-red-400">
            {unit.alerts.length} active alert{unit.alerts.length > 1 ? 's' : ''}
          </span>
        </div>
      )}
    </div>
  )
}