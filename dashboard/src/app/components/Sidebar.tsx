'use client'

import { useState } from 'react'
import { useHealth } from '../hooks/useApi'

const STORES = [
  { id: 'STORE_BLR_002', name: 'Koramangala', city: 'Bangalore' },
  { id: 'STORE_BLR_004', name: 'Indiranagar', city: 'Bangalore' },
  { id: 'STORE_MUM_001', name: 'Bandra', city: 'Mumbai' },
  { id: 'STORE_DEL_003', name: 'Connaught Place', city: 'Delhi' },
  { id: 'STORE_HYD_002', name: 'Banjara Hills', city: 'Hyderabad' },
]

const NAV = [
  { id: 'overview', label: 'Overview', icon: '⬡' },
  { id: 'traffic', label: 'Traffic', icon: '↑↓' },
  { id: 'heatmap', label: 'Heatmap', icon: '◈' },
  { id: 'funnel', label: 'Funnel', icon: '▽' },
  { id: 'anomalies', label: 'Anomalies', icon: '⚡' },
  { id: 'events', label: 'Event Stream', icon: '≋' },
]

interface Props {
  selectedStore: string
  onStoreChange: (id: string) => void
  activeTab: string
  onTabChange: (id: string) => void
}

export default function Sidebar({ selectedStore, onStoreChange, activeTab, onTabChange }: Props) {
  const { data: health } = useHealth()
  const apiOk = health?.status === 'ok' || health?.status === 'degraded'

  return (
    <aside className="w-56 bg-dark-700 border-r border-dark-400 flex flex-col flex-shrink-0">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-dark-400">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-dark to-brand flex items-center justify-center text-white text-sm font-bold">
            S
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-100 tracking-tight">StoreMind AI</div>
            <div className="text-xs text-slate-500">Store Intelligence</div>
          </div>
        </div>
      </div>

      {/* Store selector */}
      <div className="px-3 py-3 border-b border-dark-400">
        <div className="text-xs text-slate-500 uppercase tracking-wider mb-2 px-1">Store</div>
        <select
          value={selectedStore}
          onChange={e => onStoreChange(e.target.value)}
          className="w-full bg-dark-500 border border-dark-300 text-slate-300 text-xs rounded-lg px-3 py-2 cursor-pointer focus:outline-none focus:border-brand"
        >
          {STORES.map(s => (
            <option key={s.id} value={s.id}>{s.name} — {s.city}</option>
          ))}
        </select>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-3">
        <div className="text-xs text-slate-500 uppercase tracking-wider mb-2 px-2">Navigation</div>
        {NAV.map(item => (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm mb-0.5 transition-all ${
              activeTab === item.id
                ? 'bg-brand-dark text-brand-light font-medium'
                : 'text-slate-400 hover:bg-dark-500 hover:text-slate-300'
            }`}
          >
            <span className="text-base leading-none w-4 text-center">{item.icon}</span>
            {item.label}
            {item.id === 'anomalies' && (
              <span className="ml-auto bg-red-900 text-red-300 text-xs px-1.5 py-0.5 rounded-full">!</span>
            )}
            {item.id === 'overview' && (
              <span className="ml-auto flex items-center gap-1 text-success text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse-slow" />
                live
              </span>
            )}
          </button>
        ))}
      </nav>

      {/* API Status */}
      <div className="px-4 py-3 border-t border-dark-400">
        <div className="text-xs text-slate-500 mb-1.5">API STATUS</div>
        <div className={`flex items-center gap-2 text-xs ${apiOk ? 'text-success' : 'text-danger'}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${apiOk ? 'bg-success animate-pulse-slow' : 'bg-danger'}`} />
          {health ? (apiOk ? 'All systems OK' : 'Degraded') : 'Connecting...'}
        </div>
        {health?.total_events_ingested != null && (
          <div className="text-xs text-slate-500 mt-1">
            {health.total_events_ingested.toLocaleString()} events ingested
          </div>
        )}
      </div>
    </aside>
  )
}
