"""
Building data endpoint — single airport with solar calculations.
"""

import logging
import re

from fastapi import APIRouter, Query, HTTPException

from services import calc_solar, calc_totals
from services.data_loader import load_airports, get_buildings_for_airport
from services.glare import calc_glare_risk, classify_glare_risk_fast
from solar_constants import (
    STATE_ELEC_PRICES,
    DEFAULT_ELEC_PRICE,
    STATE_NET_METERING,
    DEFAULT_NET_METERING,
    GLARE_RISK_THRESHOLDS,
    AIRPORT_CAPACITY_FACTORS,
    DEFAULT_CAPACITY_FACTOR,
    RUNWAY_HEADINGS,
    AIRPORT_COORDS,
    SPLIT_INCENTIVE_BY_TYPE,
    GRANT_PROGRAMS_BY_TYPE,
    FAA_AIP_ELIGIBLE_TYPES,
    IRA_ENERGY_COMMUNITY_AIRPORTS,
    IRA_ENERGY_COMMUNITY_ADDER,
    REC_PRICES_PER_MWH,
    DEFAULT_REC_PRICE_PER_MWH,
    LCFS_AIRPORTS,
)

router = APIRouter(prefix="/api", tags=["buildings"])
logger = logging.getLogger(__name__)

# Pvlib glare calc is expensive — only run for buildings within this radius
PVLIB_GLARE_RADIUS_KM = 3.0


def _classify_building_type(distance_km: float, area_m2: float) -> str:
    """Classify building type based on distance from airport center and footprint area."""
    if distance_km <= 0.5 and area_m2 >= 3000:
        return "terminal"
    elif distance_km <= 2.5 and area_m2 >= 5000:
        return "hangar"
    elif distance_km <= 3.0 and area_m2 >= 2500:
        return "cargo"
    elif distance_km <= 5.0 and area_m2 >= 1500:
        return "hotel"
    return "commercial"


