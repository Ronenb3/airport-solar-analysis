"""
Single source of truth for all solar-related constants and parameters.

Data sources & methodology:
- Per-airport capacity factors: NREL PVWatts v8 API + NSRDB TMY3 (2024)
  https://developer.nrel.gov/api/pvwatts/v8.json
  10° tilt, south-facing, fixed roof mount, 14% system losses
- State-level fallback: NREL 2024 Annual Technology Baseline (ATB)
  https://atb.nrel.gov/electricity/2024/commercial_pv
- eGRID subregion CO2 rates: EPA eGRID 2023 (subregion-level, not state)
- Install costs: SEIA/Wood Mackenzie U.S. Solar Market Insight 2025
- Electricity prices: EIA Electric Power Monthly 2024
"""

# =============================================================================
# PER-AIRPORT CAPACITY FACTORS (NREL PVWatts v8 API + NSRDB TMY, 2024)
# =============================================================================
# AC capacity factors derived from PVWatts API calls per airport lat/lon.
# Parameters: tilt=10°, azimuth=180° (south), fixed roof mount, losses=14%.
# This supersedes state-level ATB averages for supported airports.
# Source: https://developer.nrel.gov/api/pvwatts/v8.json (DEMO_KEY, Jan 2025)
# Note: SFO and SEA show largest deviation from state averages due to
# coastal fog (SFO) and maritime cloud cover (SEA).

AIRPORT_CAPACITY_FACTORS = {
    # Fetched directly from PVWatts API
    "ATL": 0.1581,  # 138,524 kWh/yr — state avg was 0.168 (+6% overstatement)
    "DFW": 0.1666,  # 145,947 kWh/yr — state avg was 0.175 (+5%)
    "DEN": 0.1704,  # 149,300 kWh/yr — state avg was 0.171 (close)
    "ORD": 0.1438,  # 125,967 kWh/yr — state avg was 0.153 (+6%)
    "LAX": 0.1854,  # 162,445 kWh/yr — state avg was 0.185 (close)
    "JFK": 0.1466,  # 128,415 kWh/yr — state avg was 0.153 (+4%)
    "LAS": 0.1897,  # 166,154 kWh/yr — state avg was 0.191 (close)
    "MCO": 0.1674,  # 146,616 kWh/yr — state avg was 0.171 (+2%)
    "CLT": 0.1581,  # 138,537 kWh/yr — state avg was 0.163 (+3%)
    "SEA": 0.1182,  # 103,500 kWh/yr — state avg was 0.140 (+18% overstatement!)
    # Derived from NREL NSRDB TMY3 data for airport coordinates
    "PHX": 0.2048,  # Phoenix desert — state avg was 0.198 (+3% understatement)
    "MIA": 0.1748,  # South Florida tropical — state avg was 0.171 (+2%)
    "IAH": 0.1697,  # Houston TX — state avg was 0.175 (+3%)
    "SFO": 0.1573,  # Bay Area marine layer — state avg was 0.185 (+18% overstatement!)
    "BOS": 0.1443,  # New England maritime — state avg was 0.153 (+6%)
    "EWR": 0.1496,  # Newark NJ — state avg was 0.158 (+5%)
    "MSP": 0.1558,  # Minneapolis — state avg was 0.153 (+2%)
    "DTW": 0.1441,  # Detroit — state avg was 0.146 (+1%)
    "FLL": 0.1748,  # Fort Lauderdale — state avg was 0.171 (+2%)
    "PHL": 0.1518,  # Philadelphia — state avg was 0.153 (+1%)
    "LGA": 0.1463,  # LaGuardia — state avg was 0.153 (+5%)
    "BWI": 0.1547,  # Baltimore — state avg was 0.158 (+2%)
    "DCA": 0.1552,  # Reagan National — state avg was 0.161 (+4%)
    "SAN": 0.1921,  # San Diego (sunnier than CA avg) — state avg was 0.185 (-4%)
    "IAD": 0.1553,  # Dulles — state avg was 0.161 (+3%)
    "TPA": 0.1685,  # Tampa — state avg was 0.171 (+1%)
    "AUS": 0.1694,  # Austin — state avg was 0.175 (+3%)
    "BNA": 0.1573,  # Nashville — state avg was 0.161 (+2%)
    "MDW": 0.1433,  # Chicago Midway — state avg was 0.153 (+7%)
    "HNL": 0.1887,  # Honolulu — state avg was 0.180 (-5%)
    "ABQ": 0.2012,  # Albuquerque high desert — state avg was 0.198 (-2%)
}

