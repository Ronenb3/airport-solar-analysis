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

# =============================================================================
# RENEWABLE ENERGY CERTIFICATE (REC) PRICES BY STATE ($/MWh, 2024)
# =============================================================================
# REC prices vary widely by state based on RPSs and voluntary market demand.
# Source: SREC Trade, LevelTen Energy 2024 Market Intelligence Report,
#         NREL State RPS compliance analysis 2024
# Note: NJ/MA/CT/IL have high-value SREC/SREC-II markets & carve-outs.
# California uses LCFS instead of RECs for commercial aviation sector.
REC_PRICES_PER_MWH = {
    # Compliance markets with high value
    "New Jersey": 68.0,    # NJ SREC: ~$215 TRECkills, but commercial ~$68/MWh
    "Massachusetts": 55.0, # MA SREC-II program, ~$40-70/MWh
    "Connecticut": 45.0,   # CT Class I RECs
    "Illinois": 25.0,      # IL Adjustable Block / SREC
    "Maryland": 22.0,      # MD RPS with solar carve-out
    "New York": 18.0,      # NY CSC credits
    "Virginia": 16.0,      # VA IRP solar carve-out
    "North Carolina": 12.0, # NC REPS program
    "Pennsylvania": 10.0,  # PA AECs (Alternative Energy Credits)
    "Ohio": 8.0,           # OH competitive market
    # States with lower-value voluntary markets
    "California": 5.0,     # CA has LCFS (below); unbundled REC market thin
    "Texas": 3.0,          # TX voluntary market, very low (surplus)
    "Nevada": 6.0,         # NV RPS compliance
    "Arizona": 6.0,        # AZ RPS carve-out
    "Florida": 3.0,        # FL voluntary, no mandate
    "Georgia": 3.0,        # GA voluntary
    "Colorado": 8.0,       # CO RPS
    "Minnesota": 9.0,      # MN community solar premium
    "Washington": 7.0,     # WA Clean Energy standard
    "Tennessee": 3.0,      # TVA voluntary
    "Michigan": 7.0,       # MI RPS compliance
    "Hawaii": 12.0,        # HI RPS 100% by 2045
}
DEFAULT_REC_PRICE_PER_MWH = 8.0  # US voluntary market average (~$8-10/MWh)

# =============================================================================
# CALIFORNIA LCFS (Low Carbon Fuel Standard) CREDIT — CA AIRPORTS ONLY
# =============================================================================
# LCFS credits available for renewable electricity used in transportation context.
# Airport ground support equipment (GSE) running on electricity from rooftop PV
# can generate LCFS credits: ~$80/ton CO2eq (2024 average clearing price).
# Electricity grid CI (carbon intensity): CA grid ~100 gCO2e/MJ → 0.36 kgCO2e/kWh
# Solar CI: ~30 gCO2e/MJ lifecycle → 0.108 kgCO2e/kWh
# Net CI reduction: 0.252 kgCO2e/kWh = 0.252 tonnes CO2e/MWh
# LCFS credit: 0.252 tonne/MWh × $80/tonne = $20.16/MWh ≈ $0.020/kWh
# (Lower bound — higher for direct airport GSE pathway, up to $0.075/kWh)
# Source: CARB LCFS Dashboard 2024; BloombergNEF LCFS Price Forecast 2024
LCFS_AIRPORTS = {"LAX", "SFO", "SAN", "OAK"}  # CA airports
LCFS_CREDIT_PER_KWH = 0.020  # Conservative estimate for general airport use

