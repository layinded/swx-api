from datetime import datetime
from typing import Optional, Union, Annotated
from pydantic import Field

import dateparser
import httpx
from czfb_server.tools.transport.mcp_base import mcp_transport_tools as mcp
from czfb_server.config.config import OTP_URL
from czfb_server.model.schemas import Coordinates
from czfb_server.tools.transport.services.geocoding_service import geocode_location


def _summarize_trip_for_speech(pattern: dict) -> str:
    """
    Generates a short spoken summary for a trip pattern.

    Extracts key trip details like origin, destination, and start time to form a natural-language sentence.

    Args:
        pattern (dict): A trip pattern object from the OTP API.

    Returns:
        str: Human-readable trip summary suitable for voice output.
    """
    try:
        start = pattern.get("expectedStartTime", "soon")
        first_leg = pattern.get("legs", [])[0]
        last_leg = pattern.get("legs", [])[-1]
        origin = first_leg.get("fromPlace", {}).get("name", "origin")
        destination = last_leg.get("toPlace", {}).get("name", "destination")
        duration = "about " + str(len(pattern.get("legs", [])) * 5) + " minutes"
        return f"Your trip from {origin} to {destination} starts at {start} and takes {duration}."
    except Exception:
        return "Trip details found but could not generate summary."


async def plan_trip(
    from_coords: Coordinates,
    to_coords: Coordinates,
    planned_time: Optional[datetime] = None
) -> dict[str, Union[str, int, list[str]]]:
    """
    Query the OpenTripPlanner (OTP) backend to generate a public transport plan between two coordinates.

    Args:
        from_coords (Coordinates): Origin point.
        to_coords (Coordinates): Destination point.
        planned_time (Optional[datetime]): Optional departure datetime. If not provided, uses ASAP.

    Returns:
        dict:
            - trip_plans: List of human-readable leg-by-leg trip descriptions.
            - speech_response: Short spoken summary of the trip.
            - total_trips: Count of trip alternatives found.
    """

    date_time_str = planned_time.isoformat() if planned_time else None

    trip_args = f"""
        from: {{
            coordinates: {{latitude: {from_coords.latitude}, longitude: {from_coords.longitude}}}
        }},
        to: {{
            coordinates: {{latitude: {to_coords.latitude}, longitude: {to_coords.longitude}}}
        }}
    """
    if date_time_str:
        trip_args += f', dateTime: "{date_time_str}"'

    query = {
        "query": f"""
        query {{
          trip(
            {trip_args}
          ) {{
            tripPatterns {{
              expectedStartTime
              legs {{
                mode
                expectedStartTime
                expectedEndTime
                line {{
                  publicCode
                  name
                }}
                fromPlace {{
                  name
                }}
                toPlace {{
                  name
                }}
              }}
            }}
          }}
        }}
        """
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(OTP_URL, json=query, timeout=20)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return {
            "trip_plans": [],
            "speech_response": f"Failed to fetch trip plan: {str(e)}",
            "total_trips": 0
        }

    patterns = data.get("data", {}).get("trip", {}).get("tripPatterns", [])
    if not patterns:
        return {
            "trip_plans": [],
            "speech_response": "No trip found for the given route.",
            "total_trips": 0
        }

    detailed_plans = []
    speech_summaries = []

    for pattern in patterns:
        legs_text = []
        for leg in pattern.get("legs", []):
            mode = leg.get("mode", "UNKNOWN")
            line = leg.get("line", {})
            line_info = f"{line.get('publicCode', '')} ({line.get('name', '')})" if line else ""
            from_name = leg.get("fromPlace", {}).get("name", "Unknown")
            to_name = leg.get("toPlace", {}).get("name", "Unknown")
            dep = leg.get("expectedStartTime", "N/A")
            arr = leg.get("expectedEndTime", "N/A")
            legs_text.append(f"{mode} {line_info}: {from_name} ({dep}) → {to_name} ({arr})")
        detailed_plans.append("\n".join(legs_text))
        speech_summaries.append(_summarize_trip_for_speech(pattern))

    return {
        "trip_plans": detailed_plans,
        "speech_response": speech_summaries[0] if speech_summaries else "Trip found.",
        "total_trips": len(patterns)
    }

@mcp.tool(
    name="plan_trip_between",
    description="Plan a public transport route between two named locations. Uses OTP backend.",
    tags={"trip", "planner", "routing", "transport"}
)
async def plan_trip_between(
    from_place: Annotated[
        str,
        Field(description="Name of the origin location (e.g., 'Florenc')")
    ],
    to_place: Annotated[
        str,
        Field(description="Name of the destination (e.g., 'Karlovo náměstí')")
    ],
    departure_time: Annotated[
        Optional[str],
        Field(description="Optional departure time in ISO format or natural language (e.g., 'in 15 minutes')")
    ] = None
) -> dict[str, Union[str, int, list[str], dict]]:
    """
    FastMCP tool to plan a trip between two place names.

    Resolves each place name into coordinates using geocoding, optionally parses the departure time,
    then queries the OTP trip planner backend to get public transport routes.

    Args:
        from_place (str): Human-friendly origin name.
        to_place (str): Human-friendly destination name.
        departure_time (Optional[str]): Optional departure time ("2025-07-18T09:00" or "in 1 hour").

    Returns:
        dict:
            - trip_plans: List of leg-by-leg route descriptions.
            - planned_time: Parsed time or "ASAP".
            - speech_response: Short summary of the trip.
            - total_trips: Number of trip options found.
            - fallback: Flags indicating whether fallback geocoding was used for origin or destination.
    """

    from_result = await geocode_location(from_place)
    to_result = await geocode_location(to_place)

    if not from_result or not to_result:
        return {
            "trip_plans": [],
            "speech_response": "Sorry, I couldn't resolve both locations.",
            "total_trips": 0,
            "fallback": {"from": None, "to": None}
        }

    from_coords, from_fallback = from_result
    to_coords, to_fallback = to_result

    planned_time: Optional[datetime] = None
    if departure_time:
        try:
            planned_time = datetime.fromisoformat(departure_time)
        except ValueError:
            planned_time = dateparser.parse(
                departure_time,
                settings={"TIMEZONE": "UTC", "RETURN_AS_TIMEZONE_AWARE": True}
            )

    if departure_time and not planned_time:
        return {
            "trip_plans": [],
            "planned_time": "ASAP",
            "speech_response": "Invalid time format. Use ISO or phrases like 'in 1 hour'.",
            "total_trips": 0,
            "fallback": {"from": from_fallback, "to": to_fallback}
        }

    result = await plan_trip(from_coords, to_coords, planned_time)

    # Annotate speech response with fallback context if needed
    base_speech = result.get("speech_response", "Trip found.")
    if from_fallback or to_fallback:
        fallback_note = " (using approximate location)"
        base_speech += fallback_note

    return {
        "trip_plans": result.get("trip_plans", []),
        "planned_time": planned_time.isoformat() if planned_time else "ASAP",
        "speech_response": base_speech,
        "total_trips": result.get("total_trips", 0),
        "fallback": {"from": from_fallback, "to": to_fallback}
    }