# =============================================================================
# NREL 2024 ATB CAPACITY FACTORS BY STATE
# =============================================================================
# AC capacity factors for commercial rooftop PV
# Based on Global Horizontal Irradiance (GHI) resource classes
# Source: https://atb.nrel.gov/electricity/2024/commercial_pv
# ~14% system losses included: inverter 96%, soiling 2%, wiring 2%,
# mismatch 2%, availability 3%, age 1.5%

CAPACITY_FACTORS = {
    # Class 1-2: Sunny Southwest (GHI > 5.5)
    "Arizona": 0.198,
    "Nevada": 0.191,
    "New Mexico": 0.198,

    # Class 2-3: California varies by region
    "California": 0.185,

    # Class 3-4: Texas & South
    "Texas": 0.175,
    "Florida": 0.171,
    "Louisiana": 0.168,
    "Hawaii": 0.180,

    # Class 4: Mountain West
    "Colorado": 0.171,
    "Utah": 0.175,

    # Class 4-5: Southeast
    "Georgia": 0.168,
    "North Carolina": 0.163,
    "South Carolina": 0.168,
    "Tennessee": 0.161,
    "Alabama": 0.168,

    # Class 5-6: Mid-Atlantic
    "Virginia": 0.161,
    "Maryland": 0.158,
    "New Jersey": 0.158,
    "Pennsylvania": 0.153,
    "Delaware": 0.158,

    # Class 6-7: Northeast
    "New York": 0.153,
    "Massachusetts": 0.153,
    "Connecticut": 0.153,
    "Rhode Island": 0.153,

    # Class 6-7: Midwest
    "Illinois": 0.153,
    "Michigan": 0.146,
    "Minnesota": 0.153,
    "Ohio": 0.146,
    "Indiana": 0.153,
    "Wisconsin": 0.146,

    # Class 9-10: Pacific Northwest
    "Washington": 0.140,
    "Oregon": 0.146,
}

# US mean from NREL 2024 ATB
DEFAULT_CAPACITY_FACTOR = 0.158

# =============================================================================
# EPA eGRID 2023 SUBREGION CO2 RATES PER AIRPORT (kg CO2/kWh)
# =============================================================================
# Each airport mapped to its actual eGRID subregion, not just state average.
# Key corrections vs state averages:
#   JFK -> NYLI subregion: 0.169 vs NY state 0.211 (Long Island isolated grid)
#   LGA -> NYCW subregion: 0.244 (NYC uses more gas peakers)
#   ORD/MDW -> RFCW subregion: 0.246 (RFC-West, coal-heavy Midwest)
#   DTW -> RFCM subregion: 0.467 (RFC-Michigan, heavy coal/gas)
# Source: EPA eGRID 2023 subregion data
AIRPORT_CO2_RATES = {
    "ATL": 0.324, "DFW": 0.349, "DEN": 0.492, "ORD": 0.246,
    "LAX": 0.178, "JFK": 0.169, "LAS": 0.291, "MCO": 0.357,
    "CLT": 0.283, "SEA": 0.120, "PHX": 0.311, "MIA": 0.357,
    "IAH": 0.349, "SFO": 0.178, "BOS": 0.373, "EWR": 0.212,
    "MSP": 0.339, "DTW": 0.467, "FLL": 0.357, "PHL": 0.293,
    "LGA": 0.244, "BWI": 0.236, "DCA": 0.244, "SAN": 0.178,
    "IAD": 0.244, "TPA": 0.357, "AUS": 0.349, "BNA": 0.298,
    "MDW": 0.246, "HNL": 0.628, "ABQ": 0.499,
}

# =============================================================================
# PANEL & INSTALLATION DEFAULTS
# =============================================================================

# Panel power density: 200 W/m² (standard 20% efficiency commercial panels)
DEFAULT_WATTS_PER_M2 = 200

# Usable roof fraction: 60% (NREL Gagnon et al., 2016)
DEFAULT_USABLE_FRACTION = 0.60

# Installation cost per watt (commercial rooftop, 2025 — SEIA/Wood Mackenzie)
INSTALL_COST_PER_WATT = 1.40

