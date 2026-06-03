import logging
from typing import List, Optional
from decimal import Decimal

from app.repositories.vehicle_repo import VehicleRepository
from app.repositories.reservation_repo import ReservationRepository
from motor.motor_asyncio import AsyncIOMotorClient
from app.models import VehicleCreate

logger = logging.getLogger(__name__)


class VehicleService:
    def __init__(self, db):
        self.vehicle_repo = VehicleRepository(db)
        self.reservation_repo = ReservationRepository(db)

    async def register_vehicle(self, payload: VehicleCreate) -> dict:
        return await self.vehicle_repo.create(payload)

    async def get_vehicle(self, vehicle_id: str) -> Optional[dict]:
        return await self.vehicle_repo.get_by_vehicle_id(vehicle_id)

    async def update_location(self, vehicle_id: str, lat: float, lng: float, battery_level: int) -> Optional[dict]:
        return await self.vehicle_repo.update_location(vehicle_id, lat, lng, battery_level)

    async def find_available_nearby(self, lat: float, lng: float, radius_m: int) -> List[dict]:
        return await self.vehicle_repo.find_nearby(lat, lng, radius_m)
