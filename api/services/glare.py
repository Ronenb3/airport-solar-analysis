"""
FAA Solar Glare Analysis Service — pvlib-based specular reflection model.

Methodology (based on FAA Technical Guidance for Evaluating Solar Technologies
on Airports, 2013, and Sandia Report SAND2013-5426 "Solar Glare Hazard Analysis
Tool for FAA"):

1. For each hour of a representative meteorological year, compute solar position
   (elevation, azimuth) using pvlib at the airport lat/lon.

2. Compute the specular reflection direction from a flat tilted panel
   (tilt=10°, azimuth=180° south-facing — standard commercial rooftop config).

3. Check if the reflected beam would be visible to a pilot or ATC:
   - Reflected elevation in [-5°, 30°] (eye-level hazard zone)
   - Reflected azimuth within ±50° of any primary runway heading

4. Count annual glare hours → classify as low / moderate / high.

Panel normal convention (East, North, Up):
   n = (0, -sin(tilt), cos(tilt)) for south-facing at 10° tilt
     = (0, -0.1736, 0.9848)

Solar unit vector (incoming radiation direction, pointing FROM sun TO panel):
   sun_inc = (-cos(el)*sin(az), -cos(el)*cos(az), -sin(el))
   where az measured from North clockwise.

Reflected beam (Snell's law specular):
   r = sun_inc - 2*(sun_inc · n) * n
   then r points FROM panel outward toward potential observer.
"""

from __future__ import annotations

import logging
import math
from functools import lru_cache
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Panel tilt and azimuth (standard commercial rooftop)
PANEL_TILT_DEG = 10.0
PANEL_AZIMUTH_DEG = 180.0  # south-facing

# Precompute panel normal in (East, North, Up)
_tilt_r = math.radians(PANEL_TILT_DEG)
_az_r = math.radians(PANEL_AZIMUTH_DEG - 180.0)  # 0 = tilted north, 180 = tilted south
PANEL_NORMAL = np.array([
    math.sin(_tilt_r) * math.sin(_az_r),   # East component
    -math.sin(_tilt_r) * math.cos(_az_r),  # North component  (south-facing → negative N)
    math.cos(_tilt_r),                      # Up component
], dtype=float)
# For az=180° (south): sin(0)=0, cos(0)=1 → n = (0, -0.1736, 0.9848) ✓
PANEL_NORMAL /= np.linalg.norm(PANEL_NORMAL)

# Maximum cone angle from runway centerline to consider a glare threat (degrees)
RUNWAY_CORRIDOR_HALF_ANGLE = 50.0

# Reflected elevation range that poses pilot eye-level hazard
REFLECTED_EL_MIN = -5.0   # degrees (slightly below horizon — low-flying approach)
REFLECTED_EL_MAX = 30.0   # degrees (30° elevation = ~3nm from runway threshold)


def _solar_to_enu(el_deg: float, az_deg: float) -> np.ndarray:
    """
    Convert solar position (elevation, azimuth from North CW) to a unit vector
    pointing FROM the observer TO the sun, in ENU (East, North, Up) frame.
    """
    el = math.radians(el_deg)
    az = math.radians(az_deg)
    return np.array([
        math.cos(el) * math.sin(az),  # East
        math.cos(el) * math.cos(az),  # North
        math.sin(el),                  # Up
    ])


def _reflected_beam(sun_to_observer: np.ndarray, normal: np.ndarray) -> np.ndarray:
    """
    Compute specular reflection direction.

    Parameters
    ----------
    sun_to_observer : unit vector pointing FROM sun TOWARD panel (incoming ray)
    normal : surface normal (already normalized)

    Returns
    -------
    Reflected beam direction FROM panel TOWARD observer.
    """
    # Incoming ray = direction FROM sun TO panel = -sun_enu
    incident = -sun_to_observer
    dot = float(np.dot(incident, normal))
    reflected = incident - 2.0 * dot * normal
    norm = np.linalg.norm(reflected)
    return reflected / norm if norm > 1e-9 else reflected


def _vec_to_az_el(v: np.ndarray) -> tuple[float, float]:
    """Convert ENU unit vector to (azimuth_deg, elevation_deg)."""
    el = math.degrees(math.asin(float(np.clip(v[2], -1.0, 1.0))))
    az = math.degrees(math.atan2(float(v[0]), float(v[1]))) % 360.0
    return az, el


def _angle_diff(a: float, b: float) -> float:
    """Absolute angular difference in degrees, wrapped to [0, 180]."""
    diff = abs((a - b + 180.0) % 360.0 - 180.0)
    return diff


