"""Data models for Traffic Light Service."""
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SignalState(str, Enum):
    """Enumeration of traffic signal states."""

    GREEN = "green"
    RED = "red"
    YELLOW = "yellow"


class SignalPriority(str, Enum):
    """Priority levels for signal override."""

    NORMAL = "normal"
    HIGH = "high"  # Delayed bus
    CRITICAL = "critical"  # Emergency vehicle


class BusDelayedEvent(BaseModel):
    """Event model for delayed buses from Kafka."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bus_id": "BUS-102",
                "route_id": "R-001",
                "delay_minutes": 8,
                "corridor": "Avenida Principal",
                "latitude": -16.4897,
                "longitude": -68.1193,
                "timestamp": "2026-06-02T19:00:00Z",
            }
        }
    )

    bus_id: str = Field(..., min_length=1)
    route_id: str = Field(..., min_length=1)
    delay_minutes: int = Field(..., ge=1)
    corridor: str = Field(..., min_length=1)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timestamp: datetime


class CongestionAlertEvent(BaseModel):
    """Event model for congestion alerts from Kafka."""

    corridor_id: str = Field(..., min_length=1)
    severity: int = Field(..., ge=1, le=5)
    predicted_delay_minutes: int = Field(..., ge=1)
    timestamp: datetime


class SignalState_Response(BaseModel):
    """Response model for traffic signal state."""

    intersection_id: str
    current_state: SignalState
    timer_remaining_sec: int
    priority_override_active: bool
    last_updated: datetime


class NTCIPMessage(BaseModel):
    """NTCIP command message (max 256 bytes)."""

    command_type: str = Field(..., description="Type: SET_SIGNAL_STATE, ACTIVATE_PRIORITY, etc.")
    intersection_id: str
    signal_state: SignalState | None = None
    priority_level: SignalPriority | None = None
    duration_sec: int | None = None

    def to_ntcip_payload(self) -> bytes:
        """Serialize to compact NTCIP binary payload (max 256 bytes)."""
        # Simplified NTCIP serialization (in prod: use actual NTCIP ASN.1 codec)
        payload = f"{self.command_type}|{self.intersection_id}"
        if self.signal_state:
            payload += f"|{self.signal_state.value}"
        if self.priority_level:
            payload += f"|{self.priority_level.value}"
        if self.duration_sec is not None:
            payload += f"|{self.duration_sec}"

        encoded = payload.encode("utf-8")
        if len(encoded) > 256:
            raise ValueError(f"NTCIP payload exceeds 256 bytes: {len(encoded)}")
        return encoded


class AuditLogEntry(BaseModel):
    """Audit log entry for regulatory compliance."""

    log_id: str
    timestamp: datetime
    event_type: str  # 'signal_priority_applied', 'reroute_confirmed', 'reroute_failed'
    intersection_id: str
    bus_id: str | None = None
    priority_level: str | None = None
    status: str  # 'success', 'failure'
    details: str


class AcceptedResponse(BaseModel):
    """Response model for accepted events."""

    message: str
    status: str