# =============================================================================
# DEMAND CHARGE RATES BY AIRPORT / UTILITY ($/kW-month)
# =============================================================================
# Commercial customers pay demand charges on their monthly peak kW draw.
# Solar reduces the peak, esp. during afternoon hours (noon-3pm).
# Conservative assumption: solar shaves 25% of coincident peak demand.
# Source: OpenEI Utility Rate Database (URDB) 2024; utility tariff filings
DEMAND_CHARGE_RATES = {
    "ATL":  14.00,  # Georgia Power: LG-7 large commercial ~$14/kW-mo
    "DFW":  11.00,  # Oncor/TXU large commercial ~$11/kW-mo
    "DEN":  13.50,  # Xcel Energy CISD-SB ~$13.50/kW-mo
    "ORD":  16.00,  # ComEd large commercial B-1 ~$16/kW-mo
    "LAX":  19.00,  # SCE TOU-GS-3 ~$19/kW-mo (expensive CA utility)
    "JFK":  18.00,  # Con Edison SC-9 large commercial ~$18/kW-mo
    "LAS":  10.00,  # NV Energy LGS ~$10/kW-mo
    "MCO":  13.00,  # Duke Energy Florida GS-2 ~$13/kW-mo
    "CLT":  12.00,  # Duke Energy Carolinas SGS-6 ~$12/kW-mo
    "SEA":  10.00,  # Puget Sound Energy GS-3 ~$10/kW-mo (mostly hydro)
    "PHX":  12.00,  # APS Comml LG ~$12/kW-mo
    "MIA":  13.00,  # FPL GSD-2 ~$13/kW-mo
    "IAH":  11.00,  # CenterPoint/Reliant large commercial ~$11/kW-mo
    "SFO":  19.00,  # PG&E BX large commercial ~$19/kW-mo
    "BOS":  22.00,  # Eversource LCA-S large commercial ~$22/kW-mo (highest in US)
    "EWR":  15.00,  # PSE&G LPL large commercial ~$15/kW-mo
    "MSP":  12.00,  # Xcel Energy MN Lg.Business ~$12/kW-mo
    "DTW":  13.00,  # DTE Energy D11 large commercial ~$13/kW-mo
    "FLL":  13.00,  # FPL GSD-2 Broward ~$13/kW-mo
    "PHL":  14.00,  # PECO large commercial GS-3 ~$14/kW-mo
    "LGA":  18.00,  # Con Edison SC-9 ~$18/kW-mo
    "BWI":  14.00,  # BGE C&I large commercial ~$14/kW-mo
    "DCA":  15.00,  # Dominion Energy VAE large commercial ~$15/kW-mo
    "SAN":  19.00,  # SDG&E AL-TOU commercial ~$19/kW-mo
    "IAD":  15.00,  # Dominion Energy large commercial ~$15/kW-mo
    "TPA":  13.00,  # Duke/TECO large commercial ~$13/kW-mo
    "AUS":  11.00,  # Austin Energy large commercial LGS ~$11/kW-mo
    "BNA":  11.00,  # NES (Nashville Electric) commercial ~$11/kW-mo
    "MDW":  16.00,  # ComEd B-1 ~$16/kW-mo (same grid as ORD)
    "HNL":  17.00,  # HECO large commercial G commercial ~$17/kW-mo
    "ABQ":  11.00,  # PNM large commercial ~$11/kW-mo
}
DEFAULT_DEMAND_CHARGE = 13.50  # National commercial average
# What fraction of peak kW demand solar covers (for demand charge savings)
# Conservative: ~25% via afternoon generation (noon-3pm peak alignment)
DEMAND_REDUCTION_FACTOR = 0.25

# =============================================================================
# IRA (Inflation Reduction Act) BONUS ITC ADDERS — 2024
# =============================================================================
# IRA Section 48 bonus credits on top of the base 30% ITC:
# +10% Domestic Content (US-made panels/racking; not modeled here — complex)
# +10% Energy Community (census tract w/ shut coal plant or >0.17% fossil fuel jobs)
# +10% Low-Income Community (LMI bonus for smaller projects ≤5 MW)
# Source: IRS Notice 2023-29; DOE/Treasury Energy Community Mapping Tool 2024
# Note: Only energy community bonus included here (airports tend to be in
#       industrial zones with higher probability of energy community designation).
IRA_ENERGY_COMMUNITY_AIRPORTS = {
    # Airports in or adjacent to energy community census tracts (IRS/Treasury 2024)
    # These have significant coal/fossil employment history nearby
    "PHL",   # Philadelphia — former shipping/industrial
    "DTW",   # Detroit — Rust Belt, automotive legacy coal use
    "CLT",   # Charlotte — Carolinas coal history
    "TPA",   # Tampa — former coal plants in Hillsborough County
    "BOS",   # Boston — former coal plants in MA
    "BNA",   # Nashville — TVA coal legacy
    "MDW",   # Chicago Midway — heavy industrial area
    "ORD",   # Chicago O'Hare — industrial corridor
    "PIT",   # Pittsburgh (not in top 30, but if added)
    "BWI",   # Maryland — Brandon Shores coal plant retiring
}
IRA_ENERGY_COMMUNITY_ADDER = 0.10  # +10% ITC on top of base 30%

