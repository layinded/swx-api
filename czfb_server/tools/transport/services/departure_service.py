import json
from collections import defaultdict
from datetime import datetime
from typing import Optional, Annotated

import dateparser
import httpx
from pydantic import Field

from czfb_server.config.config import GOLEMIO_API_KEY
from czfb_server.model.schemas import Coordinates
from czfb_server.tools.transport.mcp_base import mcp_transport_tools as mcp
from czfb_server.tools.transport.services.geocoding_service import geocode_location
from czfb_server.tools.transport.summarizers import summarize_departures_speech
from czfb_server.tools.transport.utils.stop_util import find_nearest_stop


def build_departureboard_params(
        stop_id: str,
        asw_id_node: Optional[int],
        when: Optional[str] = None,
        arrive_by: Optional[str] = None,
        default_minutes_after: int = 30
) -> dict:
    """
    Build Golemio PID departure board API query parameters.

    This function prepares the query parameters used to fetch real-time
    departure or arrival data from Golemio based on the provided stop information,
    time constraints, and arrival mode. It supports planning for either departing
    or arriving by a specific time and adjusts time windows accordingly.

    Args:
        stop_id (str): The GTFS stop ID (e.g., 'U689Z1P') used for departure mode queries.
        asw_id_node (Optional[int]): The ASW node ID used for arrival mode queries (e.g., 689).
        when (Optional[str]): Desired departure time (natural language format, e.g., 'in 10 minutes', 'at 8am').
        arrive_by (Optional[str]): Desired arrival deadline (e.g., 'by 7:45am').
        default_minutes_after (int): Time window (in minutes) for future departures or past arrivals.

    Returns:
        dict: Dictionary of query parameters to be sent to the Golemio `/departureboards` endpoint.
              Includes keys like `timeFrom`, `mode`, `ids[]` or `aswIds[]`, and time filters (`minutesAfter` or `minutesBefore`).
    """

    now = datetime.now()
    time_from = now
    minutes_before = 0
    minutes_after = default_minutes_after
    mode = "departures"

    if arrive_by:
        parsed = dateparser.parse(arrive_by)
        if parsed:
            mode = "arrivals"
            time_from = parsed
            minutes_before = default_minutes_after
            minutes_after = 0

    elif when:
        parsed = dateparser.parse(when)
        if parsed:
            time_from = parsed
            delta = int((parsed - now).total_seconds() // 60)
            minutes_after = max(min(delta, 360), 1)

    params = {
        "limit": 20,
        "preferredTimezone": "Europe/Prague",
        "filter": "routeHeadingOnceFill",
        "timeFrom": time_from.isoformat(),
        "mode": mode,
    }

    if mode == "arrivals" and asw_id_node:
        params["aswIds[]"] = [str(asw_id_node)]
        params["minutesBefore"] = minutes_before
    else:
        params["ids[]"] = [stop_id]
        params["minutesAfter"] = minutes_after

    return params


async def get_departures_info(
        stop_name: str,
        when: Optional[str] = None,
        arrive_by: Optional[str] = None,
        mode: Optional[str] = None
) -> dict[str, Optional[str]]:
    """
    Retrieve upcoming public transport departures or arrivals from a named stop.

    This function performs stop name geocoding, finds the nearest GTFS stop, builds
    a query to the Golemio PID `departureboards` API, and formats the result into
    grouped text for both UI and speech response. Optionally filters results by mode
    (tram, metro, or bus), and supports both `depart after` and `arrive by` queries.

    Args:
        stop_name (str): Natural language name of the stop (e.g., "Anděl").
        when (Optional[str]): Desired departure time (e.g., "now", "in 20 minutes", "at 14:00").
        arrive_by (Optional[str]): Desired arrival deadline (e.g., "by 7:30am", "at 9:00").
        mode (Optional[str]): Optional transport mode filter ('bus', 'tram', or 'metro').

    Returns:
        dict[str, Optional[str]]: Dictionary with:
            - "departures" (str | None): Formatted multiline text of grouped departures.
            - "speech_response" (str): Condensed speech-friendly summary of departures.
            - "fallback" (bool): True if fallback location was used (e.g., coarse geocode).
    """

    result = {
        "departures": None,
        "speech_response": f"No stops found matching '{stop_name}'.",
        "fallback": False,
    }

    # Geocode stop name → coords → nearest GTFS stop
    geocode_result = await geocode_location(stop_name)
    if not geocode_result:
        return result

    coords, used_fallback = geocode_result
    nearest = find_nearest_stop(coords)
    if not nearest:
        return {
            **result,
            "speech_response": f"Could not find any known stop near '{stop_name}'.",
            "fallback": used_fallback
        }

    # Prepare API query parameters
    params = build_departureboard_params(
        stop_id=nearest.stop_id,
        asw_id_node=nearest.asw_node_id,
        when=when,
        arrive_by=arrive_by
    )
    url = "https://api.golemio.cz/v2/pid/departureboards"
    headers = {"X-Access-Token": GOLEMIO_API_KEY}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return {
            **result,
            "speech_response": f"Error retrieving departures: {e}",
            "fallback": used_fallback
        }

    departures = data.get("departures", [])
    if not departures:
        return {
            **result,
            "speech_response": f"No departures found from {nearest.stop_name}.",
            "fallback": used_fallback
        }

    # Filter by transport mode
    mode_map = {"tram": 0, "metro": 1, "bus": 3}
    if mode and mode in mode_map:
        desired_type = mode_map[mode]
        departures = [d for d in departures if d.get("route", {}).get("type") == desired_type]

    # Group and format
    grouped = defaultdict(list)
    for dep in departures:
        stop = dep.get("stop", {})
        stop_id = stop.get("id", "Unknown")
        platform = stop.get("platform_code") or "N/A"
        group_key = (stop_id, platform)

        route = dep.get("route", {}).get("short_name", "N/A")
        headsign = dep.get("trip", {}).get("headsign", "N/A")
        timestamp_raw = (
                dep.get("departure_timestamp", {}).get("predicted")
                or dep.get("departure_timestamp", {}).get("scheduled")
        )
        timestamp = datetime.fromisoformat(timestamp_raw).strftime("%H:%M") if timestamp_raw else "N/A"
        grouped[group_key].append(f"• Line {route} to {headsign} at {timestamp}")

    output = []
    for (stop_id, platform), lines in grouped.items():
        output.append(f"🚏 {stop_id} [Platform {platform}]")
        output.extend(lines)
        output.append("")

    departures_text = "\n".join(output).strip()
    speech = summarize_departures_speech(nearest.stop_name, departures_text)
    if used_fallback:
        speech += " (approximate location used)"

    return {
        "departures": departures_text,
        "speech_response": speech,
        "fallback": used_fallback
    }


@mcp.tool(
    name="get_departures",
    description="Get upcoming departures or arrivals from a public transport stop. Accepts time filters and optional mode.",
    tags={"departures", "transport", "schedule"}
)
async def get_departures(
        stop_name: Annotated[str, Field(description="Name of the public transport stop (e.g., 'Anděl')")],
        when: Annotated[
            Optional[str],
            Field(description="Desired departure time (e.g., 'now', 'in 30 minutes', or 'at 7am')"),
        ] = None,
        arrive_by: Annotated[
            Optional[str],
            Field(description="Desired arrival deadline (e.g., 'by 8am', 'at 14:30')"),
        ] = None,
        mode: Annotated[
            Optional[str],
            Field(description="Optional transport mode filter: 'bus', 'tram', or 'metro'"),
        ] = None,
) -> dict:
    """
    MCP tool to fetch upcoming public transport departures (or arrivals) from a specific stop.

    This tool geocodes the stop name, queries the Golemio PID API, filters by departure time or
    arrival deadline, and returns both a formatted list of departures and a summarized speech response.

    Args:
        stop_name (str): Name of the stop to query.
        when (Optional[str]): Desired departure time in natural language (e.g., "in 20 minutes", "at 8am").
        arrive_by (Optional[str]): Desired arrival deadline (e.g., "by 7:45am").
        mode (Optional[str]): Filter results by transport mode: "tram", "metro", or "bus".

    Returns:
        dict: {
            "stop_name" (str): Name of the stop used,
            "departures" (str | None): Formatted departure lines for display (grouped by stop+platform),
            "speech_response" (str): Speech-ready summary of the next departures,
            "fallback" (bool): True if fallback geolocation was used
        }
    """
    data = await get_departures_info(stop_name=stop_name, when=when, arrive_by=arrive_by, mode=mode)
    return {
        "stop_name": stop_name,
        "departures": data.get("departures"),
        "speech_response": data.get("speech_response"),
        "fallback": data.get("fallback", False),
    }


@mcp.tool(
    name="departures_by_coordinates",
    description="Find the nearest public transport stop by coordinates and show upcoming departures.",
    tags={"location", "departures", "coordinates"}
)
async def departures_by_coordinates(
        latitude: Annotated[
            float,
            Field(description="Latitude in decimal degrees")
        ],
        longitude: Annotated[
            float,
            Field(description="Longitude in decimal degrees")
        ]
) -> dict:
    """
    FastMCP tool to retrieve upcoming departures from the nearest stop to the given coordinates.

    Uses coordinate-based geolocation to find the closest known public transport stop and
    retrieves its upcoming departures.

    Args:
        latitude (float): Latitude of the location in decimal degrees.
        longitude (float): Longitude of the location in decimal degrees.

    Returns:
        dict: A structured response including:
            - stop_name: Nearest stop name.
            - departures: Formatted list of upcoming departures.
            - speech_response: Summary for conversational delivery.
            - coordinates: Dictionary with latitude and longitude.
            - distance_meters: Approximate distance from input location to stop.
            - fallback: Whether fallback geolocation was used.
    """
    coords = Coordinates(latitude=latitude, longitude=longitude)
    nearest = find_nearest_stop(coords)
    if not nearest:
        return {"speech_response": "No nearby stop found for departures."}

    data = await get_departures_info(nearest.stop_name)

    return {
        "stop_name": nearest.stop_name,
        "departures": data.get("departures"),
        "speech_response": data.get("speech_response", f"No departures available from {nearest.stop_name}."),
        "coordinates": {
            "lat": nearest.latitude,
            "lon": nearest.longitude
        },
        "distance_meters": int(float(nearest.distance)) if nearest.distance is not None else None,
        "fallback": data.get("fallback", False)
    }
