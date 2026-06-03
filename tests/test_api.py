# PROMPT: "Write pytest tests for a FastAPI store analytics API. Cover:
# 1) POST /events/ingest idempotency (same payload twice → same accepted count first time, 0 second),
# 2) Staff exclusion from metrics,
# 3) Zero-traffic stores returning valid JSON not 500,
# 4) Re-entry deduplication in funnel,
# 5) Anomaly detection for queue spike,
# 6) Health endpoint STALE_FEED flag,
# 7) Schema validation rejecting malformed events.
# Use pytest-asyncio with an in-memory SQLite DB. Include fixtures."
#
# CHANGES MADE:
# - Added async fixture for test DB (AI used sync fixtures initially)
# - Fixed event timestamp format: AI used datetime.now() without UTC Z suffix
# - Added explicit is_staff=False assertions (AI forgot staff exclusion in metrics test)
# - Split monolith test into separate functions for clearer failure messages
# - Fixed Pydantic v2 model_validate call (AI used .parse_obj() which is v1)

import json
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db, EventRecord

# ---------------------------------------------------------------------------
# Test DB setup — in-memory SQLite
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ts(offset_minutes: int = 0) -> str:
    t = datetime.now(timezone.utc) - timedelta(minutes=offset_minutes)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _event(
    event_type="ENTRY",
    visitor_id="VIS_aaa111",
    store_id="STORE_BLR_002",
    camera_id="CAM_ENTRY_01",
    zone_id=None,
    dwell_ms=0,
    is_staff=False,
    confidence=0.92,
    offset_minutes=0,
    **meta,
):
    return {
        "event_id": f"test-{visitor_id}-{event_type}-{offset_minutes}",
        "store_id": store_id,
        "camera_id": camera_id,
        "visitor_id": visitor_id,
        "event_type": event_type,
        "timestamp": _ts(offset_minutes),
        "zone_id": zone_id,
        "dwell_ms": dwell_ms,
        "is_staff": is_staff,
        "confidence": confidence,
        "metadata": {"session_seq": 1, **meta},
    }


# ---------------------------------------------------------------------------
# Part A — Schema compliance
# ---------------------------------------------------------------------------
class TestSchemaValidation:
    @pytest.mark.asyncio
    async def test_valid_event_accepted(self, client):
        r = await client.post("/events/ingest", json={"events": [_event()]})
        assert r.status_code == 200
        assert r.json()["accepted"] == 1
        assert r.json()["rejected"] == 0

    @pytest.mark.asyncio
    async def test_invalid_event_type_rejected(self, client):
        bad = _event()
        bad["event_type"] = "FLYING_SAUCER"
        r = await client.post("/events/ingest", json={"events": [bad]})
        assert r.status_code == 200
        assert r.json()["rejected"] == 1

    @pytest.mark.asyncio
    async def test_invalid_confidence_rejected(self, client):
        bad = _event()
        bad["confidence"] = 1.5  # > 1.0
        r = await client.post("/events/ingest", json={"events": [bad]})
        assert r.status_code == 200
        assert r.json()["rejected"] == 1

    @pytest.mark.asyncio
    async def test_batch_partial_success(self, client):
        """Valid + invalid in same batch → partial accept."""
        events = [_event(visitor_id="VIS_good"), _event(visitor_id="VIS_bad")]
        events[1]["event_type"] = "NONSENSE"
        r = await client.post("/events/ingest", json={"events": events})
        assert r.status_code == 200
        d = r.json()
        assert d["accepted"] == 1
        assert d["rejected"] == 1


