# app/models.py
from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TelemetryPayload(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "bus_id": "BUS-102",
            "latitude": -16.4897,
            "longitude": -68.1193,
            "speed_kmh": 42.5,
            "timestamp": "2026-06-02T19:00:00Z",
        }
    })

    bus_id: str = Field(..., min_length=1, max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    speed_kmh: float = Field(..., ge=0, le=180)
    timestamp: datetime

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def to_event(self, event_id: UUID | None = None) -> dict:
        event = {
            "event_type": "bus.location.updated",
            "bus_id": self.bus_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "speed_kmh": self.speed_kmh,
            "timestamp": self.timestamp.isoformat(),
        }
        if event_id is not None:
            event["event_id"] = str(event_id)
        return event


class OutboxEvent(BaseModel):
    id: UUID
    topic: str
    key: str
    payload: dict


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


class ReadinessResponse(BaseModel):
    status: str
    database: str
    kafka: str


class AcceptedResponse(BaseModel):
    message: str
    event_id: UUID
    topic: str
