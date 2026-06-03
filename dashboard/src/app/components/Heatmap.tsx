'use client'

import { useHeatmap } from '../hooks/useApi'

function HeatCell({ zone }: { zone: any }) {
  const score = zone.heat_score ?? 0
  const opacity = 0.15 + (score / 100) * 0.75
  const bg = `rgba(58,127,213,${opacity})`
  const textColor = score > 60 ? '#a0d4ff' : score > 30 ? '#6aabff' : '#3a6fa5'

  return (
    <div
      className="rounded-lg p-3 text-center transition-all duration-500 cursor-default"
      style={{ background: bg }}
      title={`${zone.zone_id}: ${zone.visit_count} visits, ${zone.avg_dwell_seconds}s avg dwell`}
    >
      <div className="text-xs text-slate-400 mb-1 truncate">{zone.zone_id}</div>
      <div className="text-xl font-semibold" style={{ color: textColor }}>{score}</div>
      <div className="text-xs text-slate-500 mt-1">{zone.avg_dwell_seconds}s dwell</div>
      {zone.data_confidence === 'LOW' && (
        <div className="text-xs text-warning mt-1">low data</div>
      )}
    </div>
  )
}

export default function Heatmap({ storeId }: { storeId: string }) {
  const { data, loading } = useHeatmap(storeId)
  const zones = data?.zones ?? []

  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Zone Heatmap</div>
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span>score 0–100</span>
          {data?.data_confidence && (
            <span className={`px-2 py-0.5 rounded-full text-xs ${
              data.data_confidence === 'HIGH' ? 'bg-green-900 text-green-300' :
              data.data_confidence === 'MEDIUM' ? 'bg-yellow-900 text-yellow-300' :
              'bg-slate-800 text-slate-400'
            }`}>
              {data.data_confidence}
            </span>
          )}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-5 gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-20 bg-dark-500 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : zones.length === 0 ? (
        <div className="text-center text-slate-500 text-sm py-8">
          No zone data yet — run the detection pipeline first
        </div>
      ) : (
        <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
          {zones.map((z: any) => <HeatCell key={z.zone_id} zone={z} />)}
        </div>
      )}
    </div>
  )
}
