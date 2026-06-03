'use client'

import { useState, useEffect, useCallback } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function useApi<T>(endpoint: string, intervalMs = 5000) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetch_ = useCallback(async () => {
    try {
      const res = await fetch(`${API}${endpoint}`, { cache: 'no-store' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      setData(json)
      setError(null)
      setLastUpdated(new Date())
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [endpoint])

  useEffect(() => {
    fetch_()
    const id = setInterval(fetch_, intervalMs)
    return () => clearInterval(id)
  }, [fetch_, intervalMs])

  return { data, loading, error, lastUpdated, refetch: fetch_ }
}

export function useMetrics(storeId: string) {
  return useApi<any>(`/stores/${storeId}/metrics`, 4000)
}

export function useFunnel(storeId: string) {
  return useApi<any>(`/stores/${storeId}/funnel`, 6000)
}

export function useHeatmap(storeId: string) {
  return useApi<any>(`/stores/${storeId}/heatmap`, 8000)
}

export function useAnomalies(storeId: string) {
  return useApi<any>(`/stores/${storeId}/anomalies`, 5000)
}

export function useHealth() {
  return useApi<any>(`/health`, 10000)
}