@router.get("/buildings-test/{airport_code}")
def get_buildings_test(airport_code: str):
    """Lightweight endpoint: load data only, no solar calculations. For debugging."""
    import traceback
    try:
        airports = load_airports()
        airport = next((a for a in airports if a["code"] == airport_code.upper()), None)
        if not airport:
            return {"ok": False, "error": f"Airport {airport_code} not found"}
        buildings, error = get_buildings_for_airport(airport, 5.0, 500.0)
        return {
            "ok": True,
            "airport": airport,
            "building_count": len(buildings) if buildings else 0,
            "error": error,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "trace": traceback.format_exc()[-2000:]}


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

    try:
        buildings, error = get_buildings_for_airport(airport, radius, min_size)
    except Exception as exc:
        logger.exception(f"get_buildings_for_airport failed for {airport_code}")
        raise HTTPException(status_code=500, detail=f"data load: {exc}")

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

    # Solar calcs per building — using per-airport PVWatts capacity factors,
    # simplified inter-building shading, building type classification,
    # and pvlib-based FAA glare analysis for buildings within 3km.
    code_upper = airport_code.upper()
    runways_tuple = tuple(RUNWAY_HEADINGS.get(code_upper, []))
    ap_coords = AIRPORT_COORDS.get(code_upper)
    ira_community = code_upper in IRA_ENERGY_COMMUNITY_AIRPORTS
    rec_price = REC_PRICES_PER_MWH.get(airport["state"], DEFAULT_REC_PRICE_PER_MWH)

    try:
        for b in buildings:
            # Simplified shading: if a neighbor within 80m has area > 3x this building
            # it's likely taller and may partially shade morning/evening sun
            shading_factor = 1.0
            b_lat = b.get("lat", 0)
            b_lon = b.get("lon", 0)
            b_area = b.get("area_m2", 1)
            dist = b.get("distance_km", 999)
            large_neighbors = sum(
                1 for other in buildings
                if other is not b
                and ((other.get("lat", 0) - b_lat) * 111000) ** 2
                   + ((other.get("lon", 0) - b_lon) * 111000 * 0.85) ** 2 < 80 ** 2
                and other.get("area_m2", 0) > b_area * 3
            )
            if large_neighbors >= 3:
                shading_factor = 0.93
            elif large_neighbors >= 1:
                shading_factor = 0.97

            # Building type classification
            btype = _classify_building_type(dist, b_area)

            b["solar"] = calc_solar(
                b["area_m2"], airport["state"], usable_pct, panel_eff, elec_price,
                include_itc=include_itc,
                rate_escalation=rate_escalation,
                financing=financing,
                airport_code=code_upper,
                shading_factor=shading_factor,
                building_type=btype,
            )
            if shading_factor < 1.0:
                b["shading_factor"] = round(shading_factor, 2)

            # Building metadata
            b["building_type"] = btype
            b["split_incentive"] = SPLIT_INCENTIVE_BY_TYPE.get(btype, "medium")
            b["grant_programs"] = GRANT_PROGRAMS_BY_TYPE.get(btype, [])
            b["faa_aip_eligible"] = btype in FAA_AIP_ELIGIBLE_TYPES
            b["ira_energy_community"] = ira_community
            b["ira_adder_pct"] = int(IRA_ENERGY_COMMUNITY_ADDER * 100) if ira_community else 0

            # Carbon credit info
            b["rec_price_per_mwh"] = round(rec_price, 2)
            b["lcfs_eligible"] = code_upper in LCFS_AIRPORTS

            # FAA glare risk — use pvlib for close buildings, distance heuristic otherwise
            if dist <= PVLIB_GLARE_RADIUS_KM and runways_tuple and ap_coords:
                try:
                    glare = calc_glare_risk(
                        airport_code=code_upper,
                        lat=b_lat,
                        lon=b_lon,
                        runways=runways_tuple,
                    )
                    b["glare_risk"] = glare["risk_level"]
                    b["glare_hours_per_year"] = glare.get("glare_hours_per_year", 0)
                    b["glare_worst_months"] = glare.get("worst_months", [])
                    b["glare_description"] = glare.get("description", "")
                    b["glare_method"] = "pvlib_specular"
                except Exception as exc:
                    logger.warning(f"pvlib glare error for {code_upper}: {exc}")
                    b["glare_risk"] = classify_glare_risk_fast(dist)
                    b["glare_method"] = "distance_fallback"
            else:
                b["glare_risk"] = classify_glare_risk_fast(dist)
                b["glare_hours_per_year"] = None
                b["glare_method"] = "distance_heuristic"
    except Exception as exc:
        logger.exception(f"building loop failed for {airport_code}")
        raise HTTPException(status_code=500, detail=f"building calculation: {exc}")

    try:
        # Aggregate totals
        totals = calc_totals(
            buildings, airport["state"], usable_pct, panel_eff, elec_price,
            include_itc=include_itc,
            rate_escalation=rate_escalation,
            financing=financing,
            airport_code=code_upper,
        )
    except Exception as exc:
        logger.exception(f"calc_totals failed for {airport_code}")
        raise HTTPException(status_code=500, detail=f"calc_totals: {exc}")

    # State-level metadata
    state = airport["state"]
    state_meta = {
        "elec_price": STATE_ELEC_PRICES.get(state, DEFAULT_ELEC_PRICE),
        "net_metering": STATE_NET_METERING.get(state, DEFAULT_NET_METERING),
        "rec_price_per_mwh": REC_PRICES_PER_MWH.get(state, DEFAULT_REC_PRICE_PER_MWH),
        "lcfs_eligible": code_upper in LCFS_AIRPORTS,
        "ira_energy_community": ira_community,
        "ira_adder_pct": int(IRA_ENERGY_COMMUNITY_ADDER * 100) if ira_community else 0,
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
