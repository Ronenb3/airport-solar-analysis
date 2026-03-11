"""
Solar calculation service — unified calculations for all endpoints.
Uses shared constants from solar_constants.py.

Inspired by professional-grade LCOE (Levelized Cost of Energy) modeling:
- Year-by-year grid vs solar cost comparison
- Electricity rate escalation (grid prices rise ~2%/year)
- Inverter replacement at year 15
- LCOE for both grid and solar ($/kWh)
- Cumulative savings tracking with breakeven year
- Optional loan financing with PMT calculation
- MACRS depreciation benefit for commercial installations
"""

import math

from solar_constants import (
    CAPACITY_FACTORS,
    DEFAULT_CAPACITY_FACTOR,
    INSTALL_COST_PER_WATT,
    ITC_RATE,
    ANNUAL_DEGRADATION,
    SYSTEM_LIFETIME_YEARS,
    DEFAULT_DISCOUNT_RATE,
    OM_COST_PER_KW_YEAR,
    GRID_CO2_KG_PER_KWH,
    STATE_CO2_RATES,
    AVG_HOME_KWH_YEAR,
    HOURS_PER_YEAR,
    INVERTER_COST_PER_WATT,
    INVERTER_REPLACEMENT_YEAR,
    RATE_ESCALATION,
    DEFAULT_LOAN_RATE,
    DEFAULT_LOAN_TERM,
    MACRS_5YR_SCHEDULE,
    DEFAULT_TAX_RATE,
)


def _pmt(rate: float, nper: int, pv: float) -> float:
    """Calculate monthly payment (PMT) for a fixed-rate loan.

    Same formula used for mortgages:
        PMT = P × r(1+r)^n / ((1+r)^n - 1)
    where r = monthly rate, n = months, P = principal.
    """
    if rate == 0:
        return pv / nper
    r = rate / 12
    n = nper * 12
    return pv * r * (1 + r) ** n / ((1 + r) ** n - 1)


