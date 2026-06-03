'use client'

import { useState } from 'react'
import Sidebar from './components/Sidebar'
import MetricsRow from './components/MetricsRow'
import TrafficChart from './components/TrafficChart'
import FunnelChart from './components/FunnelChart'
import Heatmap from './components/Heatmap'
import AnomalyPanel from './components/AnomalyPanel'
import EventStream from './components/EventStream'
import InsightsPanel from './components/InsightsPanel'

export default function Dashboard() {
  const [storeId, setStoreId] = useState('STORE_BLR_002')
  const [activeTab, setActiveTab] = useState('overview')

  return (
    <div className="flex h-screen bg-dark-900 overflow-hidden">
      <Sidebar
        selectedStore={storeId}
        onStoreChange={setStoreId}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="flex items-center justify-between px-6 py-3.5 border-b border-dark-400 bg-dark-800 flex-shrink-0">
          <div>
            <h1 className="text-sm font-semibold text-slate-200 capitalize">{activeTab} — {storeId}</h1>
            <p className="text-xs text-slate-500 mt-0.5">Store Intelligence Platform</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs text-success bg-green-950 border border-green-900 px-3 py-1.5 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse-slow" />
              Real-time
            </div>
            <div className="text-xs text-slate-500" suppressHydrationWarning>
              {new Date().toLocaleTimeString()} IST
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          {/* Always show metrics row */}
          <MetricsRow storeId={storeId} />

          {activeTab === 'overview' && (
            <div className="flex flex-col gap-4">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <TrafficChart storeId={storeId} />
                <FunnelChart storeId={storeId} />
              </div>
              <Heatmap storeId={storeId} />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <AnomalyPanel storeId={storeId} />
                <EventStream storeId={storeId} />
              </div>
              <InsightsPanel storeId={storeId} />
            </div>
          )}

          {activeTab === 'traffic' && (
            <div className="flex flex-col gap-4">
              <div className="h-80"><TrafficChart storeId={storeId} /></div>
              <InsightsPanel storeId={storeId} />
            </div>
          )}

          {activeTab === 'heatmap' && <Heatmap storeId={storeId} />}

          {activeTab === 'funnel' && (
            <div className="max-w-2xl">
              <FunnelChart storeId={storeId} />
            </div>
          )}

          {activeTab === 'anomalies' && (
            <div className="max-w-2xl">
              <AnomalyPanel storeId={storeId} />
            </div>
          )}

          {activeTab === 'events' && (
            <div className="h-[500px]">
              <EventStream storeId={storeId} />
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
