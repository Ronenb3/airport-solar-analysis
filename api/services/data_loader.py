"""
Data loading service — handles all cache/file loading with proper caching.
"""

import copy
import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, List

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, mapping, Polygon
from pyproj import Transformer

from config import settings


logger = logging.getLogger(__name__)

# DATA_DIR: use DATA_DIR env var if set and the path actually exists,
# else resolve relative to source tree.
# This guards against stale Docker-era env vars on native Python deployments.
_env_data = os.environ.get("DATA_DIR")
_env_path = Path(_env_data) if _env_data else None
_repo_data = Path(__file__).parent.parent.parent / "data"
if _env_path and _env_path.exists():
    DATA_DIR = _env_path
else:
    DATA_DIR = _repo_data
BUILDINGS_DIR = DATA_DIR / "buildings"
AIRPORT_CACHE_DIR = DATA_DIR / "airport_cache"
AIRPORTS_FILE = DATA_DIR / "airports" / "top_30_airports.csv"

MAX_BUILDINGS = settings.MAX_BUILDINGS_RETURN


@lru_cache(maxsize=1)
def load_airports() -> list:
    """Load airports data — cached."""
    return pd.read_csv(AIRPORTS_FILE).to_dict("records")


def _round_float(v: float, decimals: int = 2) -> float:
    """Round floats for stable cache keys."""
    return round(v, decimals)


@lru_cache(maxsize=64)
def load_from_cache_v2(
    airport_code: str,
    radius_km_r: float,
    min_area_r: float,
) -> Optional[List[dict]]:
    """Load buildings from optimized JSON cache (precomputed area/distance)."""
    cache_file = DATA_DIR / "airport_cache_v2" / f"{airport_code}.json"
    if not cache_file.exists():
        return None

    try:
        with open(cache_file) as f:
            all_buildings = json.load(f)

        buildings = [
            b
            for b in all_buildings
            if b["distance_km"] <= radius_km_r and b["area_m2"] >= min_area_r
        ]
        buildings.sort(key=lambda x: x["area_m2"], reverse=True)
        return buildings[:MAX_BUILDINGS]
    except Exception as e:
        logger.warning(f"Cache v2 error for {airport_code}: {e}")
        return None


@lru_cache(maxsize=32)
def load_from_cache(
    airport_code: str,
    lat_r: float,
    lon_r: float,
    radius_km_r: float,
    min_area_r: float,
) -> Optional[List[dict]]:
    """Load buildings from pre-built airport GeoJSON cache."""
    cache_file = AIRPORT_CACHE_DIR / f"{airport_code}.geojson"
    if not cache_file.exists():
        return None

    try:
        gdf = gpd.read_file(cache_file, engine="pyogrio")
        if len(gdf) == 0:
            return []

        utm_zone = int((lon_r + 180) // 6) + 1
        utm_crs = f"EPSG:326{utm_zone:02d}" if lat_r >= 0 else f"EPSG:327{utm_zone:02d}"
        transformer = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)
        ax, ay = transformer.transform(lon_r, lat_r)
        airport_pt = Point(ax, ay)

        buildings = []
        for _, row in gdf.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            centroid = geom.centroid
            cx, cy = transformer.transform(centroid.x, centroid.y)
            dist = Point(cx, cy).distance(airport_pt)
            if dist > radius_km_r * 1000:
                continue
            if geom.geom_type == "Polygon":
                coords = list(geom.exterior.coords)
                utm_coords = [transformer.transform(x, y) for x, y in coords]
                area = Polygon(utm_coords).area
            elif geom.geom_type == "MultiPolygon":
                area = sum(
                    Polygon([transformer.transform(x, y) for x, y in p.exterior.coords]).area
                    for p in geom.geoms
                )
            else:
                continue
            if area >= min_area_r:
                buildings.append(
                    {
                        "geometry": mapping(geom),
                        "area_m2": round(area, 1),
                        "distance_km": round(dist / 1000, 3),
                        "lat": round(centroid.y, 6),
                        "lon": round(centroid.x, 6),
                    }
                )

        buildings.sort(key=lambda x: x["area_m2"], reverse=True)
        return buildings[:MAX_BUILDINGS]
    except Exception as e:
        logger.warning(f"Cache error for {airport_code}: {e}")
        return None