# =============================================================================
# FINANCIAL DEFAULTS
# =============================================================================

# Federal Investment Tax Credit (ITC) — 30% for commercial solar through 2032
ITC_RATE = 0.30

# Annual panel degradation rate (NREL 2024 ATB)
ANNUAL_DEGRADATION = 0.005  # 0.5%/year

# System lifetime in years
SYSTEM_LIFETIME_YEARS = 25

# Discount rate for NPV calculations
DEFAULT_DISCOUNT_RATE = 0.06  # 6%

# O&M cost per kW/year (NREL 2024 ATB)
OM_COST_PER_KW_YEAR = 15.0

# Inverter cost per watt (NREL 2024 ATB — mid-life replacement at ~year 15)
INVERTER_COST_PER_WATT = 0.10

# Inverter replacement year (typical inverter lifespan is 12-15 years)
INVERTER_REPLACEMENT_YEAR = 15

# =============================================================================
# FINANCING DEFAULTS
# =============================================================================

# Annual electricity rate escalation (EIA Annual Energy Outlook 2024)
# Commercial electricity prices have historically risen ~2%/year
RATE_ESCALATION = 0.02  # 2%/year

# Loan interest rate (commercial solar, 2025 market)
DEFAULT_LOAN_RATE = 0.065  # 6.5% APR

# Loan term in years
DEFAULT_LOAN_TERM = 25

# Property tax rate per kW/year (varies by jurisdiction; $0 for many states with exemptions)
PROPERTY_TAX_PER_KW_YEAR = 0.0

# MACRS depreciation schedule (5-year for commercial solar under IRC § 168)
# Year: depreciation fraction of depreciable basis
# Depreciable basis = gross_cost * (1 - ITC_RATE/2)  [ITC reduces basis by half the credit]
MACRS_5YR_SCHEDULE = [0.20, 0.32, 0.192, 0.1152, 0.1152, 0.0576]

# Assumed marginal tax rate for commercial entity (for depreciation benefit)
DEFAULT_TAX_RATE = 0.21  # Federal corporate rate

# =============================================================================
# ENVIRONMENTAL CONSTANTS
# =============================================================================

# Grid CO2 intensity — US average (kg CO2/kWh, EPA eGRID 2023)
GRID_CO2_KG_PER_KWH = 0.348

# Average US home consumption (EIA 2022)
AVG_HOME_KWH_YEAR = 10_500

# Hours per year
HOURS_PER_YEAR = 8_760

# =============================================================================
# EPA eGRID STATE CO2 RATES (kg CO2/kWh, eGRID 2023 — released Jan 2025)
# Source: https://www.epa.gov/egrid/summary-data
# =============================================================================

STATE_CO2_RATES = {
    "Arizona": 0.311,
    "California": 0.178,
    "Colorado": 0.492,
    "Florida": 0.357,
    "Georgia": 0.324,
    "Hawaii": 0.628,
    "Illinois": 0.214,
    "Maryland": 0.236,
    "Massachusetts": 0.373,
    "Michigan": 0.360,
    "Minnesota": 0.339,
    "Nevada": 0.291,
    "New Jersey": 0.212,
    "New York": 0.211,
    "North Carolina": 0.283,
    "Ohio": 0.483,
    "Pennsylvania": 0.293,
    "Tennessee": 0.298,
    "Texas": 0.349,
    "Virginia": 0.244,
    "Washington": 0.120,
}

# =============================================================================
# EIA 2024 COMMERCIAL ELECTRICITY PRICES BY STATE ($/kWh)
# Source: EIA Retail Sales API (annual, commercial sector)
# https://www.eia.gov/electricity/data/state/
# =============================================================================

STATE_ELEC_PRICES = {
    "Arizona": 0.1223,
    "California": 0.2554,
    "Colorado": 0.1171,
    "Florida": 0.1099,
    "Georgia": 0.1087,
    "Hawaii": 0.3818,
    "Illinois": 0.1181,
    "Maryland": 0.1296,
    "Massachusetts": 0.2090,
    "Michigan": 0.1401,
    "Minnesota": 0.1215,
    "Nevada": 0.1019,
    "New Jersey": 0.1464,
    "New Mexico": 0.1054,
    "New York": 0.1877,
    "North Carolina": 0.1056,
    "Ohio": 0.1066,
    "Pennsylvania": 0.1103,
    "Tennessee": 0.1205,
    "Texas": 0.0855,
    "Virginia": 0.0872,
    "Washington": 0.0999,
}

