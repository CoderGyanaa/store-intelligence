# StoreMind AI — System Design

**Candidate:** Gyana Ranjan Sahoo  
**Challenge:** Purplle / Apex Retail Store Intelligence — Round 2  
**Version:** 1.0.0

---

## North Star Metric

> **Offline Store Conversion Rate** = Unique visitors who reached a purchase ÷ Total unique visitors in session window

Every architectural decision traces back to one question: does this make the conversion rate *more accurate* or *more actionable*?

---

## System Architecture

```
CCTV Clips (1080p, 15fps)
        │
        ▼
┌──────────────────────────────┐
│  Detection Layer             │
│  YOLOv8n → person bbox       │
│  ByteTrack → track_id        │
│  StaffClassifier → is_staff  │
│  ZoneManager → zone_id       │
│  DirectionDetector → ENTRY   │
│  ReIDEngine → visitor_id     │
└──────────────┬───────────────┘
               │ structured events (JSONL)
               ▼
┌──────────────────────────────┐
│  Event Ingest (POST /events) │
│  Idempotency by event_id     │
│  Validation (Pydantic v2)    │
│  Partial success on errors   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Storage (PostgreSQL / SQLite│
│  Indexed: store_id + ts      │
│  Indexed: store_id + visitor │
└──────────────┬───────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌────────────┐   ┌──────────────┐
│ Analytics  │   │ Anomaly      │
│ /metrics   │   │ Detection    │
│ /funnel    │   │ /anomalies   │
│ /heatmap   │   │              │
└────────────┘   └──────────────┘
       │                │
       └───────┬────────┘
               ▼
     Live Dashboard (Next.js)
     Real-time polling / SSE
```

---

## Component Design Decisions

### Detection Layer

The pipeline is structured as a single-pass processor: each frame is processed by YOLO → tracker → zone classifier → event emitter in sequence. This avoids the complexity of multi-process queues at the cost of per-frame latency — acceptable since we're running offline on clip files, not true real-time streams.

**Frame subsampling (every 3rd frame → ~5fps effective):** Bounding box movement between adjacent frames at 15fps is small enough that tracking quality is not significantly impacted. The 3× speed gain is meaningful on CPU.

**Staff detection strategy:** HSV histogram matching against known uniform colour ranges. This is fast (~0.2ms per crop) and requires no labelled training data. The tradeoff: it fails on unusual uniforms. In production, the correct fix is a small fine-tuned binary classifier trained on store-specific footage — a 1–2 day labelling effort for a real deployment.

**Re-ID design:** Trajectory-based cosine similarity rather than a deep ReID model (OSNet). Rationale: OSNet requires a GPU and adds significant pipeline complexity for a single-digit improvement in re-entry detection accuracy on the challenge dataset. The trajectory approach is deterministic, debuggable, and handles the challenge's stated edge case (customer leaves and re-enters within 10 minutes) correctly.

### Event Schema

The schema is a strict superset of the challenge specification. Key additions:
- `metadata.session_seq`: ordinal position of this event in the visitor's session — enables funnel reconstruction without full session replay
- `ingested_at`: server-side timestamp added on ingest — enables lag detection in `/health`
- `confidence` is *never suppressed*: low-confidence events are stored with their actual confidence value and flagged at the API layer via `data_confidence` fields

### API Layer

**FastAPI over Django/Flask:** FastAPI's async-first design and native Pydantic integration eliminates an entire category of input validation bugs. The schema is defined once in `models.py` and enforced automatically at the HTTP boundary.

**SQLite in dev, PostgreSQL in prod:** The switch is a single environment variable (`DATABASE_URL`). This gives zero-friction local development (`docker compose up` with no external deps) while supporting production scale. SQLAlchemy async ORM abstracts the difference.

**No caching layer (Redis) in this implementation:** The challenge data size (5 stores, ~1 hour each) doesn't stress a raw SQL query. Adding Redis would improve `/metrics` response time at scale but adds operational complexity not justified at this submission size. Documented as a scaling decision in CHOICES.md.

### Anomaly Detection

Four anomaly types are implemented:

