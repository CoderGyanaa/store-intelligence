"""
StoreMind — GET /stores/{store_id}/metrics
Real-time: unique visitors, conversion rate, avg dwell per zone, queue depth, abandonment rate.
Excludes is_staff=true. Handles zero-purchase stores.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.database import get_db, EventRecord

logger = logging.getLogger("storemind.metrics")
router = APIRouter()


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


@router.get("/{store_id}/metrics")
async def get_metrics(
    store_id: str,
    window_hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # Fetch all customer events (exclude staff) in window
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

    if not events:
        return {
            "store_id": store_id,
            "window_hours": window_hours,
            "unique_visitors": 0,
            "conversion_rate": 0.0,
            "avg_dwell_per_zone": {},
            "queue_depth": 0,
            "abandonment_rate": 0.0,
            "total_events": 0,
            "data_confidence": "LOW",
        }

    # Unique visitors (by visitor_id, de-dup re-entries per session)
    visitor_ids = {e.visitor_id for e in events if e.event_type in ("ENTRY", "REENTRY")}
    unique_visitors = len(visitor_ids)

    # Avg dwell per zone
    zone_dwell: dict[str, list] = defaultdict(list)
    for e in events:
        if e.event_type == "ZONE_EXIT" and e.zone_id and e.dwell_ms > 0:
            zone_dwell[e.zone_id].append(e.dwell_ms)
    avg_dwell = {
        zone: round(sum(dwells) / len(dwells) / 1000, 1)  # seconds
        for zone, dwells in zone_dwell.items()
    }

    # Queue depth (current active in BILLING zone)
    billing_entries = {e.visitor_id for e in events if e.event_type in ("BILLING_QUEUE_JOIN", "ZONE_ENTER") and e.zone_id == "BILLING"}
    billing_exits = {e.visitor_id for e in events if e.event_type in ("ZONE_EXIT", "EXIT") and e.zone_id == "BILLING"}
    queue_depth = max(0, len(billing_entries) - len(billing_exits))

    # Abandonment rate
    abandonments = sum(1 for e in events if e.event_type == "BILLING_QUEUE_ABANDON")
    queue_joins = sum(1 for e in events if e.event_type in ("BILLING_QUEUE_JOIN",))
    abandonment_rate = round(abandonments / queue_joins, 3) if queue_joins > 0 else 0.0

    # Conversion rate: visitors who reached BILLING zone → unique conversions
    # (POS correlation via time-window — approximated by billing zone presence)
    billing_visitors = {e.visitor_id for e in events if e.zone_id == "BILLING"}
    converted = len(billing_visitors)
    conversion_rate = round(converted / unique_visitors, 3) if unique_visitors > 0 else 0.0

    data_confidence = "HIGH" if unique_visitors >= 20 else ("MEDIUM" if unique_visitors >= 5 else "LOW")

    return {
        "store_id": store_id,
        "window_hours": window_hours,
        "unique_visitors": unique_visitors,
        "conversion_rate": conversion_rate,
        "avg_dwell_per_zone": avg_dwell,
        "queue_depth": queue_depth,
        "abandonment_rate": abandonment_rate,
        "total_events": len(events),
        "data_confidence": data_confidence,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
