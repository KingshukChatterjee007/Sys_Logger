'use client'

import React, { useEffect, useState, useMemo } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { motion } from 'framer-motion'
import { Cpu, Layers, Zap, Network } from 'lucide-react'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const generateInitialData = (length = 20) => {
  return Array.from({ length }, (_, i) => ({
    x: i,
    y: 30 + Math.random() * 40
  }))
}

const ChartCard = ({ title, label, icon, color, data, unit = "%" }: { title: string, label: string, icon: any, color: string, data: any[], unit?: string }) => {
  const chartData = {
    labels: data.map(d => d.x),
    datasets: [
      {
        data: data.map(d => d.y),
        borderColor: color,
        backgroundColor: `${color}20`,
        fill: true,
        tension: 0,
        pointRadius: 0,
        borderWidth: 2,
      }
    ]
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 200, easing: 'easeOutQuart' as const },
    plugins: {
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: { display: false },
      y: { 
        display: false,
        min: 0,
        max: unit === "%" ? 100 : undefined
      },
    },
  }

  return (
    <div className="bg-white/50 backdrop-blur-sm ring-1 ring-zinc-200/50 rounded-2xl p-4 flex flex-col gap-3 h-32">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className={`p-1.5 rounded-lg bg-white ring-1 ring-zinc-200/50 shadow-sm`} style={{ color }}>
            {icon}
          </div>
          <div className="flex flex-col">
            <span className="text-[9px] font-black uppercase tracking-widest text-zinc-500">{title}</span>
            <span className="text-[7px] font-bold text-zinc-300 uppercase tracking-widest leading-none">{label}</span>
          </div>
        </div>
        <span className="text-[10px] font-mono font-bold text-zinc-400">
          {data[data.length - 1]?.y.toFixed(unit === "MB/s" ? 3 : 1)}{unit}
        </span>
      </div>
      <div className="flex-1 min-h-0">
        <Line data={chartData} options={options} />
      </div>
    </div>
  )
}

export default function MockFleetGraphs() {
  const [cpuData, setCpuData] = useState(generateInitialData())
  const [ramData, setRamData] = useState(generateInitialData())
  const [gpuData, setGpuData] = useState(generateInitialData())
  const [netData, setNetData] = useState(generateInitialData())

  useEffect(() => {
    const updateData = (prev: any[]) => {
      const lastValue = prev[prev.length - 1].y
      // Increased variance and added occasional "spikes" for more abrupt motion
      const variance = (Math.random() - 0.5) * 45
      const spike = Math.random() > 0.8 ? (Math.random() - 0.5) * 60 : 0
      const newValue = Math.max(5, Math.min(95, lastValue + variance + spike))
      const newData = [...prev.slice(1), { x: prev[prev.length - 1].x + 1, y: newValue }]
      return newData
    }

    const interval = setInterval(() => {
      setCpuData(updateData)
      setRamData(updateData)
      setGpuData(updateData)
      setNetData(updateData)
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full h-full p-6">
      <ChartCard title="PROCESSING" label="CPU LOAD" icon={<Cpu size={12} />} color="#f97316" data={cpuData} />
      <ChartCard title="MEMORY" label="RAM UTIL" icon={<Layers size={12} />} color="#10b981" data={ramData} />
      <ChartCard title="GRAPHICS" label="GPU COMPUTE" icon={<Zap size={12} />} color="#3b82f6" data={gpuData} />
      <ChartCard title="NETWORK" label="RX RATE" icon={<Network size={12} />} color="#8b5cf6" data={netData} unit="MB/s" />
    </div>
  )
}
