"""
StoreMind AI — Intelligence API
FastAPI entrypoint with structured logging, trace IDs, and graceful degradation.
"""

import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import init_db, get_db_status
from app.routers import events, metrics, funnel, heatmap, anomalies, health

# ---------------------------------------------------------------------------
# Structured logger
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger("storemind.api")


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("StoreMind API starting — initialising database")
    try:
        await init_db()
        logger.info("Database ready")
    except Exception as e:
        logger.error(f"Database init failed: {e}")
    yield
    logger.info("StoreMind API shutting down")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="StoreMind Intelligence API",
    version="1.0.0",
    description="Real-time store analytics from CCTV footage",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request logging middleware — trace_id per request
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    trace_id = str(uuid.uuid4())[:8]
    request.state.trace_id = trace_id
    start = time.time()

    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(
            f"trace_id={trace_id} method={request.method} path={request.url.path} "
            f"error={exc}"
        )
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "trace_id": trace_id},
        )

    latency_ms = round((time.time() - start) * 1000, 1)
    store_id = request.path_params.get("store_id", "-")
    logger.info(
        f"trace_id={trace_id} method={request.method} path={request.url.path} "
        f"store_id={store_id} status={response.status_code} latency_ms={latency_ms}"
    )
    response.headers["X-Trace-Id"] = trace_id
    return response


# ---------------------------------------------------------------------------
# Graceful degradation — DB health check on startup
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", "unknown")
    logger.error(f"Unhandled exception trace_id={trace_id}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=503,
        content={
            "error": "Service temporarily unavailable",
            "trace_id": trace_id,
            "hint": "Check /health for service status",
        },
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(events.router, prefix="/events", tags=["Events"])
app.include_router(metrics.router, prefix="/stores", tags=["Metrics"])
app.include_router(funnel.router, prefix="/stores", tags=["Funnel"])
app.include_router(heatmap.router, prefix="/stores", tags=["Heatmap"])
app.include_router(anomalies.router, prefix="/stores", tags=["Anomalies"])
app.include_router(health.router, tags=["Health"])


@app.get("/")
async def root():
    return {
        "service": "StoreMind Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
