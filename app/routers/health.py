"""
StoreMind — GET /health
Service status, last event timestamp per store, STALE_FEED warning if > 10 min lag.
"""

import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.database import get_db, EventRecord, get_db_status

logger = logging.getLogger("storemind.health")
router = APIRouter()

STALE_THRESHOLD_MINUTES = 10


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    db_status = await get_db_status()

    # Last event per store
    try:
        result = await db.execute(
            select(EventRecord.store_id, func.max(EventRecord.timestamp).label("last_event"))
            .group_by(EventRecord.store_id)
        )
        rows = result.fetchall()
    except Exception as e:
        return {
            "status": "degraded",
            "database": "unavailable",
            "error": str(e),
            "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    stale_threshold = (now - timedelta(minutes=STALE_THRESHOLD_MINUTES)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    stores = []
    any_stale = False

    for row in rows:
        store_id, last_event = row
        is_stale = last_event is None or last_event < stale_threshold
        if is_stale:
            any_stale = True
        stores.append({
            "store_id": store_id,
            "last_event_timestamp": last_event,
            "feed_status": "STALE_FEED" if is_stale else "OK",
            "lag_minutes": (
                round((now - datetime.fromisoformat(last_event.replace("Z", "+00:00"))).total_seconds() / 60, 1)
                if last_event else None
            ),
        })

    overall = "degraded" if any_stale else "ok"

    return {
        "status": overall,
        "version": "1.0.0",
        "database": db_status.get("status", "unknown"),
        "total_events_ingested": db_status.get("event_count", 0),
        "stores": stores,
        "stale_feed_warning": any_stale,
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
