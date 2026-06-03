from typing import Literal, Optional
from pydantic import BaseModel


class Station(BaseModel):
    station_id: str
    name: str
    type: Literal["bus_stop", "metro_station", "scooter_hub"]
    latitude: float
    longitude: float


class Connection(BaseModel):
    from_station_id: str
    to_station_id: str
    transport_mode: str
    line: Optional[str] = None
    route_id: Optional[str] = None
    distance_meters: int
    average_travel_time_sec: int
    carbon_footprint_grams: float