# =============================================================================
# AIRPORT RUNWAY HEADINGS (for pvlib-based glare analysis)
# =============================================================================
# Primary runway magnetic headings (degrees true, converted) per airport.
# Used for FAA glare: reflected sunbeam azimuth checked against runway corridors.
# Source: FAA NASR aeronautical data (public domain)
# Only major runways listed; sub-runways omitted for performance.
RUNWAY_HEADINGS = {
    "ATL": [100, 280, 80, 260],    # 10/28, 08/26
    "DFW": [170, 350, 180, 360],   # 17/35, 18/36
    "DEN": [80, 260, 160, 340, 170, 350],  # 08/26, 16/34, 17/35
    "ORD": [100, 280, 90, 270, 40, 220],   # 10/28, 09/27, 04/22
    "LAX": [60, 240, 70, 250],     # 06/24, 07/25
    "JFK": [40, 220, 130, 310],    # 04/22, 13/31
    "LAS": [10, 190, 70, 250],     # 01/19, 07/25
    "MCO": [180, 360, 170, 350],   # 18/36, 17/35
    "CLT": [180, 360, 50, 230],    # 18/36, 05/23
    "SEA": [160, 340],              # 16/34
    "PHX": [80, 260],               # 08/26
    "MIA": [90, 270, 120, 300],    # 09/27, 12/30
    "IAH": [150, 330, 90, 270],    # 15/33, 09/27
    "SFO": [100, 280, 10, 190],    # 10/28, 01/19
    "BOS": [40, 220, 90, 270, 150, 330],  # 04/22, 09/27, 15/33
    "EWR": [40, 220, 110, 290],    # 04/22, 11/29
    "MSP": [120, 300, 170, 350],   # 12/30, 17/35
    "DTW": [40, 220, 90, 270],     # 04/22, 09/27
    "FLL": [90, 270, 100, 280],    # 09/27, 10/28
    "PHL": [90, 270, 170, 350],    # 09/27, 17/35
    "LGA": [40, 220, 130, 310],    # 04/22, 13/31
    "BWI": [100, 280, 150, 330],   # 10/28, 15/33
    "DCA": [10, 190, 150, 330],    # 01/19, 15/33
    "SAN": [90, 270],               # 09/27
    "IAD": [10, 190, 120, 300],    # 01R/19L, 12/30
    "TPA": [10, 190, 100, 280],    # 01/19, 10/28
    "AUS": [170, 350],              # 17/35
    "BNA": [20, 200, 130, 310],    # 02/20, 13/31
    "MDW": [40, 220, 130, 310],    # 04/22, 13/31
    "HNL": [80, 260],               # 08/26
    "ABQ": [80, 260, 170, 350],    # 08/26, 17/35
}

# =============================================================================
# BUILDING TYPE CLASSIFICATION HEURISTICS
# =============================================================================
# Classification tiers based on distance from airport center + footprint area.
# Source: Airport design guidelines (FAA AC 150/5300-13B), typical airport layouts.
BUILDING_TYPE_THRESHOLDS = {
    # < 0.5 km from airport center
    "terminal":    {"max_dist_km": 0.5,  "min_area_m2": 3000},
    # 0.5–2.5 km, large footprints (>5000 m²)
    "hangar":      {"max_dist_km": 2.5,  "min_area_m2": 5000},
    # 0.5–3.0 km, medium-large
    "cargo":       {"max_dist_km": 3.0,  "min_area_m2": 2500},
    # > 1.5 km, medium footprints
    "hotel":       {"max_dist_km": 5.0,  "min_area_m2": 1500},
    # Default
    "commercial":  {"max_dist_km": 20.0, "min_area_m2": 500},
}

