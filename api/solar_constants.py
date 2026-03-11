"""
Single source of truth for all solar-related constants and parameters.

Data sources & methodology:
- Capacity factors: NREL 2024 Annual Technology Baseline (ATB)
  https://atb.nrel.gov/electricity/2024/commercial_pv
- Commercial PV assumptions based on 200kW flat-roof systems
- DC capacity factors range from 12.7% (Class 10) to 19.8% (Class 1)
- Install costs: SEIA/Wood Mackenzie U.S. Solar Market Insight 2025
- Grid emissions: EPA eGRID 2023
- Electricity prices: EIA Electric Power Monthly 2024
"""

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

