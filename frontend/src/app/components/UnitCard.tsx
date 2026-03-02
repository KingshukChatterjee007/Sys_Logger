'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { Unit } from './types'
import { Monitor, Clock } from 'lucide-react'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

interface UnitCardProps {
  unit: Unit
  onClick: (unitId: string) => void
}

export const UnitCard: React.FC<UnitCardProps> = ({ unit, onClick }) => {
  const getStatusColor = (status: Unit['status']) => {
    switch (status) {
      case 'online': return 'bg-emerald-500'
      case 'offline': return 'bg-slate-600'
      case 'warning': return 'bg-amber-500'
      default: return 'bg-slate-500'
    }
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
    <motion.div
      whileHover={{ y: -2, scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className="glass-panel-rich p-4 rounded-xl cursor-pointer hover:border-blue-500/30 group transition-all"
      onClick={() => onClick(unit.id)}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white/5 rounded-lg text-slate-400 group-hover:text-blue-400 transition-colors">
            <Monitor size={18} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white group-hover:text-blue-100 transition-colors tracking-tight italic uppercase">
              {unit.name}
            </h3>
            <div className="flex items-center gap-1.5 text-[9px] text-slate-500 font-bold uppercase tracking-widest mt-0.5">
              <Clock size={10} /> {getTimeAgo(unit.last_seen)}
            </div>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className={cn("w-2 h-2 rounded-full", getStatusColor(unit.status), unit.status === 'online' && "shadow-[0_0_8px_rgba(16,185,129,0.5)]")} />
          <span className="text-[8px] font-black text-slate-600 uppercase tracking-tighter">{unit.status}</span>
        </div>
      </div>

      <div className="flex gap-2">
        <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
          <div className={cn("h-full", unit.status === 'online' ? "bg-emerald-500/40" : "bg-slate-700")} style={{ width: unit.status === 'online' ? '100%' : '0%' }} />
        </div>
      </div>

      {unit.alerts && unit.alerts.length > 0 && (
        <div className="mt-3 pt-3 border-t border-white/5">
          <span className="text-[9px] font-black text-red-500 uppercase tracking-[0.2em] flex items-center gap-1.5 animate-pulse">
            <div className="w-1 h-1 rounded-full bg-red-500" />
            {unit.alerts.length} Critical Alert{unit.alerts.length > 1 ? 's' : ''}
          </span>
        </div>
      )}
    </motion.div>
  )
}