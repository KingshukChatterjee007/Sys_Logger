'use client'

import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Alert } from './types'
import { AlertCircle, CheckCircle2, Info } from 'lucide-react'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

interface AlertsListProps {
  alerts: Alert[]
  onAcknowledge: (alertId: string) => void
}

export const AlertsList: React.FC<AlertsListProps> = ({ alerts, onAcknowledge }) => {
  const activeAlerts = alerts.filter(alert => !alert.acknowledged)

  if (activeAlerts.length === 0) {
    return (
      <div className="p-8 glass-panel-rich rounded-2xl flex flex-col items-center justify-center text-center border-dashed border-2 border-white/5">
        <CheckCircle2 className="w-10 h-10 text-emerald-500/30 mb-3" />
        <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Matrix Clear - No Active Alerts</p>
      </div>
    )
  }

  const getSeverityStyles = (severity: Alert['severity']) => {
    switch (severity) {
      case 'high': return {
        icon: <AlertCircle className="text-red-400" size={16} />,
        border: 'border-red-500/30',
        bg: 'bg-red-500/[0.03]',
        tag: 'bg-red-600 text-white'
      }
      case 'medium': return {
        icon: <AlertCircle className="text-amber-400" size={16} />,
        border: 'border-amber-500/30',
        bg: 'bg-amber-500/[0.03]',
        tag: 'bg-amber-600 text-white'
      }
      case 'low': return {
        icon: <Info className="text-blue-400" size={16} />,
        border: 'border-blue-500/30',
        bg: 'bg-blue-500/[0.03]',
        tag: 'bg-blue-600 text-white'
      }
      default: return {
        icon: <Info className="text-slate-400" size={16} />,
        border: 'border-slate-500/30',
        bg: 'bg-slate-500/[0.03]',
        tag: 'bg-slate-600 text-white'
      }
    }
  }

  return (
    <div className="space-y-3">
      <AnimatePresence mode='popLayout'>
        {activeAlerts.map((alert, idx) => {
          const styles = getSeverityStyles(alert.severity)
          return (
            <motion.div
              layout
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ delay: idx * 0.05 }}
              key={alert.id}
              className={cn(
                "p-4 rounded-xl border glass-panel-rich relative overflow-hidden group transition-all hover:bg-white/[0.02]",
                styles.border,
                styles.bg
              )}
            >
              <div className="flex items-start justify-between relative z-10">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <div className={cn("px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-widest", styles.tag)}>
                      {alert.severity}
                    </div>
                    <span className="text-[9px] text-slate-500 font-bold uppercase tracking-[0.1em]">{alert.type}</span>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5">{styles.icon}</div>
                    <div>
                      <p className="text-xs font-bold text-white/90 leading-relaxed italic">{alert.message}</p>
                      <p className="text-[9px] text-slate-500 font-bold uppercase tracking-tighter mt-1.5 opacity-60">
                        {new Date(alert.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => onAcknowledge(alert.id)}
                  className="ml-4 px-3 py-1.5 bg-white/5 hover:bg-white/10 text-[9px] font-black uppercase tracking-widest text-slate-400 hover:text-white rounded-lg transition-all border border-white/5 group-hover:border-white/10"
                >
                  Clear
                </button>
              </div>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}