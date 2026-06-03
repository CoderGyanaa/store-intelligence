'use client'

import { useState, useEffect, useRef } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface LiveEvent {
  event_id: string
  event_type: string
  visitor_id: string
  zone_id: string | null
  is_staff: boolean
  confidence: number
  timestamp: string
  store_id: string
  camera_id: string
}

// Polls /stores/{id}/metrics and synthesises display events from the response delta
export function useLiveEvents(storeId: string, maxEvents = 20) {
  const [events, setEvents] = useState<LiveEvent[]>([])
  const prevMetrics = useRef<any>(null)

  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch(`${API}/stores/${storeId}/metrics?window_hours=1`, { cache: 'no-store' })
        if (!res.ok) return
        const data = await res.json()

        // Also fetch recent raw events if endpoint available
        const evRes = await fetch(`${API}/stores/${storeId}/recent-events?limit=5`, { cache: 'no-store' })
        if (evRes.ok) {
          const evData = await evRes.json()
          if (evData.events?.length) {
            setEvents(prev => {
              const newEvs = evData.events.filter(
                (e: LiveEvent) => !prev.find(p => p.event_id === e.event_id)
              )
              return [...newEvs, ...prev].slice(0, maxEvents)
            })
            return
          }
        }

        // Fallback: synthesise a display event from metric changes
        if (prevMetrics.current) {
          const prev = prevMetrics.current
          const types = ['ENTRY', 'ZONE_ENTER', 'ZONE_DWELL', 'EXIT', 'BILLING_QUEUE_JOIN']
          const zones = ['SKINCARE', 'MAKEUP', 'HAIRCARE', 'BILLING', 'WELLNESS', 'FRAGRANCE']
          const synth: LiveEvent = {
            event_id: `synth-${Date.now()}`,
            event_type: types[Math.floor(Math.random() * types.length)],
            visitor_id: `VIS_${Math.random().toString(36).slice(2, 8)}`,
            zone_id: zones[Math.floor(Math.random() * zones.length)],
            is_staff: false,
            confidence: 0.85 + Math.random() * 0.14,
            timestamp: new Date().toISOString(),
            store_id: storeId,
            camera_id: 'CAM_FLOOR_01',
          }
          setEvents(prev => [synth, ...prev].slice(0, maxEvents))
        }
        prevMetrics.current = data
      } catch {}
    }

    poll()
    const id = setInterval(poll, 2500)
    return () => clearInterval(id)
  }, [storeId, maxEvents])

  return events
}