DEFAULT_ELEC_PRICE = 0.1275  # US commercial average (EIA 2024)

# =============================================================================
# STATE NET METERING POLICIES (DSIRE Database, 2024)
# Source: https://www.dsireusa.org/
# =============================================================================
# Categories:
#   "full"     — Full retail rate credit for excess generation
#   "reduced"  — Credit at avoided cost or reduced rate
#   "none"     — No statewide net metering mandate
#   "varies"   — Utility-specific policies, no uniform state law

STATE_NET_METERING = {
    "Arizona": {"policy": "reduced", "label": "Reduced Rate", "detail": "Export rate set by utility (typically 75-90% of retail)"},
    "California": {"policy": "reduced", "label": "Net Billing", "detail": "NEM 3.0: export credits at avoided cost (~$0.05/kWh avg)"},
    "Colorado": {"policy": "full", "label": "Full Retail", "detail": "Full retail credit up to 120% of annual consumption"},
    "Florida": {"policy": "full", "label": "Full Retail", "detail": "Full retail credit, no system size cap for commercial"},
    "Georgia": {"policy": "varies", "label": "Utility-Specific", "detail": "Georgia Power offers net metering; co-ops vary"},
    "Hawaii": {"policy": "reduced", "label": "Self-Supply", "detail": "Customer Self-Supply program; no export credit"},
    "Illinois": {"policy": "full", "label": "Full Retail", "detail": "Full retail credit; statewide net metering mandate"},
    "Maryland": {"policy": "full", "label": "Full Retail", "detail": "Full retail credit up to 200 kW commercial"},
    "Massachusetts": {"policy": "reduced", "label": "Net Metering Credit", "detail": "Credit varies by utility and system size"},
    "Michigan": {"policy": "reduced", "label": "Inflow/Outflow", "detail": "Outflow credited at avoided cost rate"},
    "Minnesota": {"policy": "full", "label": "Full Retail", "detail": "Full retail credit up to 1 MW"},
    "Nevada": {"policy": "reduced", "label": "Net Billing", "detail": "Export credit at 75% of retail rate"},
    "New Jersey": {"policy": "full", "label": "Full Retail", "detail": "Full retail credit; SREC program adds value"},
    "New Mexico": {"policy": "full", "label": "Full Retail", "detail": "Full retail credit up to 80 MW"},
    "New York": {"policy": "reduced", "label": "VDER", "detail": "Value of Distributed Energy Resources tariff"},
    "North Carolina": {"policy": "full", "label": "Full Retail", "detail": "Full retail credit up to 1 MW"},
    "Ohio": {"policy": "full", "label": "Full Retail", "detail": "Full retail credit; statewide mandate"},
    "Pennsylvania": {"policy": "full", "label": "Full Retail", "detail": "Full retail credit up to 5 MW"},
    "Tennessee": {"policy": "varies", "label": "Utility-Specific", "detail": "TVA Green Connect or utility programs; no state mandate"},
    "Texas": {"policy": "varies", "label": "Utility-Specific", "detail": "Deregulated market; retail providers set buyback rates"},
    "Virginia": {"policy": "full", "label": "Full Retail", "detail": "Full retail credit up to 1 MW; statewide mandate"},
    "Washington": {"policy": "full", "label": "Full Retail", "detail": "Full retail credit up to 100 kW"},
}

DEFAULT_NET_METERING = {"policy": "varies", "label": "Varies", "detail": "Check local utility for net metering availability"}

# =============================================================================
# FAA SOLAR GLARE THRESHOLDS
# =============================================================================
# FAA interim policy (2013, updated 2021) requires solar glare analysis for
# installations within airport property or within the approach/departure paths.
# Buildings closer to runways pose higher risk of pilot ocular hazard from
# specular reflection (glare). Thresholds below are simplified distance bands.
# Source: FAA Technical Guidance for Evaluating Solar Technologies on Airports
# https://www.faa.gov/airports/engineering/solar

GLARE_RISK_THRESHOLDS = {
    "high": 1.0,    # km — within airport perimeter, very likely in approach path
    "moderate": 2.5, # km — possibly in extended approach/departure corridor
    "low": 5.0,     # km — generally outside FAA concern area
}

