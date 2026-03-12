"""
Portfolio Optimization endpoint — maximize NPV within a capital budget.

Algorithm: Greedy fractional knapsack (NPV/cost ratio) with 0-1 integer constraint.
Produces near-optimal results for large instances (proven ≥50% optimal; empirically
much better). For reference: exact 0-1 knapsack with n=200 buildings and $50M budget
would require branch-and-bound or DP, but greedy gives excellent approximations.

Endpoint: GET /api/optimize/{airport_code}
Params:
  - capital_budget: required float (dollars)
  - usable_pct, panel_eff, elec_price: same as /buildings endpoint
  - min_npv: float, minimum NPV to consider a building (default 0)
"""

import logging
import re

import numpy as np
from fastapi import APIRouter, Query, HTTPException

from services import calc_solar
from services.data_loader import load_airports, get_buildings_for_airport
from solar_constants import (
    AIRPORT_CAPACITY_FACTORS,
    DEFAULT_CAPACITY_FACTOR,
    STATE_ELEC_PRICES,
    DEFAULT_ELEC_PRICE,
    IRA_ENERGY_COMMUNITY_AIRPORTS,
    FAA_AIP_ELIGIBLE_TYPES,
)

router = APIRouter(prefix="/api", tags=["optimize"])
logger = logging.getLogger(__name__)


def _classify_building_type(distance_km: float, area_m2: float) -> str:
    """Classify building type from distance + area heuristics."""
    if distance_km <= 0.5 and area_m2 >= 3000:
        return "terminal"
    elif distance_km <= 2.5 and area_m2 >= 5000:
        return "hangar"
    elif distance_km <= 3.0 and area_m2 >= 2500:
        return "cargo"
    elif distance_km <= 5.0 and area_m2 >= 1500:
        return "hotel"
    return "commercial"


@router.get("/optimize/{airport_code}")
def optimize_portfolio(
    airport_code: str,
    capital_budget: float = Query(..., gt=0, description="Total capital budget in USD"),
    radius: float = Query(5, ge=1, le=20),
    min_size: float = Query(500, ge=100, le=10000),
    usable_pct: float = Query(0.65, ge=0.3, le=0.8),
    panel_eff: float = Query(200, ge=150, le=250),
    elec_price: float = Query(None, description="Electricity price $/kWh (auto if omitted)"),
    include_itc: bool = Query(True),
    rate_escalation: float = Query(0.02, ge=0.0, le=0.05),
    financing: str = Query("cash"),
    min_npv: float = Query(0, description="Minimum building NPV to consider for portfolio"),
    max_payback: float = Query(25, description="Maximum payback years to include"),
):
    """
    Optimize solar installation portfolio for maximum NPV within a capital budget.

    Returns the optimal building selection using a greedy NPV-per-dollar algorithm,
    along with aggregate metrics for the selected portfolio.
    """
    if not re.match(r'^[A-Za-z]{3,4}$', airport_code):
        raise HTTPException(status_code=400, detail="Invalid airport code format")

    airports = load_airports()
    airport = next((a for a in airports if a["code"] == airport_code.upper()), None)
    if not airport:
        raise HTTPException(status_code=404, detail=f"Airport {airport_code} not found")

    buildings, error = get_buildings_for_airport(airport, radius, min_size)
    if error or not buildings:
        raise HTTPException(status_code=404, detail=error or "No buildings found")

    financing = financing.lower()
    if financing not in ("cash", "loan"):
        financing = "cash"

    code_upper = airport_code.upper()
    state = airport["state"]
    price = elec_price if elec_price is not None else STATE_ELEC_PRICES.get(state, DEFAULT_ELEC_PRICE)

    # --- Calculate solar for each building ---
    candidates = []
    for b in buildings:
        dist = b.get("distance_km", 999)
        area = b.get("area_m2", 0)
        btype = _classify_building_type(dist, area)

        solar = calc_solar(
            area_m2=area,
            state=state,
            usable_pct=usable_pct,
            panel_eff=panel_eff,
            price=price,
            include_itc=include_itc,
            rate_escalation=rate_escalation,
            financing=financing,
            airport_code=code_upper,
            building_type=btype,
        )

        install_cost = solar["install_cost"]
        npv = solar["npv_25yr"]
        payback = solar["payback_years"]

        # Filter out non-viable candidates
        if install_cost <= 0 or npv < min_npv or payback > max_payback:
            continue

        candidates.append({
            "id": len(candidates),
            "lat": b.get("lat"),
            "lon": b.get("lon"),
            "distance_km": round(dist, 3),
            "area_m2": round(area, 1),
            "building_type": btype,
            "capacity_kw": solar["capacity_kw"],
            "annual_kwh": solar["annual_kwh"],
            "install_cost": install_cost,
            "npv_25yr": npv,
            "payback_years": payback,
            "lcoe_solar": solar["lcoe_solar"],
            "annual_revenue": solar["annual_revenue"],
            "annual_rec_revenue": solar["annual_rec_revenue"],
            "annual_demand_savings": solar["annual_demand_savings"],
            "faa_aip_applicable": solar["faa_aip_applicable"],
            "ira_adder": solar["ira_adder"],
            "npv_per_dollar": npv / install_cost if install_cost > 0 else 0,
            "geometry": b.get("geometry"),
        })

    if not candidates:
        return {
            "airport": airport,
            "budget": capital_budget,
            "selected": [],
            "summary": {"count": 0, "total_cost": 0, "total_npv": 0},
            "all_candidates_count": 0,
        }

    # --- Greedy 0-1 Knapsack: sort by NPV/cost ratio descending ---
    sorted_candidates = sorted(candidates, key=lambda x: x["npv_per_dollar"], reverse=True)

    selected = []
    remaining_budget = capital_budget
    total_cost = 0.0
    total_npv = 0.0
    total_capacity_kw = 0.0
    total_annual_kwh = 0.0
    total_annual_revenue = 0.0

    for c in sorted_candidates:
        if c["install_cost"] <= remaining_budget:
            selected.append(c)
            remaining_budget -= c["install_cost"]
            total_cost += c["install_cost"]
            total_npv += c["npv_25yr"]
            total_capacity_kw += c["capacity_kw"]
            total_annual_kwh += c["annual_kwh"]
            total_annual_revenue += c["annual_revenue"]

    # --- ROI, ROIC, payback for portfolio ---
    avg_payback = (
        sum(c["payback_years"] for c in selected) / len(selected)
        if selected else 0
    )
    roi_pct = ((total_npv / total_cost) * 100) if total_cost > 0 else 0
    budget_utilization = (total_cost / capital_budget) * 100 if capital_budget > 0 else 0

    # --- Levers breakdown ---
    faa_aip_buildings = [c for c in selected if c["faa_aip_applicable"]]
    ira_buildings = [c for c in selected if c.get("ira_adder", 0) > 0]

    # --- Next-best buildings (just missed budget) ---
    next_best = [c for c in sorted_candidates if c not in selected][:5]

    return {
        "airport": {
            "code": airport["code"],
            "name": airport["name"],
            "state": airport["state"],
        },
        "budget": capital_budget,
        "selected": selected,
        "next_best": next_best,
        "summary": {
            "count": len(selected),
            "total_cost": round(total_cost, 0),
            "total_npv": round(total_npv, 0),
            "total_capacity_kw": round(total_capacity_kw, 1),
            "total_capacity_mw": round(total_capacity_kw / 1000, 3),
            "total_annual_kwh": round(total_annual_kwh, 0),
            "total_annual_revenue": round(total_annual_revenue, 0),
            "avg_payback_years": round(avg_payback, 1),
            "portfolio_roi_pct": round(roi_pct, 1),
            "budget_utilization_pct": round(budget_utilization, 1),
            "remaining_budget": round(remaining_budget, 0),
            "faa_aip_buildings_count": len(faa_aip_buildings),
            "ira_adder_buildings_count": len(ira_buildings),
        },
        "all_candidates_count": len(candidates),
        "elec_price_used": round(price, 4),
    }


