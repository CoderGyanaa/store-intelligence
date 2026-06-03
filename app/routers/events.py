"""
StoreMind — POST /events/ingest
Idempotent batch ingest: deduplicates by event_id.
Returns partial success on malformed events.
Accepts raw list to enable per-event validation (not Pydantic batch-level rejection).
"""

import json
import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import ValidationError
from typing import Any

from app.database import get_db, EventRecord
from app.models import IngestResponse, StoreEvent

logger = logging.getLogger("storemind.ingest")
router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_events(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
    
    raw_events: list[Any] = body.get("events", [])
    if not isinstance(raw_events, list):
        return JSONResponse(status_code=400, content={"error": "'events' must be a list"})
    if len(raw_events) > 500:
        return JSONResponse(status_code=400, content={"error": "Batch size exceeds 500"})

    # Validate per-event — collect valid ones, record failures
    valid_events: list[StoreEvent] = []
    errors = []
    for i, raw in enumerate(raw_events):
        try:
            ev = StoreEvent.model_validate(raw)
            valid_events.append(ev)
        except (ValidationError, Exception) as e:
            eid = raw.get("event_id", f"index_{i}") if isinstance(raw, dict) else f"index_{i}"
            errors.append({"event_id": eid, "error": str(e)[:200]})

    rejected = len(errors)

    # Fetch existing event_ids for deduplication
    incoming_ids = [e.event_id for e in valid_events]
    existing_ids: set[str] = set()
    if incoming_ids:
        existing = await db.execute(
            select(EventRecord.event_id).where(EventRecord.event_id.in_(incoming_ids))
        )
        existing_ids = {row[0] for row in existing.fetchall()}

    new_records = []
    accepted = 0
    skipped = 0
    for ev in valid_events:
        if ev.event_id in existing_ids:
            skipped += 1
            continue
        rec = EventRecord(
            event_id=ev.event_id,
            store_id=ev.store_id,
            camera_id=ev.camera_id,
            visitor_id=ev.visitor_id,
            event_type=ev.event_type,
            timestamp=ev.timestamp,
            zone_id=ev.zone_id,
            dwell_ms=ev.dwell_ms,
            is_staff=ev.is_staff,
            confidence=ev.confidence,
            metadata_json=ev.metadata.model_dump_json(),
        )
        new_records.append(rec)
        accepted += 1

    if new_records:
        db.add_all(new_records)
        await db.commit()

    logger.info(
        f"trace_id={trace_id} ingest: accepted={accepted} rejected={rejected} "
        f"idempotent_skips={skipped} event_count={len(raw_events)}"
    )

    return IngestResponse(
        accepted=accepted,
        rejected=rejected,
        errors=errors[:20],
        idempotent_skips=skipped,
    )
