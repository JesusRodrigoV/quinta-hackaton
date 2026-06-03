import asyncio
import json
import logging
from typing import Optional

from aiokafka import AIOKafkaProducer

from app.config import settings

logger = logging.getLogger(__name__)

_producer: Optional[AIOKafkaProducer] = None


async def init_producer() -> None:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS, client_id=settings.KAFKA_CLIENT_ID)
        await _producer.start()
        logger.info("Kafka producer started")


async def close_producer() -> None:
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
        logger.info("Kafka producer stopped")


async def publish_event(topic: str, payload: dict) -> None:
    if _producer is None:
        raise RuntimeError("Producer not initialized")
    data = json.dumps(payload, default=str).encode("utf-8")
    await _producer.send_and_wait(topic, data)
    logger.info("Published event to %s: %s", topic, payload)