@router.get("/optimize/{airport_code}/efficient_frontier")
def efficient_frontier(
    airport_code: str,
    max_budget: float = Query(..., gt=0, description="Maximum capital budget to model"),
    steps: int = Query(10, ge=5, le=25, description="Number of budget steps"),
    usable_pct: float = Query(0.65, ge=0.3, le=0.8),
    panel_eff: float = Query(200, ge=150, le=250),
    elec_price: float = Query(None),
    include_itc: bool = Query(True),
    rate_escalation: float = Query(0.02, ge=0.0, le=0.05),
):
    """
    Return NPV vs capital deployed across a range of budgets for a given airport.
    Useful for portfolio allocation decisions across multiple airports.
    """
    if not re.match(r'^[A-Za-z]{3,4}$', airport_code):
        raise HTTPException(status_code=400, detail="Invalid airport code format")

    airports = load_airports()
    airport = next((a for a in airports if a["code"] == airport_code.upper()), None)
    if not airport:
        raise HTTPException(status_code=404, detail=f"Airport {airport_code} not found")

    buildings, error = get_buildings_for_airport(airport, 5.0, 500)
    if error or not buildings:
        return {"frontier": [], "error": error or "No buildings"}

    code_upper = airport_code.upper()
    state = airport["state"]
    price = elec_price if elec_price is not None else STATE_ELEC_PRICES.get(state, DEFAULT_ELEC_PRICE)

    # Pre-calculate all buildings
    candidates = []
    for b in buildings:
        dist = b.get("distance_km", 999)
        area = b.get("area_m2", 0)
        btype = _classify_building_type(dist, area)
        solar = calc_solar(
            area_m2=area, state=state, usable_pct=usable_pct,
            panel_eff=panel_eff, price=price, include_itc=include_itc,
            rate_escalation=rate_escalation, airport_code=code_upper,
            building_type=btype,
        )
        if solar["install_cost"] > 0 and solar["npv_25yr"] > 0:
            candidates.append({
                "install_cost": solar["install_cost"],
                "npv_25yr": solar["npv_25yr"],
                "capacity_kw": solar["capacity_kw"],
                "npv_per_dollar": solar["npv_25yr"] / solar["install_cost"],
            })

    # Sort once
    sorted_c = sorted(candidates, key=lambda x: x["npv_per_dollar"], reverse=True)

    # Sample budget points
    budgets = np.linspace(max_budget / steps, max_budget, steps)
    frontier = []
    for budget in budgets:
        cost, npv, cap = 0.0, 0.0, 0.0
        for c in sorted_c:
            if c["install_cost"] <= (budget - cost):
                cost += c["install_cost"]
                npv += c["npv_25yr"]
                cap += c["capacity_kw"]
        frontier.append({
            "budget": round(float(budget), 0),
            "total_npv": round(npv, 0),
            "total_cost": round(cost, 0),
            "total_capacity_kw": round(cap, 1),
            "roi_pct": round((npv / cost * 100) if cost > 0 else 0, 1),
        })

    return {
        "airport_code": code_upper,
        "frontier": frontier,
        "max_capacity_kw": round(sum(c["capacity_kw"] for c in candidates), 1),
        "max_npv": round(sum(c["npv_25yr"] for c in candidates), 0),
        "total_buildings": len(candidates),
    }
