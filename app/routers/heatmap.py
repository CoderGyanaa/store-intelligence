"""
StoreMind — GET /stores/{store_id}/heatmap
Zone visit frequency + avg dwell, normalised 0–100, with data_confidence flag.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db, EventRecord

logger = logging.getLogger("storemind.heatmap")
router = APIRouter()


@router.get("/{store_id}/heatmap")
async def get_heatmap(
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
                EventRecord.zone_id != None,
            )
        )
    )
    events = result.scalars().all()

    zone_visits: dict[str, set] = defaultdict(set)
    zone_dwell: dict[str, list] = defaultdict(list)

    for e in events:
        if e.zone_id:
            if e.event_type in ("ZONE_ENTER", "BILLING_QUEUE_JOIN"):
                zone_visits[e.zone_id].add(e.visitor_id)
            elif e.event_type == "ZONE_EXIT" and e.dwell_ms > 0:
                zone_dwell[e.zone_id].append(e.dwell_ms)

    if not zone_visits:
        return {
            "store_id": store_id,
            "window_hours": window_hours,
            "zones": [],
            "data_confidence": "LOW",
        }

    # Normalise visit counts 0–100
    max_visits = max(len(v) for v in zone_visits.values()) or 1

    zones_data = []
    for zone, visitors in zone_visits.items():
        visit_count = len(visitors)
        avg_dwell_s = round(sum(zone_dwell[zone]) / len(zone_dwell[zone]) / 1000, 1) if zone_dwell[zone] else 0.0
        session_count = visit_count

        zones_data.append({
            "zone_id": zone,
            "visit_count": visit_count,
            "unique_visitors": visit_count,
            "avg_dwell_seconds": avg_dwell_s,
            "heat_score": round(visit_count / max_visits * 100),
            "data_confidence": "HIGH" if session_count >= 20 else ("MEDIUM" if session_count >= 5 else "LOW"),
        })

    # Sort by heat score descending
    zones_data.sort(key=lambda x: x["heat_score"], reverse=True)

    total_sessions = sum(z["visit_count"] for z in zones_data)
    overall_confidence = "HIGH" if total_sessions >= 20 else ("MEDIUM" if total_sessions >= 5 else "LOW")

    return {
        "store_id": store_id,
        "window_hours": window_hours,
        "zones": zones_data,
        "data_confidence": overall_confidence,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
