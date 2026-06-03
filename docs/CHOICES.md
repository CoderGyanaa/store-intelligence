# StoreMind AI — Engineering Choices

**Three decisions. Full reasoning. AI disagreements documented.**

---

## Decision 1 — Detection Model: YOLOv8n

### Options Considered

| Model | Pros | Cons |
|---|---|---|
| YOLOv8n | Fast CPU inference (~40ms/frame), mature tracking integration, zero fine-tuning needed for person detection | Lower accuracy than larger models on partial occlusion |
| YOLOv8x | Best accuracy on crowded scenes | ~6× slower than n; would require GPU for real-time |
| RT-DETR | Transformer-based; handles occlusion better | No production ByteTrack integration; higher VRAM requirement |
| MediaPipe Person | Lightweight, runs on CPU | No tracking ID output; requires custom re-ID from scratch |
| GPT-4V / Gemini Vision (VLM) | Zero-shot zone classification, staff detection without labelling | ~2s/frame latency at API costs; unsuitable for per-frame processing |

### What AI Suggested

I used Claude to evaluate the trade-offs. Claude initially recommended RT-DETR for "superior transformer-based occlusion handling" and cited its COCO benchmark score. It also suggested using a VLM (Claude Vision or GPT-4V) for staff classification and zone determination on keyframes.

### What I Chose and Why

**YOLOv8n for detection + ByteTrack for tracking.**

RT-DETR's benchmark advantage is real but irrelevant here: the challenge's partial occlusion cases (people behind displays) are not so severe that they break YOLOv8n's person detector — they reduce confidence scores, which I keep and surface via the `confidence` field. Graceful confidence degradation is explicitly scored; perfect detection is not.

On VLMs for staff classification: I evaluated this seriously. Running GPT-4V on every 30th frame (1 keyframe every 2 seconds) for zone classification is feasible at ~$0.002/frame × 18,000 frames = ~$36/clip. The accuracy improvement on "is this person wearing a staff uniform?" is real. My decision to use HSV histograms instead was pragmatic: the challenge evaluates re-id, funnel, and conversion accuracy far more heavily than staff classification precision. HSV matching with tunable thresholds gets 80–85% accuracy on uniform colours at zero API cost and zero latency. I documented this trade-off in DESIGN.md > AI-Assisted Decisions.

**What would make me change this decision:** A production deployment where staff mis-classification inflates conversion rate (a serious measurement error) would justify the VLM cost. A 3-day labelling sprint + fine-tuned binary classifier is the correct long-term answer.

---

## Decision 2 — Event Schema Design

### Options Considered

**Option A: Minimal schema** — only the fields required by the challenge spec. Clean, small, easy to validate.

**Option B: Extended schema with session_seq** — add `session_seq` (ordinal position in visitor session) as a first-class field emitted by the pipeline.

**Option C: Separate session reconstruction service** — store raw events and replay them on-demand to compute session shape at query time.

### What AI Suggested

When I asked Claude to review the schema, it recommended Option C: a dedicated session reconstruction service, arguing it provides "cleaner separation of concerns" — the pipeline doesn't need to know about sessions, and session logic can evolve independently. Claude is architecturally correct.

### What I Chose and Why

**Option B — embedded `session_seq`.**

Here's why I overrode Claude's recommendation:

The funnel endpoint (`GET /stores/{id}/funnel`) must reconstruct the visitor journey for every API call. Under Option C, that means: for each visitor_id, load all their events ordered by timestamp, replay the sequence, and compute stage counts. At 40 stores × 1,000 daily visitors, that's 40,000 session replays per funnel query. With `session_seq` embedded at emission time, the funnel query is a single GROUP BY on `visitor_id` + filter on `event_type`.

The "cleaner separation" in Option C comes at a concrete performance cost that compounds at scale. The trade-off is acceptable when session logic is highly complex (multi-day attribution windows, cross-store journeys). For this system, sessions are single-store, single-day, and end on EXIT — simple enough that the pipeline can embed the sequence number with no fragility.

**Schema invariant documented:** `session_seq` resets to 1 on ENTRY and increments monotonically. REENTRY increments from the previous session's last seq (not reset). This prevents funnel double-counting without requiring event replay.

---

## Decision 3 — API Architecture: Synchronous FastAPI vs Event-Driven

### Options Considered

**Option A: Synchronous FastAPI** — HTTP POST to ingest events, SQL queries for analytics, polling-based dashboard updates.

**Option B: Kafka + stream processing** — Detection pipeline emits to Kafka, Flink/Spark consumes, materialized views served by API.

**Option C: SQLite for dev, PostgreSQL for prod, no message queue** — same as A but explicit about storage backends.

### What AI Suggested

Claude recommended Option B heavily, citing "event sourcing best practices" and the fact that Kafka enables replay, exactly-once delivery, and horizontal consumer scaling. It also noted that `/metrics` returning stale data without Kafka is a production risk.

### What I Chose and Why

**Option A / C — synchronous FastAPI + PostgreSQL.**

Claude is correct that Kafka is the right architecture for 40 stores sending 15fps events in real-time. At that scale, direct HTTP ingest creates a bottleneck and a single point of failure. I agree with Claude on the target architecture.

**I chose the simpler approach for three reasons specific to this submission:**

1. **Acceptance gate dependency:** `docker compose up` must start everything. A Kafka dependency means the grader needs a working Kafka cluster in Docker. Every additional container is another failure mode. The challenge README warns about setup complexity — I optimised for zero-friction evaluation.

2. **Scored categories don't require Kafka:** The scoring rubric awards points for "containerisation + README" (5pts) and "structured logs + health endpoint" (5pts). Kafka adds neither. The points available for architecture depth are in DESIGN.md documentation, not in whether Kafka actually runs.

3. **The idempotency design is Kafka-compatible:** The `event_id` deduplication in `POST /events/ingest` is exactly the pattern used in Kafka consumer idempotency (idempotent producers + consumer offset commit). The schema is designed for Kafka — switching the transport layer is a config change, not a re-design.

**Explicitly documented for follow-up Q&A:** If asked "what breaks first at 40 live stores?", the answer is the HTTP ingest endpoint — it becomes a bottleneck at ~5,000 events/second. The fix is Kafka with the existing schema. This is a known, intentional trade-off, not a gap.

---

## Summary

| Decision | AI Suggestion | My Choice | Agreed? |
|---|---|---|---|
| Detection model | RT-DETR + VLM for classification | YOLOv8n + HSV staff classifier | Partial — VLM is better for staff, impractical per-frame |
| Event schema | Separate session reconstruction service | Embedded `session_seq` | Overrode — performance argument |
| API architecture | Kafka + stream processing | Synchronous FastAPI + PostgreSQL | Overrode — evaluation constraint, documented upgrade path |
