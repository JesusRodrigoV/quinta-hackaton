from typing import Optional, List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument
from app.models import GeoPoint, VehicleCreate


class VehicleRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._coll = db.get_collection("vehicles")

    async def create(self, payload: VehicleCreate) -> dict:
        doc = payload.model_dump()
        res = await self._coll.insert_one(doc)
        doc["_id"] = res.inserted_id
        return doc

    async def get_by_vehicle_id(self, vehicle_id: str) -> Optional[dict]:
        return await self._coll.find_one({"vehicle_id": vehicle_id})

    async def update_location(self, vehicle_id: str, lat: float, lng: float, battery_level: int) -> Optional[dict]:
        loc = {"type": "Point", "coordinates": [lng, lat]}
        update = {"$set": {"location": loc, "battery_level": int(battery_level)}}
        return await self._coll.find_one_and_update({"vehicle_id": vehicle_id}, update, return_document=ReturnDocument.AFTER)

    async def find_nearby(self, lat: float, lng: float, radius_m: int) -> List[dict]:
        cursor = self._coll.aggregate([
            {"$geoNear": {
                "near": {"type": "Point", "coordinates": [lng, lat]},
                "distanceField": "distance_meters",
                "maxDistance": radius_m,
                "spherical": True,
                "query": {"status": "available"}
            }},
        ])
        return [doc async for doc in cursor]

    async def set_status(self, vehicle_id: str, status: str, current_user_id=None, session=None) -> Optional[dict]:
        update = {"$set": {"status": status, "current_user_id": current_user_id}}
        return await self._coll.find_one_and_update({"vehicle_id": vehicle_id}, update, session=session, return_document=ReturnDocument.AFTER)