# Split incentive risk by building type:
# "low"  — airport authority owns and occupies (no landlord/tenant split)
# "high" — leased to separate tenant (airline, cargo co., hotel operator, etc.)
SPLIT_INCENTIVE_BY_TYPE = {
    "terminal":   "low",     # Airport authority owns & operates
    "hangar":     "high",    # Typically leased to airlines/MROs
    "cargo":      "high",    # Leased to FedEx, UPS, airlines
    "hotel":      "high",    # Separate hotel company (Marriott, Hilton, etc.)
    "commercial": "medium",  # Varies — could be airport-owned or leased
}

# Grant programs relevant to each building type
GRANT_PROGRAMS_BY_TYPE = {
    "terminal": ["FAA AIP (90% federal)", "IRS § 179D deduction", "IRA ITC adder"],
    "hangar":   ["FAA AIP (90% federal)", "IRA ITC adder"],
    "cargo":    ["FAA AIP (90% federal)", "IRA ITC adder", "FEMA BRIC"],
    "hotel":    ["IRA ITC (30%)", "MACRS 5-yr depreciation"],
    "commercial": ["IRA ITC (30%)", "MACRS 5-yr depreciation"],
}

# FAA AIP effective ITC boost: 90% federal cost share → effectively 90% "grant"
# When FAA AIP applies, actual customer cost = 10% of install_cost
# (only applies to airport property, i.e., terminals and hangars)
FAA_AIP_ELIGIBLE_TYPES = {"terminal", "hangar", "cargo"}
FAA_AIP_FEDERAL_SHARE = 0.90  # 90% of eligible project cost paid by FAA

# =============================================================================
# AIRPORT LATITUDE / LONGITUDE (for pvlib glare calculations)
# =============================================================================
AIRPORT_COORDS = {
    "ATL": (33.6407, -84.4277),   "DFW": (32.8998, -97.0403),
    "DEN": (39.8561, -104.6737),  "ORD": (41.9742, -87.9073),
    "LAX": (33.9425, -118.4081),  "JFK": (40.6413, -73.7781),
    "LAS": (36.0840, -115.1537),  "MCO": (28.4312, -81.3081),
    "CLT": (35.2140, -80.9431),   "SEA": (47.4502, -122.3088),
    "PHX": (33.4373, -112.0078),  "MIA": (25.7959, -80.2870),
    "IAH": (29.9902, -95.3368),   "SFO": (37.6213, -122.3790),
    "BOS": (42.3656, -71.0096),   "EWR": (40.6895, -74.1745),
    "MSP": (44.8848, -93.2223),   "DTW": (42.2162, -83.3554),
    "FLL": (26.0726, -80.1527),   "PHL": (39.8744, -75.2424),
    "LGA": (40.7772, -73.8726),   "BWI": (39.1754, -76.6683),
    "DCA": (38.8521, -77.0377),   "SAN": (32.7338, -117.1933),
    "IAD": (38.9531, -77.4565),   "TPA": (27.9755, -82.5332),
    "AUS": (30.1975, -97.6664),   "BNA": (36.1263, -86.6774),
    "MDW": (41.7868, -87.7522),   "HNL": (21.3187, -157.9225),
    "ABQ": (35.0402, -106.6090),
}

# =============================================================================
# SECTION 179D COMMERCIAL BUILDING ENERGY EFFICIENCY DEDUCTION (IRS)
# =============================================================================
# IRA-enhanced Section 179D: commercial buildings can deduct $5/sqft for
# systems achieving 50% energy savings. Solar qualifies as part of HVAC/lighting.
# Airport buildings as government/public property allow the designer/installer
# to claim the deduction (transferred deduction).
# Conservative estimate: $1.00/sqft net present value for commercial PV.
# Source: IRS Rev. Proc. 2023-33; Section 179D(d)(4) allocation
SECTION_179D_PER_M2 = 10.76  # $1/sqft × 10.76 sqft/m² → $10.76/m² of panel area

