import asyncio
import json
import logging
from datetime import datetime, timezone

from aiokafka import AIOKafkaConsumer

from app.config import KAFKA_BROKER, KAFKA_TOPIC_BUS_LOCATION_UPDATED, KAFKA_CONSUMER_GROUP_ID

logger = logging.getLogger(__name__)

_positions: dict[str, dict] = {}
_consumer: AIOKafkaConsumer | None = None
_task: asyncio.Task | None = None


def _handle_message(msg):
    try:
        data = json.loads(msg.value)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Invalid message on %s: %s", msg.topic, msg.value)
        return
    bus_id = data.get("bus_id")
    if not bus_id:
        return
    _positions[bus_id] = {
        "bus_id": bus_id,
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "speed_kmh": data.get("speed_kmh"),
        "timestamp": data.get("timestamp"),
        "last_seen": datetime.now(timezone.utc).isoformat(),
    }


async def _run():
    global _consumer
    _consumer = AIOKafkaConsumer(
        KAFKA_TOPIC_BUS_LOCATION_UPDATED,
        bootstrap_servers=KAFKA_BROKER,
        group_id=KAFKA_CONSUMER_GROUP_ID,
        auto_offset_reset="latest",
        value_deserializer=lambda v: v,
    )
    await _consumer.start()
    try:
        async for msg in _consumer:
            _handle_message(msg)
    except asyncio.CancelledError:
        logger.info("Bus tracker consumer cancelled")
    except Exception:
        logger.exception("Bus tracker consumer error")
    finally:
        await _consumer.stop()
        _consumer = None


async def start():
    global _task
    if not KAFKA_BROKER:
        logger.warning("KAFKA_BROKER not set — bus tracker disabled")
        return
    if _task is not None:
        return
    _task = asyncio.create_task(_run())
    logger.info("Bus tracker started — consuming %s", KAFKA_TOPIC_BUS_LOCATION_UPDATED)


async def stop():
    global _task, _consumer
    if _consumer:
        await _consumer.stop()
    if _task:
        _task.cancel()
        try:
            await _task
        except (asyncio.CancelledError, Exception):
            pass
        _task = None
    logger.info("Bus tracker stopped")


def get_positions() -> list[dict]:
    return list(_positions.values())


def get_bus_position(bus_id: str) -> dict | None:
    return _positions.get(bus_id)
