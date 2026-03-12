"""
Airport Solar Analyzer — FastAPI Backend v2.0
Modular architecture with unified solar constants, ITC/NPV modeling,
and state-specific CO₂ emissions data.
"""

import logging
import sys

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from logger import setup_logging
from middleware import RateLimitMiddleware, TimingMiddleware, SecurityHeadersMiddleware
from routes import router as health_router
from routes.airports import router as airports_router
from routes.buildings import router as buildings_router
from routes.compare import router as compare_router
from routes.optimize import router as optimize_router
from services.data_loader import DATA_DIR, AIRPORTS_FILE

# Setup logging
logger = setup_logging(settings.LOG_LEVEL, str(settings.log_path))
logger.info("Starting Airport Solar Analyzer API v2.0.0")

# Create FastAPI app
app = FastAPI(
    title="Airport Solar Analyzer API",
    version="2.0.0",
    description="High-performance API for analyzing rooftop solar potential near airports",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ---------- Middleware (order matters — first added = last executed) ----------
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TimingMiddleware)

if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_window=settings.RATE_LIMIT_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW,
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Register routers ----------
app.include_router(health_router)
app.include_router(airports_router)
app.include_router(buildings_router)
app.include_router(compare_router)
app.include_router(optimize_router)


# ---------- Lifecycle ----------
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 80)
    logger.info("Airport Solar Analyzer API v2.0 Starting")
    logger.info(f"Data directory: {DATA_DIR}")

    if not AIRPORTS_FILE.exists():
        logger.error(f"CRITICAL: Airports file not found at {AIRPORTS_FILE}")
    else:
        airports = pd.read_csv(AIRPORTS_FILE)
        logger.info(f"Loaded {len(airports)} airports")

    cache_v2_dir = DATA_DIR / "airport_cache_v2"
    if cache_v2_dir.exists():
        cached = len(list(cache_v2_dir.glob("*.json")))
        logger.info(f"Found {cached} cached airports (v2)")
    else:
        logger.warning("Cache directory not found — performance will be degraded")
    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    requests_handled = getattr(app.state, "request_count", 0)
    logger.info(f"Shutting down. Total requests: {requests_handled}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
