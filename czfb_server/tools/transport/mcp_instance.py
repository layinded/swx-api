from fastmcp import Client
from czfb_server.tools.transport.mcp_base import mcp_transport_tools

# Trigger all tool and prompt definitions
import czfb_server.tools.transport.services.departure_service
import czfb_server.tools.transport.services.geocoding_service
import czfb_server.tools.transport.services.stop_service
import czfb_server.tools.transport.services.trip_service
import czfb_server.tools.transport.prompts

# Create MCP client
mcp_client = Client(mcp_transport_tools)
