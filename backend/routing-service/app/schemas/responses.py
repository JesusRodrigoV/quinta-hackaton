from typing import List, Optional
from pydantic import BaseModel


class StationInfo(BaseModel):
    station_id: str
    name: str
    type: str


class Segment(BaseModel):
    from_station: StationInfo
    to_station: StationInfo
    transport_mode: str
    line: Optional[str] = None
    travel_time_min: float
    distance_km: float


class RouteOption(BaseModel):
    total_time_min: float
    total_cost: float
    total_co2_kg: float
    segments: List[Segment]


class RouteResponse(BaseModel):
    route_id: Optional[str] = None
    options: List[RouteOption]
