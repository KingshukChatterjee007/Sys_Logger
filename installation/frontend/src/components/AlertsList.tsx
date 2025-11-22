import React from 'react'
import { Alert } from './types'

interface AlertsListProps {
  alerts: Alert[]
  onAcknowledge: (alertId: string) => void
}

export const AlertsList: React.FC<AlertsListProps> = ({ alerts, onAcknowledge }) => {
  const activeAlerts = alerts.filter(alert => !alert.acknowledged)

  if (activeAlerts.length === 0) {
    return (
      <div className="p-4 bg-slate-800 rounded-lg">
        <p className="text-slate-400 text-center">No active alerts</p>
      </div>
    )
  }

  const getSeverityColor = (severity: Alert['severity']) => {
    switch (severity) {
      case 'high': return 'border-red-500 bg-red-900/20'
      case 'medium': return 'border-yellow-500 bg-yellow-900/20'
      case 'low': return 'border-blue-500 bg-blue-900/20'
      default: return 'border-gray-500 bg-gray-900/20'
    }
  }

  return (
    <div className="space-y-2">
      {activeAlerts.map(alert => (
        <div
          key={alert.id}
          className={`p-3 rounded-lg border-l-4 ${getSeverityColor(alert.severity)} bg-slate-800`}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-xs px-2 py-1 rounded uppercase font-semibold ${
                  alert.severity === 'high' ? 'bg-red-600 text-white' :
                  alert.severity === 'medium' ? 'bg-yellow-600 text-white' :
                  'bg-blue-600 text-white'
                }`}>
                  {alert.severity}
                </span>
                <span className="text-xs text-slate-400 uppercase">{alert.type}</span>
              </div>
              <p className="text-sm text-white">{alert.message}</p>
              <p className="text-xs text-slate-400 mt-1">
                {new Date(alert.timestamp).toLocaleString()}
              </p>
            </div>
            <button
              onClick={() => onAcknowledge(alert.id)}
              className="ml-3 px-3 py-1 bg-slate-700 hover:bg-slate-600 text-xs rounded transition-colors"
            >
              Acknowledge
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}