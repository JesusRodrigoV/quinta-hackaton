import asyncio
import json
import logging

from aiokafka import AIOKafkaProducer

from app.config import KAFKA_BROKER

logger = logging.getLogger(__name__)
_producer = None
_TIMEOUT = 5


def set_producer(producer):
    global _producer
    _producer = producer


async def init_kafka():
    if not KAFKA_BROKER:
        logger.warning("KAFKA_BROKER not set — Kafka disabled")
        return
    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode(),
            max_block_ms=_TIMEOUT * 1000,
            request_timeout_ms=_TIMEOUT * 1000,
        )
        await asyncio.wait_for(producer.start(), timeout=_TIMEOUT)
        set_producer(producer)
        logger.info("Kafka producer connected to %s", KAFKA_BROKER)
    except Exception as e:
        logger.warning("Kafka connection failed (%s) — running without Kafka", e)


async def close_kafka():
    if _producer:
        try:
            await asyncio.wait_for(_producer.stop(), timeout=_TIMEOUT)
        except Exception:
            logger.warning("Kafka producer stop timed out — forcing close")
        set_producer(None)


async def publish(topic: str, key: str, value: dict):
    if not _producer:
        return
    try:
        await asyncio.wait_for(
            _producer.send(topic, key=key.encode(), value=value),
            timeout=_TIMEOUT,
        )
    except Exception as e:
        logger.warning("Failed to publish to Kafka (%s/%s): %s", topic, key, e)
