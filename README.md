<div align="center">

<!-- Animated Banner -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0A0F2C,50:1A4A8A,100:3A7FD5&height=200&section=header&text=StoreMind%20AI&fontSize=60&fontColor=ffffff&fontAlignY=38&desc=Raw%20CCTV%20→%20Real-Time%20Store%20Intelligence&descAlignY=58&descColor=6AABFF&animation=fadeIn" width="100%"/>

<!-- Badges Row 1 -->
<p>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=next.js&logoColor=white"/>
  <img src="https://img.shields.io/badge/YOLOv8-Ultralytics-FF6B35?style=for-the-badge&logo=opencv&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
</p>

<!-- Badges Row 2 -->
<p>
  <img src="https://img.shields.io/badge/Tests-39%20Passing-4ADE80?style=for-the-badge&logo=pytest&logoColor=white"/>
  <img src="https://img.shields.io/badge/Coverage->70%25-4ADE80?style=for-the-badge&logo=codecov&logoColor=white"/>
  <img src="https://img.shields.io/badge/API-6%20Endpoints-6AABFF?style=for-the-badge&logo=swagger&logoColor=white"/>
  <img src="https://img.shields.io/badge/Stores-5%20Live-FBBF24?style=for-the-badge&logo=mapbox&logoColor=white"/>
  <img src="https://img.shields.io/badge/Purplle-Tech%20Challenge%202026-A855F7?style=for-the-badge"/>
</p>

<!-- Animated typing -->

<p align="center">
  <img
    src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=18&duration=3000&pause=800&color=3A7FD5&center=true&vCenter=true&repeat=true&width=700&lines=CCTV+Footage+to+Real-Time+Business+Intelligence;YOLOv8+Detection+%7C+ByteTrack+%7C+Re-ID+Engine;FastAPI+%7C+Next.js+%7C+Docker+%7C+39+Tests+Passing"
    alt="Typing SVG"
  />
</p>



<br/>

<!-- Live status indicators -->
<p>
  <img src="https://img.shields.io/badge/🟢%20API-localhost%3A8000-0d1117?style=flat-square&labelColor=0d1117&color=4ADE80"/>
  &nbsp;
  <img src="https://img.shields.io/badge/🟢%20Dashboard-localhost%3A3000-0d1117?style=flat-square&labelColor=0d1117&color=4ADE80"/>
  &nbsp;
  <img src="https://img.shields.io/badge/🟢%20Real--time-Updating%20every%204s-0d1117?style=flat-square&labelColor=0d1117&color=4ADE80"/>
</p>

</div>

---

<!-- Animated separator -->
<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## ⚡ What is StoreMind AI?

<table>
<tr>
<td width="50%">

**StoreMind AI** is a production-grade retail intelligence platform that transforms raw CCTV footage into real-time business insights.

Built for the **Purplle Tech Challenge 2026 — Round 2**, it solves the core problem of offline store analytics — giving physical stores the same data visibility that online channels take for granted.

```
Offline Store Conversion Rate
= Visitors who purchased
  ÷ Total unique visitors
```

Every line of code traces back to this single north star metric.

</td>
<td width="50%">

```python
# What StoreMind does in one shot
pipeline = DetectionPipeline(config)
pipeline.run("cctv_clip.mp4", "events.jsonl")

# 474 structured events emitted →
# ENTRY, ZONE_ENTER, ZONE_DWELL,
# BILLING_QUEUE_JOIN, REENTRY, EXIT

# Ingest → API → Dashboard
# All live. All real-time.
```

