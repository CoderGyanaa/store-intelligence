'use client'

import { useFunnel } from '../hooks/useApi'

export default function FunnelChart({ storeId }: { storeId: string }) {
  const { data, loading } = useFunnel(storeId)

  const stages = data?.funnel ?? [
    { stage: 'Entry', visitors: 0, drop_off_pct: 0 },
    { stage: 'Zone Visit', visitors: 0, drop_off_pct: 0 },
    { stage: 'Billing Queue', visitors: 0, drop_off_pct: 0 },
    { stage: 'Purchase', visitors: 0, drop_off_pct: 0 },
  ]

  const maxVisitors = stages[0]?.visitors || 1
  const colors = ['#1a4a8a', '#15407a', '#10366a', '#0a2a55']

  return (
    <div className="panel p-4 h-full">
      <div className="flex items-center justify-between mb-4">
        <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Conversion Funnel</div>
        {data?.overall_conversion_rate != null && (
          <div className="text-xs text-slate-400">
            Overall: <span className="text-brand-light font-medium">
              {(data.overall_conversion_rate * 100).toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-2.5">
        {stages.map((stage: any, i: number) => {
          const pct = maxVisitors > 0 ? Math.round((stage.visitors / maxVisitors) * 100) : 0
          return (
            <div key={stage.stage} className="flex items-center gap-3">
              <div className="text-xs text-slate-500 w-24 flex-shrink-0">{stage.stage}</div>
              <div className="flex-1 bg-dark-500 rounded h-6 overflow-hidden">
                <div
                  className="h-full rounded flex items-center px-2.5 transition-all duration-700"
                  style={{ width: `${Math.max(pct, 4)}%`, background: colors[i] }}
                >
                  <span className="text-xs font-medium text-slate-300">
                    {loading ? '…' : stage.visitors}
                  </span>
                </div>
              </div>
              {stage.drop_off_pct > 0 && (
                <div className="text-xs text-danger w-10 text-right flex-shrink-0">
                  -{stage.drop_off_pct}%
                </div>
              )}
            </div>
          )
        })}
      </div>

      {data?.reentry_events > 0 && (
        <div className="mt-3 text-xs text-slate-500 flex items-center gap-1.5">
          <span className="text-warning">↺</span>
          {data.reentry_events} re-entry events detected &amp; deduplicated
        </div>
      )}
    </div>
  )
}
