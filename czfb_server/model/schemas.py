from pydantic import BaseModel, Field
from typing import Optional


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class TripRequest(BaseModel):
    from_place: str = Field(..., description="Departure place name")
    to_place: str = Field(..., description="Destination place name")


class StopMatch(BaseModel):
    stop_id: str
    stop_name: str

    # Optional geolocation
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance: Optional[float] = None

    # Metadata from GTFS-like file
    zone_id: Optional[str] = None
    stop_url: Optional[str] = None
    location_type: Optional[int] = None
    parent_station: Optional[str] = None
    wheelchair_boarding: Optional[int] = None
    level_id: Optional[str] = None
    platform_code: Optional[str] = None
    asw_node_id: Optional[str] = None
    asw_stop_id: Optional[str] = None
    zone_region_type: Optional[str] = None
