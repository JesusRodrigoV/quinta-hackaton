import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from app.repositories.vehicle_repo import VehicleRepository
from app.repositories.reservation_repo import ReservationRepository
from app.services.event_service import (
    publish_ride_started,
    publish_ride_ended,
    publish_zone_understock,
    publish_vehicle_damaged,
)
from app.database import get_client, get_db
from app.config import settings

logger = logging.getLogger(__name__)


class ReservationService:
    def __init__(self, db):
        self.db = db
        self.vehicle_repo = VehicleRepository(db)
        self.res_repo = ReservationRepository(db)

    async def create_reservation(self, user_id: UUID, vehicle_id: str) -> dict:
        client = get_client()
        async with await client.start_session() as s:
            async with s.start_transaction():
                # ensure user has no active reservation
                active = await self.res_repo.get_active_by_user(user_id)
                if active:
                    raise ValueError("User has an active reservation")

                vehicle = await self.db.get_collection("vehicles").find_one({"vehicle_id": vehicle_id}, session=s)
                if not vehicle or vehicle.get("status") != "available" or vehicle.get("current_user_id") is not None:
                    raise ValueError("Vehicle not available")

                # mark vehicle as reserved by setting current_user_id
                await self.db.get_collection("vehicles").update_one({"vehicle_id": vehicle_id}, {"$set": {"current_user_id": str(user_id)}}, session=s)

                now = datetime.utcnow()
                doc = {
                    "user_id": str(user_id),
                    "vehicle_id": vehicle_id,
                    "start_time": now,
                    "status": "active",
                }
                res = await self.res_repo.create(doc, session=s)
                return res

    async def get_reservation(self, reservation_id: str) -> Optional[dict]:
        return await self.res_repo.get_by_id(reservation_id)

    async def get_active_by_user(self, user_id: UUID) -> Optional[dict]:
        return await self.res_repo.get_active_by_user(str(user_id))

    async def unlock(self, reservation_id: str) -> dict:
        # Validate reservation active and not expired (10 minutes)
        res = await self.res_repo.get_by_id(reservation_id)
        if not res:
            raise ValueError("Reservation not found")
        if res.get("status") != "active":
            raise ValueError("Reservation not active")
        start = res.get("start_time")
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        if datetime.utcnow() - start > timedelta(minutes=10):
            # expire
            await self.cancel_reservation(reservation_id)
            raise ValueError("Reservation expired")

        # mark fulfilled and set vehicle in_use
        async with await get_client().start_session() as s:
            async with s.start_transaction():
                await self.res_repo.fulfill(reservation_id, session=s)
                await self.db.get_collection("vehicles").update_one({"vehicle_id": res.get("vehicle_id")}, {"$set": {"status": "in_use", "current_user_id": res.get("user_id")}}, session=s)

        # publish event: ride.started (use user's lat/lng unknown here -> skip coordinates as 0)
        try:
            await publish_ride_started(res.get("vehicle_id"), res.get("user_id"), str(res.get("_id")), 0.0, 0.0)
        except Exception:
            logger.exception("Failed publishing ride.started")

        return {"reservation_id": reservation_id, "unlocked": True}

    async def end_ride(self, reservation_id: str, final_lat: float, final_lng: float):
        res = await self.res_repo.get_by_id(reservation_id)
        if not res:
            raise ValueError("Reservation not found")

        start = res.get("start_time")
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        end_time = datetime.utcnow()
        duration = end_time - start
        minutes = int(duration.total_seconds() // 60)
        if minutes == 0:
            minutes = 1
        cost = (Decimal("0.15") * Decimal(minutes)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        async with await get_client().start_session() as s:
            async with s.start_transaction():
                await self.res_repo.end_ride(reservation_id, end_time=end_time, total_cost=cost, session=s)
                await self.db.get_collection("vehicles").update_one({"vehicle_id": res.get("vehicle_id")}, {"$set": {"status": "available", "current_user_id": None, "location": {"type": "Point", "coordinates": [final_lng, final_lat]}}}, session=s)

        try:
            await publish_ride_ended(str(res.get("_id")), minutes, float(cost))
        except Exception:
            logger.exception("Failed publishing ride.ended")

        # run understock check
        try:
            await self.check_understock(final_lat, final_lng)
        except Exception:
            logger.exception("Understock check failed")

        return {"reservation_id": reservation_id, "duration_minutes": minutes, "total_cost": str(cost)}

    async def cancel_reservation(self, reservation_id: str):
        res = await self.res_repo.get_by_id(reservation_id)
        if not res:
            raise ValueError("Reservation not found")
        async with await get_client().start_session() as s:
            async with s.start_transaction():
                await self.res_repo.cancel(reservation_id, session=s)
                await self.db.get_collection("vehicles").update_one({"vehicle_id": res.get("vehicle_id")}, {"$set": {"current_user_id": None, "status": "available"}}, session=s)
        return {"reservation_id": reservation_id, "cancelled": True}

    async def report_damage(self, vehicle_id: str, severity: str, reported_by: str, description: str):
        if severity in ("high", "total_loss"):
            await self.db.get_collection("vehicles").update_one({"vehicle_id": vehicle_id}, {"$set": {"status": "maintenance"}})
        await publish_vehicle_damaged(vehicle_id, severity, reported_by)
        return {"vehicle_id": vehicle_id, "reported": True}

    async def expire_worker(self):
        # Find active reservations older than 10 minutes
        cutoff = datetime.utcnow() - timedelta(minutes=10)
        expired = await self.res_repo.find_expired(cutoff)
        for r in expired:
            try:
                await self.cancel_reservation(str(r.get("_id")))
                logger.info("Expired reservation %s cancelled", r.get("_id"))
            except Exception:
                logger.exception("Failed to cancel expired reservation %s", r.get("_id"))

    async def check_understock(self, lat: float, lng: float, radius_m: int = 1000, threshold: int = 3):
        # Count available vehicles within radius
        cursor = self.db.get_collection("vehicles").aggregate([
            {"$geoNear": {"near": {"type": "Point", "coordinates": [lng, lat]}, "distanceField": "dist", "maxDistance": radius_m, "spherical": True, "query": {"status": "available"}}},
            {"$count": "available_count"}
        ])
        docs = [d async for d in cursor]
        count = docs[0].get("available_count") if docs else 0
        if count < threshold:
            await publish_zone_understock(lat, lng, count)


async def handle_payment_completed(payload: dict):
    # Expected payload contains reservation_id and payment_status
    reservation_id = payload.get("reservation_id")
    payment_status = payload.get("payment_status")
    db = get_db()
    service = ReservationService(db)
    if payment_status != "approved" and reservation_id:
        try:
            await service.cancel_reservation(reservation_id)
            logger.info("Cancelled reservation %s due to payment status %s", reservation_id, payment_status)
        except Exception:
            logger.exception("Failed handling payment completed for %s", reservation_id)
