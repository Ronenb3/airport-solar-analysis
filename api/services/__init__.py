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
    AIRPORT_CAPACITY_FACTORS,
    AIRPORT_CO2_RATES,
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
    # New constants
    REC_PRICES_PER_MWH,
    DEFAULT_REC_PRICE_PER_MWH,
    LCFS_AIRPORTS,
    LCFS_CREDIT_PER_KWH,
    DEMAND_CHARGE_RATES,
    DEFAULT_DEMAND_CHARGE,
    DEMAND_REDUCTION_FACTOR,
    DEMAND_REDUCTION_OPTIMISTIC,
    REC_VOLATILE_STATES,
    IRA_ENERGY_COMMUNITY_AIRPORTS,
    IRA_ENERGY_COMMUNITY_ADDER,
    FAA_AIP_FEDERAL_SHARE,
    FAA_AIP_ELIGIBLE_TYPES,
    SECTION_179D_PER_M2,
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
    airport_code: str = None,
    shading_factor: float = 1.0,
    building_type: str = "commercial",
    include_carbon_credits: bool = True,
    include_demand_charges: bool = True,
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
    # Use per-airport PVWatts-derived CF if available, else fall back to state ATB
    cf = AIRPORT_CAPACITY_FACTORS.get(airport_code) if airport_code else None
    if cf is None:
        cf = CAPACITY_FACTORS.get(state, DEFAULT_CAPACITY_FACTOR)
    cf = cf * shading_factor  # Apply inter-building shading derating
    # Use per-airport eGRID subregion CO2 rate if available
    co2_rate = AIRPORT_CO2_RATES.get(airport_code) if airport_code else None
    if co2_rate is None:
        co2_rate = STATE_CO2_RATES.get(state, GRID_CO2_KG_PER_KWH)

    # --- Generation ---
    usable = area_m2 * usable_pct
    capacity_kw = usable * panel_eff / 1000  # DC nameplate
    capacity_w = capacity_kw * 1000
    annual_kwh_yr1 = capacity_kw * HOURS_PER_YEAR * cf  # year-1 AC output

    # --- IRA Bonus ITC adders ---
    ira_adder = 0.0
    if airport_code and airport_code.upper() in IRA_ENERGY_COMMUNITY_AIRPORTS:
        ira_adder = IRA_ENERGY_COMMUNITY_ADDER  # +10%

    effective_itc = (ITC_RATE + ira_adder) if include_itc else 0.0

    # --- Costs (base case: gross cost minus ITC only, NO FAA AIP applied) ---
    gross_cost = capacity_w * INSTALL_COST_PER_WATT

    # --- FAA AIP grant potential (shown as upside scenario, NOT applied to base cost) ---
    # FAA Airport Improvement Program can cover up to 90% of eligible costs for
    # terminal/hangar/cargo buildings. However, it requires:
    #   - Multi-year application and FAA approval cycle (typically 2-4 years)
    #   - Environmental review (NEPA categorical exclusion or EA)
    #   - FAA design standards compliance (AC 150/5370-10)
    # It is treated as a grant_potential scenario upside, not underwritten in base case.
    faa_aip_applicable = building_type in FAA_AIP_ELIGIBLE_TYPES
    faa_aip_grant_potential = gross_cost * FAA_AIP_FEDERAL_SHARE if faa_aip_applicable else 0.0
    itc_savings = gross_cost * effective_itc if include_itc else 0.0
    net_cost = max(gross_cost - itc_savings, 0.0)

    # Grants scenario: what install cost would be with FAA AIP applied
    net_cost_with_grants = max(
        gross_cost - faa_aip_grant_potential - (gross_cost * (1 - FAA_AIP_FEDERAL_SHARE) * effective_itc),
        0.0
    ) if faa_aip_applicable else net_cost

    annual_om = capacity_kw * OM_COST_PER_KW_YEAR
    inverter_cost = capacity_w * INVERTER_COST_PER_WATT  # mid-life replacement

    # --- Section 179D deduction (commercial buildings only, not federally funded) ---
    # Available for all building types in base/incentives scenarios.
    # Excluded in grants scenario (FAA-funded portion not eligible per IRS rules).
    section_179d = usable * SECTION_179D_PER_M2 * DEFAULT_TAX_RATE

    # --- MACRS Depreciation benefit (commercial) ---
    # Depreciable basis = gross_cost - (ITC_rate / 2) * gross_cost  (IRS rule)
    depreciable_basis = gross_cost * (1 - (effective_itc / 2 if include_itc else 0))
    macrs_benefit = sum(
        depreciable_basis * frac * DEFAULT_TAX_RATE
        for frac in MACRS_5YR_SCHEDULE
    )

    # --- REC / Carbon Credit Revenue ---
    # Renewable Energy Certificates: unbundled, sold annually per MWh generated
    rec_price = REC_PRICES_PER_MWH.get(state, DEFAULT_REC_PRICE_PER_MWH)
    # Flag volatile REC markets — prices subject to significant year-to-year change
    rec_price_volatile = state in REC_VOLATILE_STATES
    annual_rec_revenue_yr1 = (annual_kwh_yr1 / 1000) * rec_price if include_carbon_credits else 0.0
    # LCFS (CA airports only): additional $/kWh when powering transportation loads
    lcfs_revenue_yr1 = 0.0
    if include_carbon_credits and airport_code and airport_code.upper() in LCFS_AIRPORTS:
        lcfs_revenue_yr1 = annual_kwh_yr1 * LCFS_CREDIT_PER_KWH

    # --- Demand Charge Savings ---
    # Conservative: 15% coincident peak shaving (DEMAND_REDUCTION_FACTOR).
    # Requires 15-min interval meter data to confirm utility-specific peak window.
    # Optimistic: 25% with smart inverter dispatch aligned to peak window.
    demand_rate = DEMAND_CHARGE_RATES.get(airport_code, DEFAULT_DEMAND_CHARGE) if airport_code else DEFAULT_DEMAND_CHARGE
    annual_demand_savings_yr1 = 0.0
    if include_demand_charges:
        annual_demand_savings_yr1 = capacity_kw * DEMAND_REDUCTION_FACTOR * demand_rate * 12
    # Compute optimistic demand savings separately (for scenario comparison)
    annual_demand_savings_optimistic = capacity_kw * DEMAND_REDUCTION_OPTIMISTIC * demand_rate * 12 if include_demand_charges else 0.0

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
    # Base: electricity savings only (most conservative, no ancillary revenues)
    net_annual_base = annual_revenue_yr1 - annual_om
    # Incentives: + RECs + demand (conservative) + LCFS
    net_annual_yr1 = annual_revenue_yr1 + annual_rec_revenue_yr1 + annual_demand_savings_yr1 + lcfs_revenue_yr1 - annual_om

    # --- Simple payback (base case: electricity savings only) ---
    simple_payback_base = net_cost / net_annual_base if net_annual_base > 0 else 999
    simple_payback = net_cost / net_annual_yr1 if net_annual_yr1 > 0 else 999

    # ===================================================================
    # 25-YEAR MODEL — Year-by-year solar vs grid comparison
    # Base scenario: electricity savings + ITC + MACRS. No ancillary revenues.
    # Ancillary revenues (RECs, demand, LCFS) tracked separately for scenario NPVs.
    # ===================================================================
    npv = -net_cost if financing == "cash" else 0  # Loan: no upfront cost
    cumulative_kwh = 0.0
    payback_year = None
    payback_year_base = None  # Base case payback (electricity only)
    cumulative_cashflow = -net_cost if financing == "cash" else 0
    cumulative_cashflow_base = -net_cost if financing == "cash" else 0
    pv_ancillary = 0.0  # PV of ancillary revenues (RECs + demand + LCFS)

    # Section 179D realized in year 1 (tax return)
    if section_179d > 0:
        cumulative_cashflow += section_179d
        cumulative_cashflow_base += section_179d

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

        # REC revenue (RECs typically sold for 1–3 year contracts; assume annual reset)
        year_rec = (year_kwh / 1000) * rec_price if include_carbon_credits else 0.0
        # LCFS revenue (annual, CA airports only)
        year_lcfs = year_kwh * LCFS_CREDIT_PER_KWH if (include_carbon_credits and airport_code and airport_code.upper() in LCFS_AIRPORTS) else 0.0
        # Demand savings (capacity degrades but peak savings roughly stable due to panel sizing)
        year_demand = annual_demand_savings_yr1  # Conservative: flat over life

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

        # Total solar revenue (electricity + RECs + demand + LCFS)
        year_total_revenue = year_revenue + year_rec + year_demand + year_lcfs
        year_base_revenue = year_revenue  # Electricity savings only

        # Cashflow: total revenue minus costs
        year_cashflow = year_total_revenue - year_solar_cost
        year_cashflow_base = year_base_revenue - year_solar_cost

        # NPV accumulation (base: electricity only)
        discount = (1 + discount_rate) ** year
        discounted_cashflow = year_cashflow / discount if financing == "cash" else \
            (year_total_revenue - year_solar_cost) / discount
        npv += discounted_cashflow

        # Track PV of ancillary revenues for scenario breakdown
        pv_ancillary += (year_rec + year_demand + year_lcfs) / discount

        # Cumulative savings vs grid (incentives scenario)
        year_savings = grid_cost - year_solar_cost + year_rec + year_demand + year_lcfs
        year_savings_base = grid_cost - year_solar_cost
        if financing == "cash":
            cumulative_cashflow += year_cashflow
            cumulative_cashflow_base += year_cashflow_base
        else:
            cumulative_cashflow += year_savings
            cumulative_cashflow_base += year_savings_base

        cumulative_kwh += year_kwh

        if payback_year is None and cumulative_cashflow >= 0:
            payback_year = year
        if payback_year_base is None and cumulative_cashflow_base >= 0:
            payback_year_base = year

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
            "solar_revenue": round(year_total_revenue, 0),
            "rec_revenue": round(year_rec, 0),
            "demand_savings": round(year_demand, 0),
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

    # Lifetime ancillary revenues (RECs, demand, LCFS) — simple sum
    lifetime_rec_revenue = sum(
        (annual_kwh_yr1 * (1 - ANNUAL_DEGRADATION) ** (y - 1) / 1000) * rec_price
        for y in range(1, SYSTEM_LIFETIME_YEARS + 1)
    ) if include_carbon_credits else 0.0
    lifetime_demand_savings = annual_demand_savings_yr1 * SYSTEM_LIFETIME_YEARS if include_demand_charges else 0.0
    lifetime_lcfs = (annual_kwh_yr1 * LCFS_CREDIT_PER_KWH * SYSTEM_LIFETIME_YEARS) \
        if (include_carbon_credits and airport_code and airport_code.upper() in LCFS_AIRPORTS) else 0.0

    lifetime_savings = lifetime_grid_cost - lifetime_solar_cost + lifetime_rec_revenue + lifetime_demand_savings + lifetime_lcfs

    # --- Three-scenario NPVs ---
    # npv currently = base case (electricity + ITC + MACRS) since pv_ancillary was tracked separately
    # but wait: the loop DID include ancillary in npv. Need to subtract.
    npv_with_incentives = npv                          # electricity + RECs + demand (15%) + LCFS
    npv_base_only = npv - pv_ancillary                 # electricity + ITC + MACRS only
    npv_with_grants = npv_with_incentives + faa_aip_grant_potential  # + FAA AIP year-0 cost reduction

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
        "install_cost_with_grants": round(net_cost_with_grants, 0),
        "annual_om": round(annual_om, 0),
        "simple_payback_years": round(simple_payback, 1),
        "simple_payback_base_years": round(simple_payback_base, 1),
        "payback_years": payback_year or round(simple_payback, 1),
        "payback_years_base": payback_year_base or round(simple_payback_base, 1),
        # Three-scenario NPVs — pick the right one for the context:
        # npv_base: most conservative (electricity savings + ITC only, no grants)
        # npv_25yr / npv_with_incentives: adds RECs + demand savings (conservative 15%) + LCFS
        # npv_with_grants: adds FAA AIP potential (requires application; not underwritten)
        "npv_25yr": round(npv_with_incentives, 0),
        "npv_base": round(npv_base_only, 0),
        "npv_with_incentives": round(npv_with_incentives, 0),
        "npv_with_grants": round(npv_with_grants, 0),
        "scenario_npvs": {
            "base": round(npv_base_only, 0),
            "incentives": round(npv_with_incentives, 0),
            "grants": round(npv_with_grants, 0),
        },
        "lifetime_mwh": round(lifetime_mwh, 0),
        "cost_per_watt": INSTALL_COST_PER_WATT,
        "itc_rate": effective_itc if include_itc else 0,
        "ira_adder": round(ira_adder, 2),
        "discount_rate": discount_rate,
        "degradation_rate": ANNUAL_DEGRADATION,
        "yearly_generation_mwh": [yd["generation_mwh"] for yd in yearly_data],
        # LCOE & Grid Comparison
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
        # Carbon credits & ancillary revenue
        "annual_rec_revenue": round(annual_rec_revenue_yr1, 0),
        "rec_price_per_mwh": round(rec_price, 2),
        "annual_lcfs_revenue": round(lcfs_revenue_yr1, 0),
        "annual_demand_savings": round(annual_demand_savings_yr1, 0),
        "demand_charge_rate": round(demand_rate, 2),
        "lifetime_rec_revenue": round(lifetime_rec_revenue, 0),
        "lifetime_demand_savings": round(lifetime_demand_savings, 0),
        "lifetime_lcfs_revenue": round(lifetime_lcfs, 0),
        # Carbon credits — notes on confidence
        "rec_price_volatile": rec_price_volatile,
        "rec_price_note": (
            f"Market-rate REC price for {state}; this state has a historically volatile "
            "REC/SREC market — actual contracted price may differ materially."
        ) if rec_price_volatile else f"Estimated spot REC price for {state}.",
        "demand_confidence": (
            "Estimated — 15% coincident peak shaving assumed (conservative). "
            "Verify with 15-min interval utility billing data before underwriting."
        ),
        # Grant / tax programs
        "faa_aip_applicable": faa_aip_applicable,
        "faa_aip_grant_potential": round(faa_aip_grant_potential, 0),
        "faa_aip_grant": round(faa_aip_grant_potential, 0),  # backward compat alias
        "faa_aip_note": (
            "FAA AIP covers up to 90% of eligible costs for qualified airport infrastructure. "
            "Requires 2-4 year application cycle, NEPA review, and FAA design compliance. "
            "Shown as upside scenario — do not apply to base-case underwriting."
        ) if faa_aip_applicable else None,
        "section_179d_benefit": round(section_179d, 0),
        "building_type": building_type,
    }


def calc_totals(buildings: list, state: str, usable_pct: float, panel_eff: float, price: float, **kwargs) -> dict:
    """Calculate aggregate totals for a list of buildings."""
    total_area = sum(b["area_m2"] for b in buildings)
    totals = calc_solar(total_area, state, usable_pct, panel_eff, price, **kwargs)
    totals["building_count"] = len(buildings)
    totals["total_roof_area_m2"] = round(total_area, 0)
    return totals
