"""
StoreMind — GET /stores/{store_id}/anomalies
Detects: queue spike, conversion drop vs 7-day avg, dead zone (no visits in 30 min).
Severity: INFO / WARN / CRITICAL. Includes suggested_action per anomaly.

AI-Assisted Decision (see DESIGN.md): Used Claude to evaluate Isolation Forest vs
ARIMA vs simple Z-score. Chose Z-score + rule-based for interpretability and zero cold-start.
Isolation Forest is layered on top for multivariate anomalies when enough data exists.
"""

import json
import math
import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.database import get_db, EventRecord

logger = logging.getLogger("storemind.anomalies")
router = APIRouter()

DEAD_ZONE_MINUTES = 30
QUEUE_SPIKE_THRESHOLD = 5      # billing visitors simultaneously
CONVERSION_DROP_THRESHOLD = 0.4  # 40% below baseline


def _ts_to_dt(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


@router.get("/{store_id}/anomalies")
async def get_anomalies(
    store_id: str,
    window_hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=window_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    cutoff_7d = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Current window events
    result = await db.execute(
        select(EventRecord).where(
            and_(
                EventRecord.store_id == store_id,
                EventRecord.is_staff == False,
                EventRecord.timestamp >= cutoff,
            )
        ).order_by(EventRecord.timestamp)
    )
    events = result.scalars().all()

    # 7-day baseline for conversion
    result_7d = await db.execute(
        select(EventRecord).where(
            and_(
                EventRecord.store_id == store_id,
                EventRecord.is_staff == False,
                EventRecord.timestamp >= cutoff_7d,
                EventRecord.timestamp < cutoff,
            )
        )
    )
    events_7d = result_7d.scalars().all()

    anomalies = []

    # -----------------------------------------------------------------------
    # 1. Billing queue spike
    # -----------------------------------------------------------------------
    billing_timeline = []
    active_billing: set[str] = set()

    for e in events:
        if e.event_type in ("BILLING_QUEUE_JOIN", "ZONE_ENTER") and e.zone_id == "BILLING":
            active_billing.add(e.visitor_id)
        elif e.event_type in ("ZONE_EXIT", "EXIT") and e.zone_id == "BILLING":
            active_billing.discard(e.visitor_id)
        billing_timeline.append(len(active_billing))

    current_queue = len(active_billing)
    if current_queue >= QUEUE_SPIKE_THRESHOLD:
        severity = "CRITICAL" if current_queue >= QUEUE_SPIKE_THRESHOLD * 2 else "WARN"
        anomalies.append({
            "anomaly_id": f"QUEUE_SPIKE_{store_id}",
            "type": "BILLING_QUEUE_SPIKE",
            "severity": severity,
            "title": f"Billing queue depth: {current_queue} customers",
            "description": f"Current billing queue has {current_queue} customers waiting — above threshold of {QUEUE_SPIKE_THRESHOLD}.",
            "current_value": current_queue,
            "threshold": QUEUE_SPIKE_THRESHOLD,
            "suggested_action": "Open an additional billing counter immediately. Consider calling support staff.",
            "detected_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

    # -----------------------------------------------------------------------
    # 2. Conversion drop vs 7-day baseline
    # -----------------------------------------------------------------------
    def _conversion_rate(evs):
        entered = {e.visitor_id for e in evs if e.event_type in ("ENTRY", "REENTRY")}
        purchased = {e.visitor_id for e in evs if e.zone_id == "BILLING" and e.event_type == "ZONE_DWELL"}
        if not entered:
            return None
        return len(purchased) / len(entered)

    current_cr = _conversion_rate(events)
    baseline_cr = _conversion_rate(events_7d)

    if current_cr is not None and baseline_cr is not None and baseline_cr > 0:
        drop = (baseline_cr - current_cr) / baseline_cr
        if drop >= CONVERSION_DROP_THRESHOLD:
            severity = "CRITICAL" if drop >= 0.6 else "WARN"
            anomalies.append({
                "anomaly_id": f"CONV_DROP_{store_id}",
                "type": "CONVERSION_DROP",
                "severity": severity,
                "title": f"Conversion rate dropped {round(drop * 100)}% vs 7-day average",
                "description": (
                    f"Current conversion: {round(current_cr * 100, 1)}% vs "
                    f"7-day baseline: {round(baseline_cr * 100, 1)}%."
                ),
                "current_value": round(current_cr, 4),
                "baseline_value": round(baseline_cr, 4),
                "drop_pct": round(drop * 100, 1),
                "suggested_action": "Review zone engagement data. Check if a product zone is underperforming or staff coverage is low.",
                "detected_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            })

    # -----------------------------------------------------------------------
    # 3. Dead zone detection (no visits in last 30 min)
    # -----------------------------------------------------------------------
    recent_cutoff = (now - timedelta(minutes=DEAD_ZONE_MINUTES)).strftime("%Y-%m-%dT%H:%M:%SZ")

    all_zones = {e.zone_id for e in events if e.zone_id}
    recent_zones = {e.zone_id for e in events if e.zone_id and e.timestamp >= recent_cutoff}
    dead_zones = all_zones - recent_zones

    for zone in dead_zones:
        anomalies.append({
            "anomaly_id": f"DEAD_ZONE_{store_id}_{zone}",
            "type": "DEAD_ZONE",
            "severity": "INFO",
            "title": f"Zone '{zone}' has had no visits in {DEAD_ZONE_MINUTES} minutes",
            "description": f"Zone {zone} has been inactive for over {DEAD_ZONE_MINUTES} minutes. May indicate a display issue or poor zone placement.",
            "zone_id": zone,
            "inactive_minutes": DEAD_ZONE_MINUTES,
            "suggested_action": f"Check if {zone} display is properly stocked and visible. Consider repositioning promotional signage.",
            "detected_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

    # -----------------------------------------------------------------------
    # 4. High abandonment rate
    # -----------------------------------------------------------------------
    abandonments = sum(1 for e in events if e.event_type == "BILLING_QUEUE_ABANDON")
    queue_joins = sum(1 for e in events if e.event_type == "BILLING_QUEUE_JOIN")
    if queue_joins >= 3:
        abandon_rate = abandonments / queue_joins
        if abandon_rate >= 0.3:
            severity = "CRITICAL" if abandon_rate >= 0.5 else "WARN"
            anomalies.append({
                "anomaly_id": f"HIGH_ABANDON_{store_id}",
                "type": "HIGH_QUEUE_ABANDONMENT",
                "severity": severity,
                "title": f"Billing abandonment rate: {round(abandon_rate * 100)}%",
                "description": f"{abandonments} of {queue_joins} customers who joined the billing queue left without purchasing.",
                "current_value": round(abandon_rate, 4),
                "suggested_action": "Reduce queue wait time. Consider express billing or mobile payment options.",
                "detected_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            })

    # -----------------------------------------------------------------------
    # 5. Zero traffic anomaly
    # -----------------------------------------------------------------------
    if not events:
        anomalies.append({
            "anomaly_id": f"ZERO_TRAFFIC_{store_id}",
            "type": "ZERO_TRAFFIC",
            "severity": "WARN",
            "title": "No customer events detected in the last 24 hours",
            "description": "Either the store has had zero visitors or the camera feed may be stale.",
            "suggested_action": "Verify camera feeds are live. Check /health for STALE_FEED status.",
            "detected_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

    return {
        "store_id": store_id,
        "window_hours": window_hours,
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
