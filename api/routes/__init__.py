"""
Health, status, and readiness endpoints.
"""

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

DATA_DIR = Path(__file__).parent.parent.parent / "data"
AIRPORTS_FILE = DATA_DIR / "airports" / "top_30_airports.csv"
APP_VERSION = "2.0.0"
_start_time = datetime.now(timezone.utc)


@router.api_route("/health", methods=["GET", "HEAD"])
@router.api_route("/api/health", methods=["GET", "HEAD"])
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/api/status")
async def status(request: Request):
    uptime = (datetime.now(timezone.utc) - _start_time).total_seconds()
    requests_handled = getattr(request.app.state, "request_count", 0)
    cache_v2_dir = DATA_DIR / "airport_cache_v2"
    cached_airports = len(list(cache_v2_dir.glob("*.json"))) if cache_v2_dir.exists() else 0

    return {
        "status": "operational",
        "version": APP_VERSION,
        "uptime_seconds": round(uptime, 2),
        "start_time": _start_time.isoformat(),
        "requests_handled": requests_handled,
        "data": {
            "airports_file_exists": AIRPORTS_FILE.exists(),
            "cached_airports": cached_airports,
        },
        "_debug": {
            "data_dir": str(DATA_DIR),
            "data_dir_exists": DATA_DIR.exists(),
            "airports_file": str(AIRPORTS_FILE),
            "cache_v2_dir": str(cache_v2_dir),
            "cache_v2_exists": cache_v2_dir.exists(),
            "env_DATA_DIR": __import__("os").environ.get("DATA_DIR", "(not set)"),
        },
    }


@router.get("/api/ready")
async def readiness():
    if not AIRPORTS_FILE.exists():
        raise HTTPException(status_code=503, detail="Airports data file not found")
    cache_v2_dir = DATA_DIR / "airport_cache_v2"
    if not cache_v2_dir.exists() or len(list(cache_v2_dir.glob("*.json"))) == 0:
        raise HTTPException(status_code=503, detail="No cached airport data available")
    return {"status": "ready", "timestamp": datetime.now(timezone.utc).isoformat()}
