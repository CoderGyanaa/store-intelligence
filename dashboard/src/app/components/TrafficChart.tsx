'use client'

import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { useMetrics } from '../hooks/useApi'

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-dark-600 border border-dark-300 rounded-lg px-3 py-2 text-xs">
      <div className="text-slate-400 mb-1">{label}</div>
      <div className="text-brand-light font-medium">{payload[0]?.value} visitors</div>
    </div>
  )
}

export default function TrafficChart({ storeId }: { storeId: string }) {
  const { data, lastUpdated } = useMetrics(storeId)
  const [history, setHistory] = useState<{ time: string; visitors: number }[]>([])

  useEffect(() => {
    if (data?.unique_visitors == null) return
    const now = new Date()
    const label = `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`
    setHistory(prev => {
      const next = [...prev, { time: label, visitors: data.unique_visitors }]
      return next.slice(-20)
    })
  }, [lastUpdated])

  // Seed with initial data if empty
  const chartData = history.length > 0 ? history : [
    { time: '10:00', visitors: 0 },
    { time: 'now', visitors: data?.unique_visitors ?? 0 },
  ]

  return (
    <div className="panel p-4 h-full">
      <div className="flex items-center justify-between mb-4">
        <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Live Traffic</div>
        <div className="flex items-center gap-1.5 text-xs text-success">
          <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse-slow" />
          updating every 4s
        </div>
      </div>
      <ResponsiveContainer width="100%" height={160}>
        <AreaChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <defs>
            <linearGradient id="trafficGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3a7fd5" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3a7fd5" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2230" />
          <XAxis dataKey="time" tick={{ fill: '#4a6fa5', fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#4a6fa5', fontSize: 10 }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Area type="monotone" dataKey="visitors" stroke="#3a7fd5" strokeWidth={2} fill="url(#trafficGrad)" dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
