import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from bson import ObjectId

from app.config import settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


def get_client() -> AsyncIOMotorClient:
    if _client is None:
        raise RuntimeError("Database client not initialized")
    return _client


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialized")
    return _db


async def init_db():
    global _client, _db
    logger.info("Connecting to MongoDB %s", settings.MONGO_URI)
    _client = AsyncIOMotorClient(settings.MONGO_URI)
    _db = _client[settings.MONGO_DB]

    # Ensure indexes
    vehicles = _db.get_collection("vehicles")
    await vehicles.create_index([("vehicle_id", 1)], unique=True)
    await vehicles.create_index([("location", "2dsphere")])
    await vehicles.create_index([("status", 1)])

    reservations = _db.get_collection("reservations")
    await reservations.create_index([("user_id", 1)])
    await reservations.create_index([("start_time", 1)])
    logger.info("MongoDB initialized and indexes ensured")


async def close_db():
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed")
