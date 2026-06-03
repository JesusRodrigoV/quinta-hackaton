import asyncio
import json
import logging
from typing import Optional

from aiokafka import AIOKafkaConsumer

from app.config import settings

logger = logging.getLogger(__name__)

_consumer: Optional[AIOKafkaConsumer] = None
_task: Optional[asyncio.Task] = None


async def _handle_payment_message(message: bytes) -> None:
    try:
        payload = json.loads(message.decode("utf-8"))
    except Exception:
        logger.exception("Failed to decode payment message")
        return

    # Lazy import to avoid circular dependencies
    from app.services.reservation_service import handle_payment_completed

    await handle_payment_completed(payload)


async def _consumer_loop(consumer: AIOKafkaConsumer) -> None:
    try:
        async for msg in consumer:
            logger.info("Consumed message %s from %s", msg.offset, msg.topic)
            await _handle_payment_message(msg.value)
    except asyncio.CancelledError:
        logger.info("Consumer loop cancelled")
    except Exception:
        logger.exception("Consumer loop error")


async def start_consumer() -> None:
    global _consumer, _task
    if _consumer is not None:
        return
    _consumer = AIOKafkaConsumer(
        "payment.journey.completed",
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=f"{settings.KAFKA_CLIENT_ID}-consumer",
        enable_auto_commit=True,
    )
    await _consumer.start()
    _task = asyncio.create_task(_consumer_loop(_consumer))
    logger.info("Kafka consumer started")


async def stop_consumer() -> None:
    global _consumer, _task
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None
    if _consumer is not None:
        await _consumer.stop()
        _consumer = None
    logger.info("Kafka consumer stopped")
