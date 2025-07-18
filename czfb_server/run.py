import asyncio
from pyngrok import ngrok, conf

from czfb_server.config.config import NGROK_AUTHTOKEN
from czfb_server.tools.transport.mcp_instance import mcp as transport_tools


async def main():
    port = 8081

    # Optional: Set ngrok authtoken from environment variable or hardcoded string
    # If you don't have an authtoken, you can skip this
    # Example:
    conf.get_default().auth_token = NGROK_AUTHTOKEN
    # Start ngrok tunnel
    public_url = ngrok.connect(port)
    print(f"✨ ngrok tunnel available at: {public_url}")

    # Start your async server
    await transport_tools.run_async(transport="streamable-http", port=port, host="0.0.0.0")



if __name__ == "__main__":
    asyncio.run(main())
