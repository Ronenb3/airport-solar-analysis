"""
Compare & aggregate endpoints.
"""

import logging
import re

from fastapi import APIRouter, Query, HTTPException

from services import calc_solar, calc_totals
from services.data_loader import load_airports, get_buildings_for_airport

router = APIRouter(prefix="/api", tags=["compare"])
logger = logging.getLogger(__name__)


@router.get("/compare")
def compare_airports(
    codes: str = Query(..., description="Comma-separated airport codes"),
    radius: float = Query(5, ge=1, le=15),
    min_size: float = Query(500, ge=100, le=10000),
    usable_pct: float = Query(0.65, ge=0.3, le=0.8),
    panel_eff: float = Query(200, ge=150, le=250),
    elec_price: float = Query(0.12, ge=0.05, le=0.25),
    include_itc: bool = Query(True),
    rate_escalation: float = Query(0.02, ge=0.0, le=0.05),
    financing: str = Query("cash"),
):
    """Compare multiple airports."""
    airport_codes = [c.strip().upper() for c in codes.split(",")[:8] if c.strip() and re.match(r'^[A-Za-z]{3,4}$', c.strip())]
    if not airport_codes:
        raise HTTPException(status_code=400, detail="No valid airport codes provided")
    airports_list = load_airports()
    results = []

    for code in airport_codes[:8]:  # max 8
        airport = next((a for a in airports_list if a["code"] == code), None)
        if not airport:
            results.append({"code": code, "error": f"Airport {code} not found"})
            continue
        try:
            buildings, error = get_buildings_for_airport(airport, radius, min_size)
            if error or not buildings:
                results.append({"code": code, "airport": airport, "error": error or "No buildings"})
                continue
            totals = calc_totals(
                buildings, airport["state"], usable_pct, panel_eff, elec_price,
                include_itc=include_itc,
                rate_escalation=rate_escalation,
                financing=financing if financing in ("cash", "loan") else "cash",
            )
            results.append({
                "code": code,
                "airport": airport,
                "totals": totals,
                "building_count": len(buildings),
            })
        except Exception as e:
            logger.warning(f"Compare: failed for {code}: {e}")
            results.append({"code": code, "error": f"Data not available for {code}"})

    return {
        "airports": results,
        "parameters": {
            "radius_km": radius,
            "min_size_m2": min_size,
            "usable_pct": usable_pct,
            "panel_eff": panel_eff,
            "elec_price": elec_price,
            "include_itc": include_itc,
        },
    }


@router.get("/aggregate")
def aggregate_all(
    radius: float = Query(5, ge=1, le=15),
    min_size: float = Query(500, ge=100, le=10000),
    usable_pct: float = Query(0.65, ge=0.3, le=0.8),
    panel_eff: float = Query(200, ge=150, le=250),
    elec_price: float = Query(0.12, ge=0.05, le=0.25),
    include_itc: bool = Query(True),
    rate_escalation: float = Query(0.02, ge=0.0, le=0.05),
    financing: str = Query("cash"),
):
    """Aggregate data for all airports."""
    airports_list = load_airports()
    results = []
    total_buildings = 0
    total_capacity_mw = 0.0
    total_energy_mwh = 0.0
    total_revenue = 0.0
    total_co2 = 0.0

    for airport in airports_list:
        try:
            buildings, _ = get_buildings_for_airport(airport, radius, min_size)
            if not buildings:
                continue
            totals = calc_totals(
                buildings, airport["state"], usable_pct, panel_eff, elec_price,
                include_itc=include_itc,
                rate_escalation=rate_escalation,
                financing=financing if financing in ("cash", "loan") else "cash",
            )
            results.append({
                "code": airport["code"],
                "name": airport["name"],
                "state": airport["state"],
                "buildings": len(buildings),
                "capacity_mw": totals["capacity_mw"],
                "annual_mwh": totals["annual_mwh"],
                "annual_revenue": totals["annual_revenue"],
                "co2_avoided_tons": totals["co2_avoided_tons"],
                "payback_years": totals["payback_years"],
                "npv_25yr": totals["npv_25yr"],
            })
            total_buildings += len(buildings)
            total_capacity_mw += totals["capacity_mw"]
            total_energy_mwh += totals["annual_mwh"]
            total_revenue += totals["annual_revenue"]
            total_co2 += totals["co2_avoided_tons"]
        except Exception as e:
            logger.warning(f"Aggregate: failed for {airport['code']}: {e}")

    results.sort(key=lambda x: x["annual_mwh"], reverse=True)

    return {
        "airports": results,
        "totals": {
            "airport_count": len(results),
            "building_count": total_buildings,
            "capacity_mw": round(total_capacity_mw, 1),
            "annual_mwh": round(total_energy_mwh, 0),
            "annual_revenue": round(total_revenue, 0),
            "co2_avoided_tons": round(total_co2, 0),
            "homes_powered": int(total_energy_mwh * 1000 / 10500),
        },
    }