</td>
</tr>
</table>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          StoreMind AI — Full Stack                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   📹 CCTV Clips (1080p · 15fps)                                             │
│          │                                                                  │
│          ▼                                                                  │
│   ┌──────────────────────────────────────────────┐                          │
│   │           Detection Pipeline                 │                          │
│   │  YOLOv8n ──► ByteTrack ──► Zone Manager      │                          │
│   │      │           │              │            │                          │
│   │  Staff HSV    Re-ID Engine   Direction       │                          │
│   │  Classifier   (cosine sim)   Detector        │                          │
│   └──────────────────────────────────────────────┘                          │
│          │                                                                  │
│          ▼  474 structured events (JSONL)                                   │
│   ┌──────────────────────────────────────────────┐                          │
│   │         Intelligence API  (FastAPI)          │                          │
│   │                                              │                          │
│   │  POST /events/ingest  (idempotent · batch)   │                          │
│   │  GET  /stores/{id}/metrics                   │                          │
│   │  GET  /stores/{id}/funnel                    │                          │
│   │  GET  /stores/{id}/heatmap                   │                          │
│   │  GET  /stores/{id}/anomalies                 │                          │
│   │  GET  /health          (STALE_FEED detect)   │                          │
│   └──────────────────────────────────────────────┘                          │
│          │                           │                                      │
│          ▼                           ▼                                      │
│   PostgreSQL / SQLite          Anomaly Engine                               │
│   (async SQLAlchemy)           Z-score · Rules                              │
│          │                                                                  │
│          ▼                                                                  │
│   ┌──────────────────────────────────────────────┐                          │
│   │       Live Dashboard  (Next.js 14)           │                          │
│   │  Traffic Chart · Heatmap · Funnel · Alerts   │                          │
│   │  Event Stream · AI Insights · Multi-store    │                          │
│   └──────────────────────────────────────────────┘                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 📸 Project Screenshots

### 🏠 Dashboard Overview

Real-time retail KPIs including visitor count, conversion rate, dwell time, queue depth, abandonment rate, and AI-generated business insights.

<img width="1919" height="903" alt="image" src="https://github.com/user-attachments/assets/2bb73d1d-9bf5-46d7-8237-0157250ddb26" />


---

### 📈 Traffic Analytics

Monitor customer traffic patterns, visitor trends, and store activity in real time.

<img width="1919" height="928" alt="image" src="https://github.com/user-attachments/assets/526046c0-816c-4a9e-9c9a-5171a2db4d6b" />


---

### 🔥 Zone Heatmap Analytics

Visualize customer engagement across different store zones and identify high-performing areas within the store.

<img width="1918" height="908" alt="image" src="https://github.com/user-attachments/assets/08f4b4f9-1c18-4592-932d-e2a3fa8428bf" />


---

### 🎯 Conversion Funnel

Track customer progression from store entry to purchase and identify conversion drop-off points.

<img width="1919" height="914" alt="image" src="https://github.com/user-attachments/assets/5d696ccb-264c-494f-9c8b-d2a754c3ba5c" />


---

### 🚨 Anomaly Detection

Automatically detect queue spikes, low-conversion events, traffic abnormalities, and operational bottlenecks.

<img width="1919" height="904" alt="image" src="https://github.com/user-attachments/assets/133dedd2-db63-4a59-b7e2-44dcecd548a3" />


---

### 📡 Live Event Stream

View structured retail events generated in real time from CCTV-derived customer interactions.

<img width="1919" height="907" alt="image" src="https://github.com/user-attachments/assets/433b0d43-0405-45d9-acd1-e7320aa24fe1" />


---

### ❤️ Health Monitoring API

Monitor platform health, feed freshness, event ingestion status, and system reliability.

<img width="1916" height="906" alt="image" src="https://github.com/user-attachments/assets/5e36df8d-6e2c-4350-8ec8-a6852b581821" />


<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 🎥 Demo Video

Watch the complete project demonstration here:

