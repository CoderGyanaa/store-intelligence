'use client'

import { useMetrics } from '../hooks/useApi'

function Skeleton() {
  return <div className="h-8 w-20 bg-dark-500 rounded animate-pulse" />
}

function MetricCard({ label, value, delta, deltaUp, color, loading }: any) {
  return (
    <div className="metric-card">
      <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">{label}</div>
      {loading ? <Skeleton /> : (
        <div className={`text-2xl font-semibold ${color || 'text-slate-100'}`}>{value}</div>
      )}
      {delta && (
        <div className={`text-xs mt-1.5 ${deltaUp ? 'text-success' : 'text-danger'}`}>
          {deltaUp ? '↑' : '↓'} {delta}
        </div>
      )}
    </div>
  )
}

export default function MetricsRow({ storeId }: { storeId: string }) {
  const { data, loading } = useMetrics(storeId)

  const visitors = data?.unique_visitors ?? 0
  const convRate = data?.conversion_rate != null ? `${(data.conversion_rate * 100).toFixed(1)}%` : '—'
  const queueDepth = data?.queue_depth ?? 0
  const abandonment = data?.abandonment_rate != null ? `${(data.abandonment_rate * 100).toFixed(1)}%` : '—'

  const zones = data?.avg_dwell_per_zone ?? {}
  const dwellVals = Object.values(zones) as number[]
  const avgDwell = dwellVals.length
    ? `${(dwellVals.reduce((a, b) => a + b, 0) / dwellVals.length / 60).toFixed(1)} min`
    : '—'

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-5 gap-3 mb-4">
      <MetricCard label="Unique Visitors" value={visitors} delta="today" deltaUp={true} loading={loading} />
      <MetricCard
        label="Conversion Rate"
        value={convRate}
        delta={data?.data_confidence === 'LOW' ? 'low data' : undefined}
        deltaUp={false}
        loading={loading}
        color={data?.conversion_rate > 0.3 ? 'text-success' : 'text-warning'}
      />
      <MetricCard
        label="Avg Dwell"
        value={avgDwell}
        loading={loading}
      />
      <MetricCard
        label="Queue Depth"
        value={queueDepth}
        delta={queueDepth >= 5 ? 'above threshold' : 'normal'}
        deltaUp={queueDepth < 5}
        loading={loading}
        color={queueDepth >= 5 ? 'text-warning' : 'text-slate-100'}
      />
      <MetricCard
        label="Abandonment"
        value={abandonment}
        loading={loading}
        color={data?.abandonment_rate > 0.3 ? 'text-danger' : 'text-slate-100'}
      />
    </div>
  )
}