@lru_cache(maxsize=256)
def calc_glare_risk(
    airport_code: str,
    lat: float,
    lon: float,
    runways: tuple,         # tuple of runway heading floats (hashable)
    panel_tilt: float = PANEL_TILT_DEG,
    panel_az: float = PANEL_AZIMUTH_DEG,
) -> dict:
    """
    Calculate annual glare-hours for a solar panel at (lat, lon)
    in the context of the given airport runway headings.

    Samples hourly solar position over a representative year (monthly middays)
    to estimate glare exposure without running a full 8760h simulation.

    Parameters
    ----------
    airport_code : str
        3-letter airport code (informational).
    lat, lon : float
        Panel location (building centroid).
    runways : tuple of float
        Runway headings in degrees true.
    panel_tilt, panel_az : float
        Panel geometry (defaulting to standard 10°/south).

    Returns
    -------
    dict with risk_level, glare_hours_per_year, worst_months, description
    """
    try:
        import pvlib
    except ImportError:
        logger.warning("pvlib not installed — returning distance-based fallback")
        return {"risk_level": "unknown", "glare_hours_per_year": 0, "pvlib": False}

    # Recompute panel normal if non-default geometry
    if panel_tilt != PANEL_TILT_DEG or panel_az != PANEL_AZIMUTH_DEG:
        tilt_r = math.radians(panel_tilt)
        az_r = math.radians(panel_az - 180.0)
        n = np.array([
            math.sin(tilt_r) * math.sin(az_r),
            -math.sin(tilt_r) * math.cos(az_r),
            math.cos(tilt_r),
        ], dtype=float)
        n /= np.linalg.norm(n)
    else:
        n = PANEL_NORMAL.copy()

    # Build set of timestamps: every hour for 12 representative days
    # (15th of each month) — 12 × 24 = 288 samples
    import pandas as pd
    tz_str = _tz_for_lon(lon)
    timestamps = []
    for month in range(1, 13):
        for hour in range(0, 24):
            timestamps.append(
                pd.Timestamp(2024, month, 15, hour, 0, 0, tz=tz_str)
            )
    times = pd.DatetimeIndex(timestamps)

    loc = pvlib.location.Location(latitude=lat, longitude=lon, tz=tz_str, altitude=300)
    solar_pos = loc.get_solarposition(times)

    glare_hours = 0
    monthly_glare: dict[int, int] = {}

    for i, (_, row) in enumerate(solar_pos.iterrows()):
        el = float(row["apparent_elevation"])
        az = float(row["azimuth"])

        # Only care about daytime (sun above horizon)
        if el <= 0.5:
            continue

        # Compute sun unit vector (FROM sun TO observer)
        sun_enu = _solar_to_enu(el, az)

        # Reflected beam direction
        r = _reflected_beam(sun_enu, n)
        r_az, r_el = _vec_to_az_el(r)

        # Check elevation: must be in pilot eye-level hazard range
        if not (REFLECTED_EL_MIN <= r_el <= REFLECTED_EL_MAX):
            continue

        # Check azimuth: must be within corridor of any runway heading
        for heading in runways:
            if _angle_diff(r_az, heading) <= RUNWAY_CORRIDOR_HALF_ANGLE:
                glare_hours += 1
                month_idx = times[i].month
                monthly_glare[month_idx] = monthly_glare.get(month_idx, 0) + 1
                break  # count this timeslot once, even if multiple runways match

    # Scale from 12-day sample to annual estimate
    # Each month represented by 1 day → multiply by avg days/month (~30.4)
    glare_hours_annual = int(glare_hours * 30.4 / 24)

    # Worst months
    worst_months = sorted(
        [_MONTH_NAMES[m - 1] for m, cnt in monthly_glare.items() if cnt > 0],
        key=lambda m: monthly_glare.get(_MONTH_NAMES.index(m) + 1, 0),
        reverse=True,
    )[:3]

    # Risk classification
    if glare_hours_annual >= 100:
        risk_level = "high"
        description = f"~{glare_hours_annual} glare-hrs/yr toward runway corridor. FAA analysis required."
    elif glare_hours_annual >= 25:
        risk_level = "moderate"
        description = f"~{glare_hours_annual} glare-hrs/yr. Low-level pilot exposure possible."
    else:
        risk_level = "low"
        description = f"~{glare_hours_annual} glare-hrs/yr. Minimal FAA concern expected."

    return {
        "risk_level": risk_level,
        "glare_hours_per_year": glare_hours_annual,
        "worst_months": worst_months,
        "description": description,
        "pvlib": True,
        "method": "specular_reflection_Sandia_SAND2013-5426",
    }


_MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def _tz_for_lon(lon: float) -> str:
    """Approximate IANA timezone from longitude (good enough for pvlib inputs)."""
    # US continental rough mapping
    if lon < -140:     return "Pacific/Honolulu"
    elif lon < -115:   return "America/Los_Angeles"
    elif lon < -100:   return "America/Denver"
    elif lon < -85:    return "America/Chicago"
    elif lon < -67:    return "America/New_York"
    else:              return "UTC"


def classify_glare_risk_fast(distance_km: float, runways: Optional[list] = None) -> str:
    """
    Fast distance-based fallback when pvlib is unavailable or for distant buildings.
    """
    from solar_constants import GLARE_RISK_THRESHOLDS
    if distance_km <= GLARE_RISK_THRESHOLDS["high"]:
        return "high"
    elif distance_km <= GLARE_RISK_THRESHOLDS["moderate"]:
        return "moderate"
    else:
        return "low"
