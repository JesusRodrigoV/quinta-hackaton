# app/producer.py
import asyncio
import json
import logging
import threading

from confluent_kafka import KafkaException, Producer

from app.config import Settings
from app.exceptions import EventPublishError

logger = logging.getLogger(__name__)


class BusLocationProducer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._producer: Producer | None = None

    async def connect(self) -> None:
        try:
            self._producer = Producer({
                "bootstrap.servers": self._settings.kafka_bootstrap_servers,
                "client.id": "telemetry-tracking-service",
                "acks": "all",
                "enable.idempotence": True,
                "message.timeout.ms": self._settings.kafka_flush_timeout_seconds * 1000,
                "retries": 5,
            })
            logger.info("Kafka producer configured for %s", self._settings.kafka_bootstrap_servers)
        except Exception as exc:
            self._producer = None
            logger.exception("Failed to configure Kafka producer")
            raise EventPublishError("Kafka producer could not be configured") from exc

    async def close(self) -> None:
        if self._producer is not None:
            await asyncio.to_thread(self._producer.flush, self._settings.kafka_flush_timeout_seconds)
            self._producer = None

    async def health_check(self) -> bool:
        if self._producer is None:
            return False

        try:
            await asyncio.to_thread(self._producer.list_topics, timeout=2)
            return True
        except Exception:
            logger.exception("Kafka health check failed")
            return False

    async def publish_event(self, topic: str, key: str, payload: dict) -> None:
        if self._producer is None:
            raise EventPublishError("Kafka producer is not connected")

        try:
            await asyncio.to_thread(self._produce_and_wait, topic, key, payload)
        except EventPublishError:
            raise
        except Exception as exc:
            logger.exception("Failed to publish Kafka event")
            raise EventPublishError("Failed to publish Kafka event") from exc

    def _produce_and_wait(self, topic: str, key: str, payload: dict) -> None:
        if self._producer is None:
            raise EventPublishError("Kafka producer is not connected")

        delivered = threading.Event()
        delivery_error: KafkaException | None = None
        encoded_value = json.dumps(payload, separators=(",", ":"), default=str).encode("utf-8")

        def delivery_callback(error, _message) -> None:
            nonlocal delivery_error
            if error is not None:
                delivery_error = KafkaException(error)
            delivered.set()

        try:
            self._producer.produce(
                topic=topic,
                key=key.encode("utf-8"),
                value=encoded_value,
                callback=delivery_callback,
            )
            self._producer.flush(self._settings.kafka_flush_timeout_seconds)
        except BufferError as exc:
            raise EventPublishError("Kafka producer queue is full") from exc

        if not delivered.is_set():
            raise EventPublishError("Kafka publish timed out before delivery confirmation")

        if delivery_error is not None:
            raise EventPublishError(str(delivery_error)) from delivery_error