@lru_cache(maxsize=32)
def load_buildings_from_state(
    state: str,
    lat_r: float,
    lon_r: float,
    radius_km_r: float,
    min_area_r: float,
):
    """Load and filter buildings from state-level GeoJSON. Slowest path."""
    file_state = state.replace(" ", "")
    state_file = BUILDINGS_DIR / f"{file_state}.geojson"
    zip_file = BUILDINGS_DIR / f"{file_state}.geojson.zip"

    if not state_file.exists() and not zip_file.exists():
        return None, f"Building data not available for {state}"

    deg_per_km = 1 / 111.0
    buffer = radius_km_r * deg_per_km * 1.5
    bbox = (lon_r - buffer, lat_r - buffer, lon_r + buffer, lat_r + buffer)

    try:
        if state_file.exists():
            gdf = gpd.read_file(state_file, bbox=bbox, engine="pyogrio")
        else:
            gdf = gpd.read_file(f"zip://{zip_file}", bbox=bbox, engine="pyogrio")

        if len(gdf) == 0:
            return None, "No buildings found in this area"

        utm_zone = int((lon_r + 180) // 6) + 1
        utm_crs = f"EPSG:326{utm_zone:02d}" if lat_r >= 0 else f"EPSG:327{utm_zone:02d}"
        transformer = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)
        ax, ay = transformer.transform(lon_r, lat_r)
        airport_pt = Point(ax, ay)

        buildings = []
        for _, row in gdf.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            centroid = geom.centroid
            cx, cy = transformer.transform(centroid.x, centroid.y)
            dist = Point(cx, cy).distance(airport_pt)
            if dist > radius_km_r * 1000:
                continue
            if geom.geom_type == "Polygon":
                coords = list(geom.exterior.coords)
                utm_coords = [transformer.transform(x, y) for x, y in coords]
                area = Polygon(utm_coords).area
            elif geom.geom_type == "MultiPolygon":
                area = sum(
                    Polygon([transformer.transform(x, y) for x, y in p.exterior.coords]).area
                    for p in geom.geoms
                )
            else:
                continue
            if area >= min_area_r:
                buildings.append(
                    {
                        "geometry": mapping(geom),
                        "area_m2": round(area, 1),
                        "distance_km": round(dist / 1000, 3),
                        "lat": round(centroid.y, 6),
                        "lon": round(centroid.x, 6),
                    }
                )

        buildings.sort(key=lambda x: x["area_m2"], reverse=True)
        return buildings[:MAX_BUILDINGS], None
    except Exception as e:
        return None, f"Error loading data: {str(e)}"


def get_buildings_for_airport(airport: dict, radius: float, min_size: float) -> tuple:
    """
    Try all cache tiers for an airport, returning (buildings, error).
    Rounds float params for stable cache keys.
    """
    code = airport["code"]
    lat = round(float(airport["lat"]), 4)
    lon = round(float(airport["lon"]), 4)
    radius_r = round(radius, 2)
    min_size_r = round(min_size, 1)

    # Tier 1: v2 JSON cache
    buildings = load_from_cache_v2(code, radius_r, min_size_r)
    if buildings is not None:
        return copy.deepcopy(buildings), None

    # Tier 2: v1 GeoJSON cache
    buildings = load_from_cache(code, lat, lon, radius_r, min_size_r)
    if buildings is not None:
        return copy.deepcopy(buildings), None

    # Tier 3: raw state file
    buildings, error = load_buildings_from_state(
        airport["state"], lat, lon, radius_r, min_size_r
    )
    if buildings is not None:
        return copy.deepcopy(buildings), error
    return buildings, error