# ---------------------------------------------------------------------------
# Part B — Idempotency
# ---------------------------------------------------------------------------
class TestIdempotency:
    @pytest.mark.asyncio
    async def test_double_ingest_idempotent(self, client):
        """Same payload ingested twice → second call skips all (idempotent_skips = n)."""
        payload = {"events": [_event(visitor_id="VIS_idem", event_type="ENTRY")]}
        r1 = await client.post("/events/ingest", json=payload)
        r2 = await client.post("/events/ingest", json=payload)

        assert r1.json()["accepted"] == 1
        assert r2.json()["accepted"] == 0
        assert r2.json()["idempotent_skips"] == 1

    @pytest.mark.asyncio
    async def test_different_event_ids_accepted(self, client):
        """Two events with different event_ids (same visitor) → both accepted."""
        e1 = _event(visitor_id="VIS_x")
        e2 = _event(visitor_id="VIS_x", event_type="EXIT")
        e2["event_id"] = "different-id-999"
        r = await client.post("/events/ingest", json={"events": [e1, e2]})
        assert r.json()["accepted"] == 2


# ---------------------------------------------------------------------------
# Part B — Staff exclusion from metrics
# ---------------------------------------------------------------------------
class TestStaffExclusion:
    @pytest.mark.asyncio
    async def test_staff_excluded_from_visitor_count(self, client):
        """Staff events must not inflate unique_visitors in /metrics."""
        staff_ev = _event(visitor_id="VIS_staff", is_staff=True, offset_minutes=5)
        cust_ev = _event(visitor_id="VIS_cust", is_staff=False, offset_minutes=5)

        await client.post("/events/ingest", json={"events": [staff_ev, cust_ev]})
        r = await client.get("/stores/STORE_BLR_002/metrics")
        assert r.status_code == 200
        d = r.json()
        # Only 1 customer — staff must be excluded
        assert d["unique_visitors"] == 1

    @pytest.mark.asyncio
    async def test_all_staff_clip_returns_zero_visitors(self, client):
        """If only staff events ingested, metrics returns 0 unique_visitors (not an error)."""
        events = [
            _event(visitor_id=f"VIS_staff_{i}", is_staff=True, offset_minutes=i)
            for i in range(5)
        ]
        await client.post("/events/ingest", json={"events": events})
        r = await client.get("/stores/STORE_BLR_002/metrics")
        assert r.status_code == 200
        assert r.json()["unique_visitors"] == 0


