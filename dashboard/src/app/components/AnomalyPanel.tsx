'use client'

import { useAnomalies } from '../hooks/useApi'

const SEV_STYLES: Record<string, string> = {
  CRITICAL: 'bg-red-950 border-red-900 text-red-200',
  WARN:     'bg-yellow-950 border-yellow-900 text-yellow-200',
  INFO:     'bg-blue-950 border-blue-900 text-blue-200',
}

const SEV_BADGE: Record<string, string> = {
  CRITICAL: 'bg-red-900 text-red-300',
  WARN:     'bg-yellow-900 text-yellow-300',
  INFO:     'bg-blue-900 text-blue-300',
}

export default function AnomalyPanel({ storeId }: { storeId: string }) {
  const { data, loading, lastUpdated } = useAnomalies(storeId)
  const anomalies = data?.anomalies ?? []

  return (
    <div className="panel p-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">
          Active Anomalies
        </div>
        <div className="flex items-center gap-2">
          {anomalies.length > 0 && (
            <span className="bg-red-900 text-red-300 text-xs px-2 py-0.5 rounded-full">
              {anomalies.length}
            </span>
          )}
          {lastUpdated && (
            <span className="text-xs text-slate-600">
              {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-2 flex-1 overflow-y-auto">
        {loading ? (
          Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="h-16 bg-dark-500 rounded-lg animate-pulse" />
          ))
        ) : anomalies.length === 0 ? (
          <div className="flex items-center gap-2 text-success text-sm py-4">
            <span className="w-2 h-2 rounded-full bg-success" />
            No anomalies detected
          </div>
        ) : (
          anomalies.map((a: any) => (
            <div
              key={a.anomaly_id}
              className={`border rounded-lg p-3 ${SEV_STYLES[a.severity] || SEV_STYLES.INFO}`}
            >
              <div className="flex items-start gap-2 mb-1">
                <span className={`text-xs px-2 py-0.5 rounded font-medium flex-shrink-0 ${SEV_BADGE[a.severity]}`}>
                  {a.severity}
                </span>
                <div className="text-xs font-medium leading-snug">{a.title}</div>
              </div>
              <div className="text-xs opacity-70 ml-0 leading-relaxed">{a.description}</div>
              {a.suggested_action && (
                <div className="text-xs text-brand-light mt-1.5 flex items-start gap-1">
                  <span className="flex-shrink-0">→</span>
                  {a.suggested_action}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
