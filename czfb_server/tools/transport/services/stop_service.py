from typing import Annotated
from typing import Optional

from pydantic import Field

from czfb_server.config.config import STOPS_FILE
from czfb_server.model.schemas import StopMatch, Coordinates
from czfb_server.tools.transport.mcp_base import mcp_transport_tools as mcp
from czfb_server.tools.transport.utils.stop_util import (
    load_stops,
    fuzzy_find_stop_ids,
    find_nearest_stop,
    haversine_distance, normalize_text,
)


async def resolve_stop_ids(stop_name: str) -> list[StopMatch]:
    """
    Internal utility to fuzzy-match a stop name to GTFS stop IDs.

    Args:
        stop_name (str): Partial or full name of a stop.

    Returns:
        list[StopMatch]: A ranked list of best fuzzy matches from the GTFS data.
    """
    stops = load_stops(STOPS_FILE)
    return fuzzy_find_stop_ids(stops, stop_name)


@mcp.tool(
    name="reverse_geocode",
    description="Find the nearest known public transport stop to a given coordinate.",
    tags={"reverse-geocoding", "transport", "location"}
)
async def reverse_geocode(
        latitude: Annotated[float, Field(description="Latitude in decimal degrees")],
        longitude: Annotated[float, Field(description="Longitude in decimal degrees")]
) -> dict:
    """
    FastMCP tool that finds the closest GTFS stop to provided coordinates.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.

    Returns:
        dict: Includes:
            - place_name: Name of the nearest known stop.
            - coordinates: Dict with lat/lon.
            - distance_meters: Distance to stop.
            - speech_response: Spoken description.
    """

    nearest = find_nearest_stop(Coordinates(latitude=latitude, longitude=longitude))
    if not nearest:
        return {"speech_response": "No known stop found nearby."}

    return {
        "place_name": nearest.stop_name,
        "coordinates": {"lat": nearest.latitude, "lon": nearest.longitude},
        "distance_meters": int(float(nearest.distance)) if nearest.distance is not None else None,
        "speech_response": (
            f"The nearest known stop is {nearest.stop_name}, about "
            f"{int(float(nearest.distance)) if nearest.distance is not None else None} meters away."
        )
    }


@mcp.tool(
    name="list_all_stops",
    description="List all known public transport stops, optionally filtered by name or zone.",
    tags={"stops", "search", "transport"}
)
async def list_all_stops(
        name_contains: Annotated[Optional[str], Field(description="Partial match of stop name")] = None,
        zone: Annotated[Optional[str], Field(description="Exact zone ID to filter by")] = None
) -> dict:
    """
    Retrieve a list of public transport stops from the GTFS dataset.

    Args:
        name_contains (Optional[str]): Text to search for in stop names.
        zone (Optional[str]): GTFS zone_id to filter results.

    Returns:
        dict: Includes:
            - count: Number of matching stops.
            - stops: List of stop metadata (max 100).
            - speech_response: Summary.
    """

    stops = load_stops(STOPS_FILE)
    filtered = []

    for stop in stops:
        if name_contains and normalize_text(name_contains) not in normalize_text(stop.stop_name):
            continue
        if zone and stop.zone_id != zone:
            continue
        filtered.append(stop)

    return {
        "count": len(filtered),
        "stops": [s.dict(exclude_none=True) for s in filtered[:100]],
        "speech_response": f"Found {len(filtered)} matching stops."
    }


@mcp.tool(
    name="get_stop_metadata",
    description="Retrieve metadata for a specific stop by GTFS stop ID or name.",
    tags={"stop", "metadata", "lookup"}
)
async def get_stop_metadata(
        stop_id: Annotated[Optional[str], Field(description="Exact GTFS stop ID (e.g., 'U1234')")] = None,
        stop_name: Annotated[Optional[str], Field(description="Fuzzy name match (e.g., 'Dejvická')")] = None
) -> dict:
    """
    FastMCP tool to fetch full GTFS metadata for a given stop by ID or name.

    Args:
        stop_id (Optional[str]): Precise GTFS stop ID.
        stop_name (Optional[str]): Fuzzy-matchable stop name.

    Returns:
        dict: Includes:
            - metadata: Full stop metadata if found.
            - speech_response: Text summary of result or error.
    """
    # Defensive casting
    if stop_name and not isinstance(stop_name, str):
        stop_name = str(stop_name)
    if stop_id and not isinstance(stop_id, str):
        stop_id = str(stop_id)

    if not stop_id and not stop_name:
        return {"speech_response": "Please provide a stop name or ID."}

    stops = load_stops(STOPS_FILE)
    print(f"Loaded {len(stops)} stops")

    match = None
    if stop_id:
        match = next((s for s in stops if s.stop_id == stop_id), None)
    elif stop_name:
        normalized_query = normalize_text(stop_name)
        matches = fuzzy_find_stop_ids(stops, stop_name, threshold=70, limit=1)
        print(f"Query: {stop_name} → {normalized_query}")
        print(f"Matches: {[m.stop_name for m in matches]}")
        if matches:
            match = matches[0]

    if not match:
        return {"speech_response": f"No stop found matching '{stop_name or stop_id}'."}

    return {
        "metadata": match.dict(exclude_none=True),
        "speech_response": f"Details for stop {match.stop_name} retrieved."
    }


@mcp.tool(
    name="find_all_stops_near",
    description="Find all public transport stops within a radius around coordinates.",
    tags={"location", "transport", "radius"}
)
async def find_all_stops_near(
        latitude: Annotated[float, Field(description="Latitude in decimal degrees")],
        longitude: Annotated[float, Field(description="Longitude in decimal degrees")],
        radius: Annotated[int, Field(description="Search radius in meters (default 500)")] = 500
) -> dict:
    """
    Returns all GTFS stops located within a specified radius of the coordinates.

    Args:
        latitude (float): Latitude of search center.
        longitude (float): Longitude of search center.
        radius (int): Maximum distance in meters to include (default is 500m).

    Returns:
        dict: Includes:
            - count: Number of nearby stops found.
            - stops: List of matching stop metadata (max 50).
            - speech_response: Textual summary.
    """

    coords = Coordinates(latitude=latitude, longitude=longitude)
    stops = load_stops(STOPS_FILE)

    nearby = []
    for stop in stops:
        if stop.latitude is None or stop.longitude is None:
            continue
        dist = haversine_distance(coords.latitude, coords.longitude, stop.latitude, stop.longitude)
        if dist <= radius:
            stop.distance = dist
            nearby.append(stop)

    nearby.sort(key=lambda s: s.distance or 0)

    return {
        "count": len(nearby),
        "stops": [s.dict(exclude_none=True) for s in nearby[:50]],
        "speech_response": f"Found {len(nearby)} stops within {radius} meters."
    }