# ---------------------------------------------------------------------------
# Part B — Zero-traffic store
# ---------------------------------------------------------------------------
class TestZeroTraffic:
    @pytest.mark.asyncio
    async def test_empty_store_metrics_not_crash(self, client):
        """Store with zero events returns valid JSON, no 5xx."""
        r = await client.get("/stores/STORE_EMPTY_999/metrics")
        assert r.status_code == 200
        d = r.json()
        assert d["unique_visitors"] == 0
        assert d["conversion_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_empty_store_funnel_not_crash(self, client):
        r = await client.get("/stores/STORE_EMPTY_999/funnel")
        assert r.status_code == 200
        d = r.json()
        assert d["overall_conversion_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_empty_store_anomalies_returns_zero_traffic(self, client):
        """Zero-traffic store should emit a ZERO_TRAFFIC anomaly, not crash."""
        r = await client.get("/stores/STORE_EMPTY_999/anomalies")
        assert r.status_code == 200
        types = [a["type"] for a in r.json()["anomalies"]]
        assert "ZERO_TRAFFIC" in types


# ---------------------------------------------------------------------------
# Part B — Re-entry deduplication in funnel
# ---------------------------------------------------------------------------
class TestReentryDedup:
    @pytest.mark.asyncio
    async def test_reentry_does_not_double_count_visitor(self, client):
        """REENTRY by same visitor_id → funnel counts as 1 unique session, not 2."""
        events = [
            _event(visitor_id="VIS_reentry", event_type="ENTRY", offset_minutes=60),
            _event(visitor_id="VIS_reentry", event_type="EXIT", offset_minutes=50),
            _event(visitor_id="VIS_reentry", event_type="REENTRY", offset_minutes=40),
        ]
        for i, ev in enumerate(events):
            ev["event_id"] = f"reentry-test-{i}"
        await client.post("/events/ingest", json={"events": events})

        r = await client.get("/stores/STORE_BLR_002/funnel")
        assert r.status_code == 200
        d = r.json()
        # Funnel unique_visitor_sessions must be 1, not 2
        assert d["unique_visitor_sessions"] == 1
        assert d["reentry_events"] == 1


# ---------------------------------------------------------------------------
# Part B — Anomaly detection
# ---------------------------------------------------------------------------
class TestAnomalyDetection:
    @pytest.mark.asyncio
    async def test_queue_spike_detected(self, client):
        """6 concurrent billing visitors → BILLING_QUEUE_SPIKE anomaly."""
        events = [
            _event(visitor_id=f"VIS_q{i}", event_type="BILLING_QUEUE_JOIN",
                   zone_id="BILLING", offset_minutes=2)
            for i in range(6)
        ]
        for i, ev in enumerate(events):
            ev["event_id"] = f"queue-test-{i}"
        await client.post("/events/ingest", json={"events": events})

        r = await client.get("/stores/STORE_BLR_002/anomalies")
        assert r.status_code == 200
        types = [a["type"] for a in r.json()["anomalies"]]
        assert "BILLING_QUEUE_SPIKE" in types

    @pytest.mark.asyncio
    async def test_anomaly_has_suggested_action(self, client):
        """Every anomaly must include a suggested_action string."""
        r = await client.get("/stores/STORE_EMPTY_999/anomalies")
        for anomaly in r.json()["anomalies"]:
            assert "suggested_action" in anomaly
            assert len(anomaly["suggested_action"]) > 10

    @pytest.mark.asyncio
    async def test_anomaly_severity_valid(self, client):
        """All severities must be INFO / WARN / CRITICAL."""
        r = await client.get("/stores/STORE_EMPTY_999/anomalies")
        valid = {"INFO", "WARN", "CRITICAL"}
        for a in r.json()["anomalies"]:
            assert a["severity"] in valid


# ---------------------------------------------------------------------------
# Part C — Health endpoint
# ---------------------------------------------------------------------------
class TestHealth:
    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        d = r.json()
        assert "status" in d
        assert "timestamp" in d

    @pytest.mark.asyncio
    async def test_stale_feed_flagged_on_old_events(self, client):
        """Event with timestamp > 10 min ago → STALE_FEED for that store."""
        old_ev = _event(visitor_id="VIS_old", offset_minutes=30)
        old_ev["event_id"] = "stale-test-001"
        await client.post("/events/ingest", json={"events": [old_ev]})

        r = await client.get("/health")
        assert r.status_code == 200
        stores = r.json().get("stores", [])
        blr = next((s for s in stores if s["store_id"] == "STORE_BLR_002"), None)
        assert blr is not None
        assert blr["feed_status"] == "STALE_FEED"

    @pytest.mark.asyncio
    async def test_health_no_raw_stacktrace(self, client):
        """Health response must never include raw Python tracebacks."""
        r = await client.get("/health")
        body = r.text
        assert "Traceback" not in body
        assert "File \"" not in body


# ---------------------------------------------------------------------------
# Part B — Heatmap
# ---------------------------------------------------------------------------
class TestHeatmap:
    @pytest.mark.asyncio
    async def test_heatmap_normalised_0_100(self, client):
        """Heat scores must be in range [0, 100]."""
        events = []
        for zone, count in [("SKINCARE", 10), ("MAKEUP", 5), ("HAIRCARE", 2)]:
            for i in range(count):
                ev = _event(visitor_id=f"VIS_{zone}_{i}", event_type="ZONE_ENTER",
                            zone_id=zone, offset_minutes=i)
                ev["event_id"] = f"heatmap-{zone}-{i}"
                events.append(ev)
        await client.post("/events/ingest", json={"events": events})

        r = await client.get("/stores/STORE_BLR_002/heatmap")
        assert r.status_code == 200
        for zone in r.json()["zones"]:
            assert 0 <= zone["heat_score"] <= 100

    @pytest.mark.asyncio
    async def test_heatmap_empty_store(self, client):
        """Empty store → empty zones list, data_confidence=LOW."""
        r = await client.get("/stores/STORE_EMPTY_999/heatmap")
        assert r.status_code == 200
        d = r.json()
        assert d["zones"] == []
        assert d["data_confidence"] == "LOW"