def calc_solar(
    area_m2: float,
    state: str,
    usable_pct: float,
    panel_eff: float,
    price: float,
    include_itc: bool = True,
    discount_rate: float = DEFAULT_DISCOUNT_RATE,
    rate_escalation: float = RATE_ESCALATION,
    financing: str = "cash",  # "cash" or "loan"
    loan_rate: float = DEFAULT_LOAN_RATE,
    loan_term: int = DEFAULT_LOAN_TERM,
) -> dict:
    """
    Calculate solar potential for a given roof area with full financial modeling.

    Produces a professional-grade 25-year model including:
    - LCOE (Levelized Cost of Energy) for both solar and grid
    - Year-by-year cost comparison (solar vs grid with escalation)
    - Cumulative savings and breakeven year
    - Inverter replacement at year 15
    - Optional loan financing with PMT formula
    - MACRS depreciation benefit (commercial solar)

    Parameters
    ----------
    area_m2 : float
        Total roof area in square meters.
    state : str
        State name for capacity factor + CO₂ rate lookup.
    usable_pct : float
        Fraction of roof usable for panels (0-1).
    panel_eff : float
        Panel power density in W/m².
    price : float
        Electricity price in $/kWh (year-1 base rate).
    include_itc : bool
        Whether to apply the 30% federal ITC.
    discount_rate : float
        Discount rate for NPV calculation.
    rate_escalation : float
        Annual grid electricity price escalation rate.
    financing : str
        "cash" for outright purchase, "loan" for financed.
    loan_rate : float
        Annual loan interest rate (only used if financing="loan").
    loan_term : int
        Loan term in years (only used if financing="loan").

    Returns
    -------
    dict with comprehensive solar generation, financial, and comparison estimates.
    """
    cf = CAPACITY_FACTORS.get(state, DEFAULT_CAPACITY_FACTOR)
    co2_rate = STATE_CO2_RATES.get(state, GRID_CO2_KG_PER_KWH)

    # --- Generation ---
    usable = area_m2 * usable_pct
    capacity_kw = usable * panel_eff / 1000  # DC nameplate
    capacity_w = capacity_kw * 1000
    annual_kwh_yr1 = capacity_kw * HOURS_PER_YEAR * cf  # year-1 AC output

    # --- Costs ---
    gross_cost = capacity_w * INSTALL_COST_PER_WATT
    itc_savings = gross_cost * ITC_RATE if include_itc else 0.0
    net_cost = gross_cost - itc_savings
    annual_om = capacity_kw * OM_COST_PER_KW_YEAR
    inverter_cost = capacity_w * INVERTER_COST_PER_WATT  # mid-life replacement

    # --- MACRS Depreciation benefit (commercial) ---
    # Depreciable basis = gross_cost - (ITC_rate / 2) * gross_cost  (IRS rule)
    depreciable_basis = gross_cost * (1 - (ITC_RATE / 2 if include_itc else 0))
    macrs_benefit = sum(
        depreciable_basis * frac * DEFAULT_TAX_RATE
        for frac in MACRS_5YR_SCHEDULE
    )

    # --- Financing ---
    monthly_payment = 0.0
    annual_loan_payment = 0.0
    total_loan_cost = 0.0
    if financing == "loan" and net_cost > 0:
        monthly_payment = _pmt(loan_rate, loan_term, net_cost)
        annual_loan_payment = monthly_payment * 12
        total_loan_cost = annual_loan_payment * loan_term

    # --- Year-1 financials ---
    annual_revenue_yr1 = annual_kwh_yr1 * price
    net_annual_yr1 = annual_revenue_yr1 - annual_om

    # --- Simple payback (on net cost, no escalation) ---
    simple_payback = net_cost / net_annual_yr1 if net_annual_yr1 > 0 else 999

    # ===================================================================
    # 25-YEAR MODEL — Year-by-year solar vs grid comparison
    # Inspired by professional LCOE methodology
    # ===================================================================
    npv = -net_cost if financing == "cash" else 0  # Loan: no upfront cost
    cumulative_kwh = 0.0
    payback_year = None
    cumulative_cashflow = -net_cost if financing == "cash" else 0

    # Accumulators for LCOE
    total_solar_cost_discounted = net_cost if financing == "cash" else 0
    total_grid_cost_discounted = 0.0
    total_kwh_discounted = 0.0

    yearly_data = []  # Detailed year-by-year breakdown

    for year in range(1, SYSTEM_LIFETIME_YEARS + 1):
        # --- Grid side (what you'd pay WITHOUT solar) ---
        grid_rate = price * (1 + rate_escalation) ** (year - 1)
        grid_cost = annual_kwh_yr1 * grid_rate  # Grid cost for the demand solar would serve

        # --- Solar side ---
        degradation_factor = (1 - ANNUAL_DEGRADATION) ** (year - 1)
        year_kwh = annual_kwh_yr1 * degradation_factor
        year_revenue = year_kwh * grid_rate  # Revenue at escalated rate

        # Solar costs for this year
        year_om = annual_om
        year_loan = annual_loan_payment if (financing == "loan" and year <= loan_term) else 0
        year_inverter = inverter_cost if year == INVERTER_REPLACEMENT_YEAR else 0

        # MACRS depreciation benefit (years 1-6)
        year_macrs = 0.0
        if year <= len(MACRS_5YR_SCHEDULE):
            year_macrs = depreciable_basis * MACRS_5YR_SCHEDULE[year - 1] * DEFAULT_TAX_RATE

        # Total solar cost this year
        if financing == "cash":
            year_solar_cost = year_om + year_inverter - year_macrs
        else:
            year_solar_cost = year_loan + year_om + year_inverter - year_macrs

        # Cashflow: revenue minus costs
        year_cashflow = year_revenue - year_solar_cost

        # NPV accumulation
        discount = (1 + discount_rate) ** year
        discounted_cashflow = year_cashflow / discount if financing == "cash" else \
            (year_revenue - year_solar_cost) / discount
        npv += discounted_cashflow

        # Cumulative savings vs grid
        year_savings = grid_cost - year_solar_cost
        if financing == "cash":
            # For cash, the upfront cost is already deducted
            cumulative_cashflow += year_cashflow
        else:
            cumulative_cashflow += year_savings

        cumulative_kwh += year_kwh

        if payback_year is None and cumulative_cashflow >= 0:
            payback_year = year

        # LCOE accumulators
        total_solar_cost_discounted += year_solar_cost / discount
        total_grid_cost_discounted += grid_cost / discount
        total_kwh_discounted += year_kwh / discount

        yearly_data.append({
            "year": year,
            "grid_rate": round(grid_rate, 4),
            "grid_cost": round(grid_cost, 0),
            "solar_kwh": round(year_kwh, 0),
            "solar_cost": round(year_solar_cost, 0),
            "solar_revenue": round(year_revenue, 0),
            "savings": round(year_savings, 0),
            "cumulative_savings": round(cumulative_cashflow, 0),
            "generation_mwh": round(year_kwh / 1000, 1),
        })

    lifetime_mwh = cumulative_kwh / 1000

    # --- LCOE Calculation ---
    # LCOE = total discounted costs / total discounted energy
    lcoe_solar = total_solar_cost_discounted / total_kwh_discounted if total_kwh_discounted > 0 else 999
    lcoe_grid = total_grid_cost_discounted / total_kwh_discounted if total_kwh_discounted > 0 else price

    # Lifetime grid cost (undiscounted, for comparison)
    lifetime_grid_cost = sum(
        annual_kwh_yr1 * price * (1 + rate_escalation) ** (y - 1)
        for y in range(1, SYSTEM_LIFETIME_YEARS + 1)
    )
    lifetime_solar_cost = (net_cost if financing == "cash" else total_loan_cost) + \
        annual_om * SYSTEM_LIFETIME_YEARS + inverter_cost - macrs_benefit

    lifetime_savings = lifetime_grid_cost - lifetime_solar_cost

    # --- Environmental ---
    co2_avoided_yr1 = annual_kwh_yr1 * co2_rate / 1000  # metric tons
    co2_avoided_lifetime = cumulative_kwh * co2_rate / 1000
    homes_powered = annual_kwh_yr1 / AVG_HOME_KWH_YEAR

    return {
        # Generation
        "usable_area_m2": round(usable, 1),
        "capacity_kw": round(capacity_kw, 1),
        "capacity_mw": round(capacity_kw / 1000, 3),
        "annual_kwh": round(annual_kwh_yr1, 0),
        "annual_mwh": round(annual_kwh_yr1 / 1000, 1),
        "capacity_factor": cf,
        # Financials
        "annual_revenue": round(annual_revenue_yr1, 0),
        "gross_install_cost": round(gross_cost, 0),
        "itc_savings": round(itc_savings, 0),
        "install_cost": round(net_cost, 0),
        "annual_om": round(annual_om, 0),
        "simple_payback_years": round(simple_payback, 1),
        "payback_years": payback_year or round(simple_payback, 1),
        "npv_25yr": round(npv, 0),
        "lifetime_mwh": round(lifetime_mwh, 0),
        "cost_per_watt": INSTALL_COST_PER_WATT,
        "itc_rate": ITC_RATE if include_itc else 0,
        "discount_rate": discount_rate,
        "degradation_rate": ANNUAL_DEGRADATION,
        "yearly_generation_mwh": [yd["generation_mwh"] for yd in yearly_data],
        # LCOE & Grid Comparison (NEW — inspired by LCOE methodology)
        "lcoe_solar": round(lcoe_solar, 4),
        "lcoe_grid": round(lcoe_grid, 4),
        "lcoe_savings_pct": round((1 - lcoe_solar / lcoe_grid) * 100, 1) if lcoe_grid > 0 else 0,
        "rate_escalation": rate_escalation,
        "lifetime_grid_cost": round(lifetime_grid_cost, 0),
        "lifetime_solar_cost": round(lifetime_solar_cost, 0),
        "lifetime_savings": round(lifetime_savings, 0),
        "inverter_replacement_cost": round(inverter_cost, 0),
        "inverter_replacement_year": INVERTER_REPLACEMENT_YEAR,
        "macrs_benefit": round(macrs_benefit, 0),
        "yearly_cashflow": yearly_data,
        # Financing
        "financing": financing,
        "monthly_payment": round(monthly_payment, 2) if financing == "loan" else 0,
        "annual_loan_payment": round(annual_loan_payment, 0) if financing == "loan" else 0,
        "total_loan_cost": round(total_loan_cost, 0) if financing == "loan" else 0,
        "loan_rate": loan_rate if financing == "loan" else 0,
        "loan_term": loan_term if financing == "loan" else 0,
        # Environmental
        "co2_avoided_tons": round(co2_avoided_yr1, 1),
        "co2_avoided_lifetime_tons": round(co2_avoided_lifetime, 0),
        "homes_powered": round(homes_powered, 0),
        "co2_rate_kg_kwh": co2_rate,
    }


def calc_totals(buildings: list, state: str, usable_pct: float, panel_eff: float, price: float, **kwargs) -> dict:
    """Calculate aggregate totals for a list of buildings."""
    total_area = sum(b["area_m2"] for b in buildings)
    totals = calc_solar(total_area, state, usable_pct, panel_eff, price, **kwargs)
    totals["building_count"] = len(buildings)
    totals["total_roof_area_m2"] = round(total_area, 0)
    return totals
