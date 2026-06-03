"""
StoreMind — Pydantic event schema and validation models.
Schema mirrors the challenge specification exactly.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, Annotated
from pydantic import BaseModel, Field, field_validator, ConfigDict
import uuid


class EventMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")
    queue_depth: Optional[int] = None
    sku_zone: Optional[str] = None
    session_seq: Optional[int] = None


EVENT_TYPES = {
    "ENTRY", "EXIT", "ZONE_ENTER", "ZONE_EXIT", "ZONE_DWELL",
    "BILLING_QUEUE_JOIN", "BILLING_QUEUE_ABANDON", "REENTRY",
    "CROWD_ALERT", "QUEUE_ALERT", "STAFF_IDLE", "ANOMALY_DETECTED",
}


class StoreEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    store_id: str
    camera_id: str
    visitor_id: str
    event_type: str
    timestamp: str
    zone_id: Optional[str] = None
    dwell_ms: int = 0
    is_staff: bool = False
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: EventMetadata = Field(default_factory=EventMetadata)

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v):
        if v not in EVENT_TYPES:
            raise ValueError(f"Unknown event_type: {v}")
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Invalid timestamp format: {v}. Must be ISO-8601 UTC")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v):
        return round(v, 4)


class IngestRequest(BaseModel):
    events: list[StoreEvent] = Field(..., max_length=500)


class IngestResponse(BaseModel):
    accepted: int
    rejected: int
    errors: list[dict] = []
    idempotent_skips: int = 0
