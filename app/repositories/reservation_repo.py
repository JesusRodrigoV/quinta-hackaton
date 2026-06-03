from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from pymongo import ReturnDocument


class ReservationRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._coll = db.get_collection("reservations")

    async def create(self, doc: dict, session=None) -> dict:
        res = await self._coll.insert_one(doc, session=session)
        doc["_id"] = res.inserted_id
        return doc

    async def get_by_id(self, id: str) -> Optional[dict]:
        return await self._coll.find_one({"_id": ObjectId(id)})

    async def get_active_by_user(self, user_id) -> Optional[dict]:
        return await self._coll.find_one({"user_id": user_id, "status": "active"})

    async def cancel(self, reservation_id: str, session=None) -> Optional[dict]:
        return await self._coll.find_one_and_update({"_id": ObjectId(reservation_id)}, {"$set": {"status": "cancelled", "end_time": datetime.utcnow()}}, session=session, return_document=ReturnDocument.AFTER)

    async def fulfill(self, reservation_id: str, session=None) -> Optional[dict]:
        return await self._coll.find_one_and_update({"_id": ObjectId(reservation_id), "status": "active"}, {"$set": {"status": "fulfilled"}}, session=session, return_document=ReturnDocument.AFTER)

    async def end_ride(self, reservation_id: str, end_time: datetime, total_cost: Decimal, session=None) -> Optional[dict]:
        return await self._coll.find_one_and_update({"_id": ObjectId(reservation_id)}, {"$set": {"end_time": end_time, "total_cost": total_cost, "status": "fulfilled"}}, session=session, return_document=ReturnDocument.AFTER)

    async def find_expired(self, older_than: datetime) -> List[dict]:
        cursor = self._coll.find({"status": "active", "start_time": {"$lt": older_than}})
        return [doc async for doc in cursor]