| Anomaly | Detection Method | Rationale |
|---|---|---|
| Queue spike | Count active billing visitors in memory | Real-time; zero lag |
| Conversion drop | Z-score vs 7-day rolling baseline | Statistically grounded; interpretable |
| Dead zone | Last-seen timestamp per zone | Simple; zero false negatives |
| High abandonment | Rate threshold on BILLING_QUEUE events | Direct business metric |

I evaluated using Isolation Forest for multivariate anomaly detection (combining queue depth + dwell time + entry rate simultaneously). This is implemented as a conceptual extension but not wired to the API endpoints. The reason: Isolation Forest requires at minimum ~50 observations per feature to produce reliable scores. The challenge's 20-minute clips don't provide enough data for the model to calibrate — it would produce near-random anomaly scores. Statistical thresholding with domain-informed rules is strictly more reliable at this data volume.

---

## AI-Assisted Decisions

### 1. Re-ID architecture choice

I asked Claude to compare three Re-ID approaches: (1) OSNet-based appearance embedding, (2) trajectory cosine similarity, (3) IOU-based heuristic. Claude suggested OSNet as the "standard industry approach" and was correct that it achieves higher precision in crowded retail settings. I disagreed with applying it here because the challenge explicitly values handling uncertainty gracefully over perfect accuracy, and a trajectory-based approach produces more interpretable outputs for the follow-up Q&A. I chose trajectory similarity with a documented accuracy tradeoff.

### 2. Anomaly detection algorithm selection

I asked Claude to evaluate Isolation Forest vs ARIMA vs Z-score for retail conversion anomaly detection. Claude initially recommended ARIMA on the grounds that time-series forecasting captures cyclical patterns (weekday vs weekend). I overrode this: ARIMA requires stationary time series and at minimum 2–4 weeks of historical data to fit meaningful seasonal components. With 7 days of baseline data, Z-score with a sliding window is strictly more reliable. I used Claude's comparison table as a reference but did not follow its recommendation.

### 3. Event schema `session_seq` field

I asked Claude whether a session reconstruction engine (replaying all events for a visitor to reconstruct their journey) was preferable to embedding `session_seq` in each event at emission time. Claude suggested the reconstruction approach for "cleaner separation of concerns." I chose embedded `session_seq` because it makes the funnel endpoint O(n) in events rather than O(n × sessions), which matters at 40 live stores with continuous event streams. This is one of the cases where Claude's suggestion was architecturally cleaner but operationally more expensive.

---

## Scalability Notes

The current architecture handles the challenge's 5-store dataset comfortably. For 40 live stores:

1. **Detection pipeline:** One GPU worker per camera stream. Horizontal scaling — no shared state between camera workers.
2. **Event ingest:** Replace synchronous HTTP with Kafka. The event schema is already Kafka-compatible (key = `store_id`, value = JSON event).
3. **API queries:** Materialise hourly metric snapshots into a `store_metrics_cache` table. `/metrics` reads the cache; a background job refreshes it every 5 minutes.
4. **Database:** Partition `events` table by `store_id` + month. At 40 stores × 15fps × 8 hours/day, expect ~500M events/month — PostgreSQL partitioning handles this to ~10M rows/partition.

---

## Data Flow: POS Correlation

The challenge requires correlating POS transactions (no customer ID) with visitor sessions using time-window + billing zone presence. Implementation:

```
For each POS transaction at store S, time T:
  Find all visitor_ids who had ZONE_ENTER/ZONE_DWELL in BILLING zone
  within [T - 5min, T]
  Mark those sessions as "purchased" = True
```

This is implemented in the funnel endpoint's `purchased` flag computation. The 5-minute window is a domain heuristic — a customer at the billing counter 5 minutes before a transaction is the strongest available signal without a customer_id link.

---

## Production Readiness Checklist

- [x] `docker compose up` — zero manual steps
- [x] Structured JSON logging with `trace_id` on every request
- [x] `POST /events/ingest` idempotent by `event_id`
- [x] `GET /health` with `STALE_FEED` detection
- [x] Graceful degradation: DB down → HTTP 503 with structured JSON body
- [x] No raw stack traces in HTTP responses
- [x] Test coverage >70% (pipeline + API)
- [x] Edge cases: empty store, all-staff clip, zero purchases, re-entry in funnel
- [x] README: setup in 5 commands
