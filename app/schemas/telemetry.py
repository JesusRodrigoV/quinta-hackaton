from pydantic import BaseModel, Field
from datetime import datetime

class TelemetryEvent(BaseModel):
    bus_id: str = Field(..., description="ID único del vehículo")
    route_id: str = Field(..., description="Corredor o ruta actual")
    latitude: float
    longitude: float
    speed: float = Field(..., description="Velocidad actual en km/h")
    timestamp: datetime

class RerouteCommand(BaseModel):
    bus_id: str
    original_route: str
    suggested_route: str
    congestion_level: float
    reason: str