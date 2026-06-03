'use client'

import { useLiveEvents } from '../hooks/useLiveEvents'

const EVENT_COLORS: Record<string, string> = {
  ENTRY:               'bg-success',
  EXIT:                'bg-danger',
  ZONE_ENTER:          'bg-brand',
  ZONE_EXIT:           'bg-slate-500',
  ZONE_DWELL:          'bg-purple-400',
  BILLING_QUEUE_JOIN:  'bg-warning',
  BILLING_QUEUE_ABANDON: 'bg-orange-400',
  REENTRY:             'bg-orange-300',
}

const EVENT_TEXT: Record<string, string> = {
  ENTRY:               'text-success',
  EXIT:                'text-danger',
  ZONE_ENTER:          'text-brand-light',
  ZONE_EXIT:           'text-slate-400',
  ZONE_DWELL:          'text-purple-300',
  BILLING_QUEUE_JOIN:  'text-warning',
  BILLING_QUEUE_ABANDON: 'text-orange-300',
  REENTRY:             'text-orange-200',
}

export default function EventStream({ storeId }: { storeId: string }) {
  const events = useLiveEvents(storeId, 15)

  return (
    <div className="panel p-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Live Event Stream</div>
        <div className="flex items-center gap-1.5 text-xs text-success">
          <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse-slow" />
          live
        </div>
      </div>

      <div className="flex flex-col gap-1 overflow-y-auto flex-1 font-mono">
        {events.length === 0 ? (
          <div className="text-slate-500 text-xs py-4 text-center">Waiting for events…</div>
        ) : (
          events.map((ev) => (
            <div
              key={ev.event_id}
              className="flex items-center gap-2 py-1 px-2 rounded hover:bg-dark-500 transition-colors animate-slide-in"
            >
              <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${EVENT_COLORS[ev.event_type] ?? 'bg-slate-500'}`} />
              <span className={`text-xs w-36 flex-shrink-0 font-medium ${EVENT_TEXT[ev.event_type] ?? 'text-slate-300'}`}>
                {ev.event_type}
              </span>
              <span className="text-xs text-slate-500 w-20 flex-shrink-0 truncate">{ev.visitor_id}</span>
              <span className="text-xs text-brand-light truncate flex-1">{ev.zone_id ?? ''}</span>
              <span className="text-xs text-slate-600 flex-shrink-0">
                {new Date(ev.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
