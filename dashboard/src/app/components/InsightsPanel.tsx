'use client'

import { useMetrics, useFunnel, useAnomalies, useHeatmap } from '../hooks/useApi'

function generateInsights(metrics: any, funnel: any, anomalies: any, heatmap: any): string[] {
  const insights: string[] = []

  if (metrics?.queue_depth >= 5)
    insights.push(`⚠ Checkout queue has ${metrics.queue_depth} customers waiting — peak congestion detected.`)

  if (funnel?.funnel) {
    const billing = funnel.funnel.find((s: any) => s.stage === 'Billing Queue')
    if (billing?.drop_off_pct > 30)
      insights.push(`${billing.drop_off_pct}% of zone visitors never reached the billing counter — review product placement.`)
  }

  if (heatmap?.zones?.length) {
    const top = heatmap.zones[0]
    const bottom = heatmap.zones[heatmap.zones.length - 1]
    if (top) insights.push(`🔥 ${top.zone_id} is the highest-traffic zone (score ${top.heat_score}) — prime upsell location.`)
    if (bottom && bottom.heat_score < 30)
      insights.push(`📉 ${bottom.zone_id} has very low engagement (score ${bottom.heat_score}) — consider repositioning display.`)
  }

  if (metrics?.conversion_rate != null) {
    const cr = (metrics.conversion_rate * 100).toFixed(1)
    if (metrics.conversion_rate > 0.35)
      insights.push(`✅ Conversion rate ${cr}% is above benchmark — store performance is strong.`)
    else if (metrics.conversion_rate < 0.2)
      insights.push(`📊 Conversion rate ${cr}% is below 20% — investigate drop-off at zone visit stage.`)
  }

  if (anomalies?.anomalies?.length === 0)
    insights.push('✅ No active anomalies — store is operating within normal parameters.')

  if (insights.length === 0)
    insights.push('📊 Collecting data... insights will appear once events are ingested.')

  return insights
}

const INSIGHT_STYLE = (text: string) => {
  if (text.startsWith('⚠') || text.startsWith('📉')) return 'border-l-warning text-warning'
  if (text.startsWith('✅')) return 'border-l-success text-success'
  if (text.startsWith('🔥')) return 'border-l-brand text-brand-light'
  return 'border-l-brand-dark text-slate-400'
}

export default function InsightsPanel({ storeId }: { storeId: string }) {
  const { data: metrics } = useMetrics(storeId)
  const { data: funnel } = useFunnel(storeId)
  const { data: anomalies } = useAnomalies(storeId)
  const { data: heatmap } = useHeatmap(storeId)

  const insights = generateInsights(metrics, funnel, anomalies, heatmap)

  return (
    <div className="panel p-4">
      <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">
        AI Business Insights
      </div>
      <div className="flex flex-col gap-2">
        {insights.map((ins, i) => (
          <div
            key={i}
            className={`text-xs px-3 py-2.5 border-l-2 bg-dark-600 rounded-r-lg leading-relaxed ${INSIGHT_STYLE(ins)}`}
          >
            {ins}
          </div>
        ))}
      </div>
    </div>
  )
}
