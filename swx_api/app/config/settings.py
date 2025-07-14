"""
Application Settings Configuration
----------------------------------
This module defines the global settings for the SwX-API.

It extends the base CoreSettings class from swx_api/core/config/settings.
"""

from pydantic import Field

from swx_api.core.config.settings import Settings as CoreSettings


class AppSettings(CoreSettings):

    NGROK_AUTH_TOKEN : str = Field(default="")
    APP_PORT: int = Field(default=8000)


# Create global settings instance
app_settings = AppSettings()
