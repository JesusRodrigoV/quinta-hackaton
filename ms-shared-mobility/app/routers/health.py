import logging
from fastapi import APIRouter, Depends
from app.database import get_db
from app.config import settings
from app.kafka.producer import _producer
from aiokafka import AIOKafkaProducer

router = APIRouter()
logger = logging.getLogger(__name__)


async def _check_kafka() -> bool:
    try:
        # check if producer started
        from app.kafka import producer as prod_mod
        return prod_mod._producer is not None
    except Exception:
        return False


@router.get("/health")
async def health(db=Depends(get_db)):
    db_ok = False
    kafka_ok = False
    try:
        await db.command({"ping": 1})
        db_ok = True
    except Exception:
        logger.exception("DB ping failed")
    try:
        kafka_ok = await _check_kafka()
    except Exception:
        logger.exception("Kafka check failed")
    return {"status": "ok", "db": db_ok, "kafka": kafka_ok}
