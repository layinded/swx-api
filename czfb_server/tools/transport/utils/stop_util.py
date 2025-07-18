import csv
import os
from pathlib import Path
from math import radians, sin, cos, sqrt, atan2
from typing import List, Optional

import unicodedata
from rapidfuzz import process, fuzz
from collections import defaultdict

from czfb_server.model.schemas import StopMatch, Coordinates
from czfb_server.config.config import STOPS_FILE

BASE_DIR = Path(os.path.dirname(__file__)).parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data/fuzzystopwords"


def load_stops(filepath: str) -> list[StopMatch]:
    """
    Load a GTFS stop CSV file and convert each row into a `StopMatch` object.

    Args:
        filepath (str): Path to the GTFS stops CSV file (relative to DATA_DIR).

    Returns:
        list[StopMatch]: List of stops with structured fields for search and matching.
    """

    stops = []
    with (DATA_DIR / filepath).open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Convert and clean up types where necessary
            stop = StopMatch(
                stop_id=row["stop_id"],
                stop_name=row["stop_name"],
                latitude=_safe_float(row.get("stop_lat")),
                longitude=_safe_float(row.get("stop_lon")),
                zone_id=row.get("zone_id"),
                stop_url=row.get("stop_url"),
                location_type=_safe_int(row.get("location_type")),
                parent_station=row.get("parent_station"),
                wheelchair_boarding=_safe_int(row.get("wheelchair_boarding")),
                level_id=row.get("level_id"),
                platform_code=row.get("platform_code"),
                asw_node_id=row.get("asw_node_id"),
                asw_stop_id=row.get("asw_stop_id"),
                zone_region_type=row.get("zone_region_type")
            )
            stops.append(stop)
    return stops


def _safe_float(value: str | None) -> float | None:
    """
    Safely convert a string to float.

    Args:
        value (str | None): Input value.

    Returns:
        float | None: Parsed float if valid, else None.
    """

    try:
        return float(value) if value else None
    except ValueError:
        return None


def _safe_int(value: str | None) -> int | None:
    """
    Safely convert a string to int.

    Args:
        value (str | None): Input value.

    Returns:
        int | None: Parsed integer if valid, else None.
    """

    try:
        return int(value) if value else None
    except ValueError:
        return None


def normalize_text(text: str) -> str:
    """
    Normalize text by lowercasing and stripping Czech diacritics.

    Args:
        text (str): Input string (e.g., "Žižkov").

    Returns:
        str: ASCII-lowercased version (e.g., "zizkov").
    """

    """
    Lowercase and strip Czech diacritics.
    """
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8").lower()


def fuzzy_find_stop_ids(
    stops: List[StopMatch],
    query: str,
    threshold: int = 70,
    limit: int = 5
) -> List[StopMatch]:
    """
    Perform fuzzy text search against stop names using token sort ratio.

    Args:
        stops (List[StopMatch]): All known stops from GTFS data.
        query (str): User query (e.g., "Andel").
        threshold (int): Minimum match score to include (default: 70).
        limit (int): Max number of matches to return.

    Returns:
        List[StopMatch]: Best-matching stops, limited and sorted by relevance.
    """

    normalized_query = normalize_text(query)

    normalized_map = defaultdict(list)
    for stop in stops:
        if stop.stop_name:
            key = normalize_text(stop.stop_name)
            normalized_map[key].append(stop)

    normalized_names = list(normalized_map.keys())

    results = process.extract(
        normalized_query,
        normalized_names,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=threshold,
        limit=limit
    )

    matched_stops = []
    for key, score, _ in results:
        matched_stops.extend(normalized_map[key])

    return matched_stops[:limit]


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points using the Haversine formula.

    Args:
        lat1 (float): Latitude of point A.
        lon1 (float): Longitude of point A.
        lat2 (float): Latitude of point B.
        lon2 (float): Longitude of point B.

    Returns:
        float: Distance in meters.
    """

    R = 6371000  # Earth radius in meters
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def find_nearest_stop(
    coords: Coordinates,
    max_distance: int = 500
) -> Optional[StopMatch]:
    """
    Find the closest stop to the given coordinates within a maximum distance.

    Args:
        coords (Coordinates): Latitude and longitude of the query point.
        max_distance (int): Maximum search radius in meters (default: 500m).

    Returns:
        Optional[StopMatch]: Closest matching stop or None if none within radius.
    """

    stops = load_stops(STOPS_FILE)
    closest = None
    min_distance = float("inf")

    for stop in stops:
        if stop.latitude is None or stop.longitude is None:
            continue
        dist = haversine_distance(coords.latitude, coords.longitude, stop.latitude, stop.longitude)
        if dist < min_distance and dist <= max_distance:
            min_distance = dist
            closest = stop

    if closest:
        closest_copy = StopMatch(**closest.dict())
        closest_copy.distance = min_distance
        return closest_copy

    return None
