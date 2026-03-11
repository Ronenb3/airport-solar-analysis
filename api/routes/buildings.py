"""
Building data endpoint — single airport with solar calculations.
"""

import logging
import re

from fastapi import APIRouter, Query, HTTPException

from services import calc_solar, calc_totals
from services.data_loader import load_airports, get_buildings_for_airport
from solar_constants import (
    STATE_ELEC_PRICES,
    DEFAULT_ELEC_PRICE,
    STATE_NET_METERING,
    DEFAULT_NET_METERING,
    GLARE_RISK_THRESHOLDS,
)

router = APIRouter(prefix="/api", tags=["buildings"])
logger = logging.getLogger(__name__)


@router.get("/buildings/{airport_code}")
def get_buildings(
    airport_code: str,
    radius: float = Query(5, ge=1, le=20, description="Search radius in km"),
    min_size: float = Query(500, ge=100, le=10000, description="Minimum building size m²"),
    usable_pct: float = Query(0.65, ge=0.3, le=0.8, description="Usable roof percentage"),
    panel_eff: float = Query(200, ge=150, le=250, description="Panel efficiency W/m²"),
    elec_price: float = Query(0.12, ge=0.05, le=0.25, description="Electricity price $/kWh"),
    include_itc: bool = Query(True, description="Include 30% federal ITC"),
    rate_escalation: float = Query(0.02, ge=0.0, le=0.05, description="Annual electricity price escalation rate"),
    financing: str = Query("cash", description="Financing mode: cash or loan"),
):
    """Get buildings near an airport with solar calculations."""
    # Validate airport code format (defense-in-depth against path traversal)
    if not re.match(r'^[A-Za-z]{3,4}$', airport_code):
        raise HTTPException(status_code=400, detail="Invalid airport code format")

    airports = load_airports()
    airport = next((a for a in airports if a["code"] == airport_code.upper()), None)
    if not airport:
        raise HTTPException(status_code=404, detail=f"Airport {airport_code} not found")

    buildings, error = get_buildings_for_airport(airport, radius, min_size)

    if error:
        raise HTTPException(status_code=404, detail=error)
    if not buildings:
        return {
            "airport": airport,
            "buildings": [],
            "totals": None,
            "error": "No buildings found",
        }

    # Validate financing param
    financing = financing.lower()
    if financing not in ("cash", "loan"):
        financing = "cash"

    # Solar calcs per building + FAA glare risk
    for b in buildings:
        b["solar"] = calc_solar(
            b["area_m2"], airport["state"], usable_pct, panel_eff, elec_price,
            include_itc=include_itc,
            rate_escalation=rate_escalation,
            financing=financing,
        )
        # FAA solar glare risk based on distance to airport center
        dist = b.get("distance_km", 999)
        if dist <= GLARE_RISK_THRESHOLDS["high"]:
            b["glare_risk"] = "high"
        elif dist <= GLARE_RISK_THRESHOLDS["moderate"]:
            b["glare_risk"] = "moderate"
        else:
            b["glare_risk"] = "low"

    # Aggregate totals
    totals = calc_totals(
        buildings, airport["state"], usable_pct, panel_eff, elec_price,
        include_itc=include_itc,
        rate_escalation=rate_escalation,
        financing=financing,
    )

    # State-level metadata
    state = airport["state"]
    state_meta = {
        "elec_price": STATE_ELEC_PRICES.get(state, DEFAULT_ELEC_PRICE),
        "net_metering": STATE_NET_METERING.get(state, DEFAULT_NET_METERING),
    }

    return {
        "airport": airport,
        "buildings": buildings,
        "totals": totals,
        "state_context": state_meta,
        "parameters": {
            "radius_km": radius,
            "min_size_m2": min_size,
            "usable_pct": usable_pct,
            "panel_eff": panel_eff,
            "elec_price": elec_price,
            "include_itc": include_itc,
            "rate_escalation": rate_escalation,
            "financing": financing,
        },
    }
