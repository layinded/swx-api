from fastmcp.prompts.prompt import PromptMessage, TextContent
from czfb_server.tools.transport.mcp_instance import mcp_transport_tools as mcp


@mcp.prompt
def plan_trip_prompt(from_place: str, to_place: str, departure_time: str | None = None) -> PromptMessage:
    """Generate a request to plan a public transport trip between two places."""
    time_phrase = f" planned to depart at '{departure_time}'" if departure_time else " departing as soon as possible"
    text = (
        f"Please plan a public transport trip from '{from_place}' to '{to_place}',"
        f"{time_phrase}. Include details like departure times, transport modes, lines, and estimated travel duration."
    )
    return PromptMessage(role="user", content=TextContent(type="text", text=text))

@mcp.prompt
def get_departures_prompt(stop_name: str, when: str | None = None) -> PromptMessage:
    """Generate a user query for getting upcoming departures from a stop."""
    text = f"Show me departures from {stop_name} {when}." if when else f"Show me the next departures from {stop_name}."
    return PromptMessage(role="user", content=TextContent(type="text", text=text))

@mcp.prompt
def nearby_stops_prompt(latitude: float, longitude: float, radius: int = 500) -> PromptMessage:
    """Ask for nearby public transport stops within a given radius."""
    text = (
        f"Find all public transport stops within {radius} meters of coordinates "
        f"latitude {latitude:.5f} and longitude {longitude:.5f}."
    )
    return PromptMessage(role="user", content=TextContent(type="text", text=text))

@mcp.prompt
def reverse_geocode_prompt(latitude: float, longitude: float) -> PromptMessage:
    """Generate a query to identify the nearest stop to given coordinates."""
    text = (
        f"What is the nearest public transport stop to latitude {latitude:.5f}, "
        f"longitude {longitude:.5f}?"
    )
    return PromptMessage(role="user", content=TextContent(type="text", text=text))

@mcp.prompt
def stop_metadata_prompt(stop_name: str) -> PromptMessage:
    """Ask for detailed metadata about a specific stop."""
    text = f"Give me the full stop metadata for '{stop_name}' including zone, platform, and accessibility."
    return PromptMessage(role="user", content=TextContent(type="text", text=text))
