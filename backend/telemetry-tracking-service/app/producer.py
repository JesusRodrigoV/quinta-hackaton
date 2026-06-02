# app/producer.py
import asyncio
import json
import logging

from confluent_kafka import KafkaException, Producer

from app.config import Settings
from app.models import TelemetryPayload

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
            })
            logger.info("Kafka producer configured for %s", self._settings.kafka_bootstrap_servers)
        except Exception:
            self._producer = None
            logger.exception("Failed to configure Kafka producer")
            raise

    async def close(self) -> None:
        if self._producer is not None:
            await asyncio.to_thread(self._producer.flush, 5)
            self._producer = None

    async def publish_bus_location_updated(self, payload: TelemetryPayload) -> None:
        if self._producer is None:
            raise RuntimeError("Kafka producer is not connected")

        try:
            await asyncio.to_thread(
                self._produce_and_flush,
                self._settings.kafka_topic_bus_location_updated,
                payload.bus_id,
                payload.to_event(),
            )
        except Exception:
            logger.exception("Failed to publish bus location update event")
            raise

    def _produce_and_flush(self, topic: str, key: str, value: dict) -> None:
        if self._producer is None:
            raise RuntimeError("Kafka producer is not connected")

        encoded_value = json.dumps(value, separators=(",", ":"), default=str).encode("utf-8")
        delivery_error: KafkaException | None = None

        def delivery_callback(error, _message) -> None:
            nonlocal delivery_error
            if error is not None:
                delivery_error = KafkaException(error)

        self._producer.produce(
            topic=topic,
            key=key.encode("utf-8"),
            value=encoded_value,
            callback=delivery_callback,
        )
        self._producer.flush(10)

        if delivery_error is not None:
            raise delivery_error
