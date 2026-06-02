import enum
from typing import Optional, Literal
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, validator
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            return v
        raise TypeError("Invalid ObjectId")


class VehicleType(str, enum.Enum):
    scooter = "scooter"
    ebike = "ebike"


class VehicleStatus(str, enum.Enum):
    available = "available"
    in_use = "in_use"
    maintenance = "maintenance"


class GeoPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: list[float]

    @validator("coordinates")
    def coords_length(cls, v):
        if len(v) != 2:
            raise ValueError("coordinates must be [lng, lat]")
        return v


class VehicleCreate(BaseModel):
    vehicle_id: str
    type: VehicleType
    battery_level: int = Field(ge=0, le=100)
    location: GeoPoint
    status: VehicleStatus = VehicleStatus.available


class VehicleLocationUpdate(BaseModel):
    lat: float
    lng: float
    battery_level: int = Field(ge=0, le=100)


class VehicleOut(BaseModel):
    id: str = Field(alias="_id")
    vehicle_id: str
    type: VehicleType
    battery_level: int
    location: GeoPoint
    status: VehicleStatus
    current_user_id: Optional[UUID] = None

    model_config = {"populate_by_name": True}


class ReservationStatus(str, enum.Enum):
    active = "active"
    fulfilled = "fulfilled"
    cancelled = "cancelled"


class ReservationCreate(BaseModel):
    user_id: UUID
    vehicle_id: str


class ReservationOut(BaseModel):
    id: str = Field(alias="_id")
    user_id: UUID
    vehicle_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_cost: Optional[Decimal] = None
    status: ReservationStatus

    model_config = {"populate_by_name": True}


class UnlockResponse(BaseModel):
    reservation_id: str
    unlocked: bool


class EndRideRequest(BaseModel):
    final_lat: float
    final_lng: float


class DamageReportCreate(BaseModel):
    vehicle_id: str
    user_id: UUID
    description: str
    severity: Literal["low", "medium", "high", "total_loss"]


class HealthResponse(BaseModel):
    status: str
    db: bool
    kafka: bool
