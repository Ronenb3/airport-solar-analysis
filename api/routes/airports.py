"""
Airport list and capacity factor endpoints.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from services.data_loader import load_airports
from solar_constants import (
    CAPACITY_FACTORS,
    STATE_ELEC_PRICES,
    DEFAULT_ELEC_PRICE,
    STATE_NET_METERING,
    DEFAULT_NET_METERING,
    STATE_CO2_RATES,
    GRID_CO2_KG_PER_KWH,
    GLARE_RISK_THRESHOLDS,
)

router = APIRouter(prefix="/api", tags=["airports"])


@router.get("/airports")
def get_airports():
    """Get list of all airports with state-level metadata."""
    airports = load_airports()
    for a in airports:
        state = a.get("state", "")
        a["elec_price"] = STATE_ELEC_PRICES.get(state, DEFAULT_ELEC_PRICE)
        a["net_metering"] = STATE_NET_METERING.get(state, DEFAULT_NET_METERING)
        a["capacity_factor"] = CAPACITY_FACTORS.get(state, 0.158)
        a["co2_rate"] = STATE_CO2_RATES.get(state, GRID_CO2_KG_PER_KWH)
        a["glare_thresholds"] = GLARE_RISK_THRESHOLDS
    return airports


@router.get("/capacity-factors")
def get_capacity_factors():
    """Get capacity factors by state (from NREL 2023 ATB)."""
    return JSONResponse(
        content=CAPACITY_FACTORS,
        headers={"Cache-Control": "public, max-age=86400"},
    )