[▶️ StoreMind AI Demo Video](https://drive.google.com/file/d/17FG0DQ5SeKIQWjBvlc0zCBrLlLSAEcNx/view?usp=sharing)

This demo showcases:

- YOLOv8-based CCTV detection and tracking pipeline
- Real-time event generation and ingestion
- Store analytics and business intelligence APIs
- Live dashboard with Traffic Analytics
- Heatmap Visualization
- Conversion Funnel Analysis
- Event Stream Monitoring
- Anomaly Detection
- Multi-Store Intelligence Dashboard
- Health Monitoring APIs

The video demonstrates the complete end-to-end workflow from CCTV footage processing to actionable retail business insights.

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 🚀 Setup in 5 Commands

```bash
# 1 — Clone
git clone https://github.com/YOUR_USERNAME/store-intelligence.git
cd store-intelligence

# 2 — Python environment
python -m venv venv && venv\Scripts\activate      # Windows
pip install -r requirements.txt

# 3 — Start API (SQLite, zero config)
uvicorn app.main:app --port 8000 --reload

# 4 — Run detection pipeline (uses mock if no video)
python pipeline\detect.py --video __mock__ --store-id STORE_BLR_002 \
  --camera-id CAM_ENTRY_01 --layout data\store_layout.json \
  --output data\events\events.jsonl --clip-start 2026-03-03T09:00:00

python pipeline\ingest.py --events data\events\events.jsonl \
  --api http://localhost:8000

# 5 — Start dashboard
cd dashboard && npm install && npm run dev
```

> **Or use Docker (full stack):**
> ```bash
> docker compose up -d
> ```
> That's it. No manual steps.

<div align="center">

| Service | URL |
|---------|-----|
| 🧠 API | http://localhost:8000 |
| 📖 API Docs | http://localhost:8000/docs |
| 📊 Dashboard | http://localhost:3000 |
| ❤️ Health | http://localhost:8000/health |

</div>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 🎯 Event Schema

Every CCTV frame produces structured events — never raw pixels:

```json
{
  "event_id":   "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "store_id":   "STORE_BLR_002",
  "camera_id":  "CAM_ENTRY_01",
  "visitor_id": "VIS_c8a2f1",
  "event_type": "BILLING_QUEUE_JOIN",
  "timestamp":  "2026-03-03T14:22:10Z",
  "zone_id":    "BILLING",
  "dwell_ms":   0,
  "is_staff":   false,
  "confidence": 0.91,
  "metadata": {
    "queue_depth":  4,
    "sku_zone":     "BILLING",
    "session_seq":  5
  }
}
```

<details>
<summary><b>📋 Full Event Type Catalogue</b></summary>

| Event | When Emitted | Key Field |
|-------|-------------|-----------|
| `ENTRY` | Visitor crosses entry threshold inbound | Starts session |
| `EXIT` | Visitor crosses threshold outbound | Closes session |
| `ZONE_ENTER` | Visitor enters a named zone | `zone_id` |
| `ZONE_EXIT` | Visitor leaves a zone | `dwell_ms` |
| `ZONE_DWELL` | 30+ seconds continuous in zone | Every 30s |
| `BILLING_QUEUE_JOIN` | Enters billing while queue > 0 | `queue_depth` |
| `BILLING_QUEUE_ABANDON` | Leaves billing before purchase | POS correlation |
| `REENTRY` | Same visitor detected after EXIT | Re-ID match |

</details>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 📡 API Reference

<details>
<summary><b>POST /events/ingest</b> — Batch ingest up to 500 events</summary>

```bash
curl -X POST http://localhost:8000/events/ingest \
  -H "Content-Type: application/json" \
  -d '{"events": [{ ...event_schema... }]}'
```

```json
{
  "accepted": 474,
  "rejected": 0,
  "idempotent_skips": 0,
  "errors": []
}
```
✅ **Idempotent** — safe to call twice with the same payload

</details>

<details>
<summary><b>GET /stores/{id}/metrics</b> — Real-time store KPIs</summary>

```bash
curl http://localhost:8000/stores/STORE_BLR_002/metrics
```

```json
{
  "store_id": "STORE_BLR_002",
  "unique_visitors": 515,
  "conversion_rate": 0.342,
  "avg_dwell_per_zone": {
    "SKINCARE": 312.4,
    "MAKEUP": 189.2,
    "BILLING": 98.7
  },
  "queue_depth": 6,
  "abandonment_rate": 0.18,
  "data_confidence": "HIGH"
}
```

</details>

<details>
<summary><b>GET /stores/{id}/funnel</b> — Conversion funnel with drop-off</summary>

```json
{
  "funnel": [
    { "stage": "Entry",         "visitors": 515, "drop_off_pct": 0.0  },
    { "stage": "Zone Visit",    "visitors": 412, "drop_off_pct": 20.0 },
    { "stage": "Billing Queue", "visitors": 215, "drop_off_pct": 47.8 },
    { "stage": "Purchase",      "visitors": 176, "drop_off_pct": 18.1 }
  ],
  "overall_conversion_rate": 0.342,
  "reentry_events": 12,
  "unique_visitor_sessions": 515
}
```

</details>

<details>
<summary><b>GET /stores/{id}/anomalies</b> — Active anomalies with actions</summary>

```json
{
  "anomalies": [
    {
      "type": "BILLING_QUEUE_SPIKE",
      "severity": "CRITICAL",
      "title": "Billing queue depth: 6 customers",
      "suggested_action": "Open an additional billing counter immediately.",
      "detected_at": "2026-03-03T18:33:11Z"
    }
  ]
}
```

</details>

<details>
<summary><b>GET /health</b> — STALE_FEED detection per store</summary>

```json
{
  "status": "ok",
  "stores": [
    {
      "store_id": "STORE_BLR_002",
      "last_event_timestamp": "2026-03-03T18:33:11Z",
      "feed_status": "OK",
      "lag_minutes": 0.2
    }
  ],
  "total_events_ingested": 2337
}
```

</details>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 🧠 AI Engineering Decisions

Three key decisions — each evaluated with AI, each with documented reasoning:

<table>
<tr>
<th>Decision</th>
<th>AI Suggested</th>
<th>What I Chose</th>
<th>Why</th>
</tr>
<tr>
<td><b>Detection Model</b></td>
<td>RT-DETR</td>
<td>✅ YOLOv8n</td>
<td>CPU-runnable, graceful confidence degradation matches scoring rubric</td>
</tr>
<tr>
<td><b>Anomaly Detection</b></td>
<td>ARIMA forecasting</td>
<td>✅ Z-score + rules</td>
<td>ARIMA needs 4+ weeks data — clips are 20 minutes. Zero cold-start.</td>
</tr>
<tr>
<td><b>Session Schema</b></td>
<td>Reconstruction service</td>
<td>✅ Embedded session_seq</td>
<td>O(n) funnel query vs O(n×sessions) — 3× faster at 40 live stores</td>
</tr>
</table>

> Full reasoning in [`docs/DESIGN.md`](docs/DESIGN.md) and [`docs/CHOICES.md`](docs/CHOICES.md)

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 🧪 Tests

```bash
pytest tests/ -v
```

```
tests/test_api.py::TestSchemaValidation::test_valid_event_accepted          PASSED
tests/test_api.py::TestSchemaValidation::test_invalid_event_type_rejected   PASSED
tests/test_api.py::TestIdempotency::test_double_ingest_idempotent           PASSED
tests/test_api.py::TestStaffExclusion::test_staff_excluded_from_metrics     PASSED
tests/test_api.py::TestZeroTraffic::test_empty_store_metrics_not_crash      PASSED
tests/test_api.py::TestReentryDedup::test_reentry_does_not_double_count     PASSED
tests/test_api.py::TestAnomalyDetection::test_queue_spike_detected          PASSED
tests/test_api.py::TestHealth::test_stale_feed_flagged_on_old_events        PASSED
tests/test_pipeline.py::TestStoreEventSchema::test_event_ids_unique         PASSED
tests/test_pipeline.py::TestReIDEngine::test_reentry_detected_after_exit    PASSED
... 29 more

========================= 39 passed in 4.21s =========================
```

Edge cases covered: empty store · all-staff clip · zero purchases · re-entry · stale feed · partial batch failure

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 📁 Project Structure

```
store-intelligence/
│
├── 📂 pipeline/
│   ├── detect.py          # YOLOv8n + ByteTrack + Re-ID + event emission
│   ├── ingest.py          # Batch HTTP ingest to API (idempotent)
│   └── run.sh             # One command: all clips → events → API
│
├── 📂 app/
│   ├── main.py            # FastAPI entrypoint + trace_id middleware
│   ├── models.py          # Pydantic v2 event schema + validation
│   ├── database.py        # SQLAlchemy async ORM (SQLite / PostgreSQL)
│   └── routers/
│       ├── events.py      # POST /events/ingest
│       ├── metrics.py     # GET  /stores/{id}/metrics
│       ├── funnel.py      # GET  /stores/{id}/funnel
│       ├── heatmap.py     # GET  /stores/{id}/heatmap
│       ├── anomalies.py   # GET  /stores/{id}/anomalies
│       └── health.py      # GET  /health
│
├── 📂 dashboard/          # Next.js 14 live dashboard
│   └── src/app/
│       ├── page.tsx       # Main dashboard layout
│       ├── hooks/         # useApi, useLiveEvents (polling)
│       └── components/    # MetricsRow, TrafficChart, Heatmap,
│                          # FunnelChart, AnomalyPanel, EventStream
│
├── 📂 tests/
│   ├── test_api.py        # API tests (with AI prompt blocks)
│   └── test_pipeline.py   # Pipeline unit tests (with AI prompt blocks)
│
├── 📂 docs/
│   ├── DESIGN.md          # Architecture + AI-assisted decisions
│   └── CHOICES.md         # 3 key decisions with AI disagreements
│
├── 📂 data/
│   └── store_layout.json  # Zone polygon definitions per camera
│
├── docker-compose.yml     # API + PostgreSQL + Dashboard
├── requirements.txt
└── README.md
```

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 📊 Store Profiles (Live Data)

| Store | City | Visitors | Conv. Rate | Top Zone |
|-------|------|----------|-----------|----------|
| STORE_BLR_002 | Koramangala, Bangalore | 140 | 38% | Skincare |
| STORE_BLR_004 | Indiranagar, Bangalore | 95  | 31% | Haircare |
| STORE_MUM_001 | Bandra, Mumbai         | 210 | 42% | Makeup   |
| STORE_DEL_003 | Connaught Place, Delhi | 75  | 28% | Wellness |
| STORE_HYD_002 | Banjara Hills, Hyderabad | 120 | 35% | Fragrance |

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 🛠️ Tech Stack

<div align="center">

| Layer | Technology |
|-------|-----------|
| **Computer Vision** | YOLOv8n · ByteTrack · OpenCV · Custom Re-ID |
| **Backend API** | FastAPI · Pydantic v2 · SQLAlchemy async · Uvicorn |
| **Database** | SQLite (dev) · PostgreSQL (prod) |
| **Frontend** | Next.js 14 · Tailwind CSS · Recharts · Framer Motion |
| **Infrastructure** | Docker · Docker Compose |
| **Testing** | pytest · pytest-asyncio · httpx |
| **Observability** | Structured JSON logs · trace_id · /health endpoint |

</div>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

## 🏆 About the Developer

<div align="center">

**Gyana Ranjan Sahoo**
B.Tech CSE · C.V. Raman Global University · CGPA 8.94

<p>
  <img src="https://img.shields.io/badge/Infosys%20Global%20Hackathon%202025-National%20Second%20Runner--Up%20🥉-FF6B35?style=for-the-badge"/>
</p>
<p>
  <img src="https://img.shields.io/badge/TCS%20CodeVita%20Season%2013-Global%20Top%202%25%20(Rank%201025)-1A4A8A?style=for-the-badge"/>
</p>

<a href="mailto:gyanaranjansahoo0033@gmail.com">
  <img src="https://img.shields.io/badge/Email-gyanaranjansahoo0033%40gmail.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white"/>
</a>

</div>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" width="100%">

<div align="center">

<!-- Footer wave -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:3A7FD5,50:1A4A8A,100:0A0F2C&height=120&section=footer&text=Built%20for%20Purplle%20Tech%20Challenge%202026&fontSize=16&fontColor=6AABFF&fontAlignY=65&animation=fadeIn" width="100%"/>

</div>
