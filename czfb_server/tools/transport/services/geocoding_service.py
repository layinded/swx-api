from typing import Optional, Annotated
from pydantic import Field
import httpx
from async_lru import alru_cache
from czfb_server.tools.transport.mcp_base import mcp_transport_tools as mcp
from czfb_server.config.config import STOPS_FILE, NOMINATIM_URL
from czfb_server.model.schemas import Coordinates
from czfb_server.tools.transport.utils.stop_util import load_stops, fuzzy_find_stop_ids


@alru_cache(maxsize=128)
async def geocode_location(name: str) -> Optional[tuple[Coordinates, bool]]:
    """
    Resolve a place name to geographic coordinates using a two-step fallback strategy.

    First attempts GTFS fuzzy matching of known stop names. If no match is found,
    falls back to Nominatim geocoding (OpenStreetMap).

    Args:
        name (str): Place or stop name (e.g., "Florenc", "Karlovo náměstí").

    Returns:
        Optional[tuple[Coordinates, bool]]:
            - Coordinates object (latitude, longitude)
            - Boolean flag indicating whether fallback method was used

        Returns None if both GTFS and Nominatim fail to resolve the name.
    """
    stops = load_stops(STOPS_FILE)
    matches = fuzzy_find_stop_ids(stops, name, threshold=70, limit=1)
    if matches:
        best = matches[0]
        return Coordinates(latitude=best.latitude, longitude=best.longitude), False

    print(f"⚠️ GTFS match failed for '{name}', trying Nominatim...")
    result = await geocode_with_nominatim(name)
    if result:
        return result  # already (Coordinates, True)

    return None


@mcp.tool(
    name="geocode",
    description="Convert a place or stop name into coordinates using GTFS matching or OpenStreetMap fallback.",
    tags={"location", "geocoding", "coordinates"}
)
async def geocode(
        name: Annotated[
            str,
            Field(description="Name of the place or public transport stop (e.g., 'Florenc')")
        ]
) -> dict:
    """
    FastMCP tool wrapper for `geocode_location`.

    Attempts to resolve a human-friendly stop name into latitude and longitude.
    Uses GTFS fuzzy matching first, and falls back to Nominatim (OSM) if needed.

    Args:
        name (str): Location or stop name.

    Returns:
        dict: A structured response containing:
            - coordinates: {"lat": float, "lon": float} if resolved; None otherwise.
            - speech_response: A spoken summary of the result.
            - fallback: Boolean indicating if fallback method (Nominatim) was used.
    """
    result = await geocode_location(name)
    if not result:
        return {
            "coordinates": None,
            "speech_response": f"Could not geocode '{name}'."
        }

    coords, used_fallback = result
    return {
        "coordinates": {"lat": coords.latitude, "lon": coords.longitude},
        "speech_response": (
                f"{name} is located at latitude {coords.latitude:.5f} "
                f"and longitude {coords.longitude:.5f}."
                + (" (approximate location)" if used_fallback else "")
        ),
        "fallback": used_fallback
    }


async def geocode_with_nominatim(name: str) -> Optional[tuple[Coordinates, bool]]:
    """
    Perform fallback geocoding via the Nominatim API (OpenStreetMap).

    Args:
        name (str): Free-text location or stop name.

    Returns:
        Optional[tuple[Coordinates, bool]]:
            - Coordinates object with lat/lon from Nominatim result.
            - Always returns `True` for the fallback flag if successful.

        Returns None if no results are found or an error occurs.
    """
    params = {"q": name, "format": "json", "limit": 1}
    headers = {"User-Agent": "Czech-Transport-Assistant/1.0"}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{NOMINATIM_URL}/search", params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            results = resp.json()
    except Exception as e:
        print(f"🌐 Nominatim geocoding failed for '{name}': {e}")
        return None

    if not results:
        print(f"🌐 Nominatim found no result for '{name}'")
        return None

    coords = Coordinates(
        latitude=float(results[0]["lat"]),
        longitude=float(results[0]["lon"])
    )
    return coords, True
