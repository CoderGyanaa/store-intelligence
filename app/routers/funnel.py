"""
StoreMind — GET /stores/{store_id}/funnel
Conversion funnel: Entry → Zone Visit → Billing Queue → Purchase
Session is the unit. Re-entries must not double-count a visitor.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db, EventRecord

logger = logging.getLogger("storemind.funnel")
router = APIRouter()


@router.get("/{store_id}/funnel")
async def get_funnel(
    store_id: str,
    window_hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

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

    # Build per-visitor session data
    # Re-entry: same visitor_id → same session unit (deduplicated)
    visitor_sessions: dict[str, dict] = {}

    for e in events:
        vid = e.visitor_id
        if vid not in visitor_sessions:
            visitor_sessions[vid] = {
                "entered": False,
                "visited_zone": False,
                "reached_billing": False,
                "purchased": False,   # approximated by billing zone presence
                "reentry_count": 0,
            }
        sess = visitor_sessions[vid]

        if e.event_type in ("ENTRY",):
            sess["entered"] = True
        elif e.event_type == "REENTRY":
            sess["entered"] = True
            sess["reentry_count"] += 1
        elif e.event_type in ("ZONE_ENTER", "ZONE_DWELL") and e.zone_id not in (None, "ENTRY_AREA", "BILLING"):
            sess["visited_zone"] = True
        elif e.event_type in ("BILLING_QUEUE_JOIN", "ZONE_ENTER") and e.zone_id == "BILLING":
            sess["reached_billing"] = True
        elif e.event_type == "BILLING_QUEUE_ABANDON":
            pass  # reached billing but did NOT purchase
        elif e.event_type == "ZONE_DWELL" and e.zone_id == "BILLING":
            # Dwell in billing ≥ 30s is a strong purchase signal
            sess["purchased"] = True

    total_entered = sum(1 for s in visitor_sessions.values() if s["entered"])
    total_zone = sum(1 for s in visitor_sessions.values() if s["visited_zone"])
    total_billing = sum(1 for s in visitor_sessions.values() if s["reached_billing"])
    total_purchased = sum(1 for s in visitor_sessions.values() if s["purchased"])

    def drop_pct(a, b):
        if b == 0:
            return 0.0
        return round((b - a) / b * 100, 1)

    return {
        "store_id": store_id,
        "window_hours": window_hours,
        "funnel": [
            {
                "stage": "Entry",
                "visitors": total_entered,
                "drop_off_pct": 0.0,
            },
            {
                "stage": "Zone Visit",
                "visitors": total_zone,
                "drop_off_pct": drop_pct(total_zone, total_entered),
            },
            {
                "stage": "Billing Queue",
                "visitors": total_billing,
                "drop_off_pct": drop_pct(total_billing, total_zone),
            },
            {
                "stage": "Purchase",
                "visitors": total_purchased,
                "drop_off_pct": drop_pct(total_purchased, total_billing),
            },
        ],
        "overall_conversion_rate": round(total_purchased / total_entered, 3) if total_entered > 0 else 0.0,
        "reentry_events": sum(s["reentry_count"] for s in visitor_sessions.values()),
        "unique_visitor_sessions": len(visitor_sessions),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
