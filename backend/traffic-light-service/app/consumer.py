"""Kafka consumer for Traffic Light Service events."""
import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from confluent_kafka import Consumer, KafkaException

from app.config import Settings
from app.database import AuditRepository, SignalStateRepository
from app.exceptions import EventConsumptionError
from app.models import AuditLogEntry, BusDelayedEvent, CongestionAlertEvent, SignalState
from app.ntcip_translator import NTCIPTranslator

logger = logging.getLogger(__name__)


class TrafficSignalConsumer:
    """Consumes Kafka events and processes traffic signal commands."""

    def __init__(
        self,
        settings: Settings,
        signal_repo: SignalStateRepository,
        audit_repo: AuditRepository,
    ) -> None:
        self._settings = settings
        self._signal_repo = signal_repo
        self._audit_repo = audit_repo
        self._consumer: Consumer | None = None
        self._running = False

    async def connect(self) -> None:
        """Initialize Kafka consumer."""
        try:
            self._consumer = Consumer(
                {
                    "bootstrap.servers": self._settings.kafka_bootstrap_servers,
                    "group.id": self._settings.kafka_group_id,
                    "auto.offset.reset": "earliest",
                    "enable.auto.commit": True,
                }
            )
            topics = [
                self._settings.kafka_topic_bus_delayed,
                self._settings.kafka_topic_congestion_alert,
            ]
            self._consumer.subscribe(topics)
            logger.info("Kafka consumer connected to topics: %s", topics)
        except Exception:
            self._consumer = None
            logger.exception("Failed to initialize Kafka consumer")
            raise

    async def close(self) -> None:
        """Close Kafka consumer."""
        self._running = False
        if self._consumer is not None:
            self._consumer.close()
            self._consumer = None

    async def start_consuming(self) -> None:
        """Start consuming events (blocking loop, run in background)."""
        if self._consumer is None:
            raise EventConsumptionError("Kafka consumer is not connected")

        self._running = True
        logger.info("Traffic Light Service consumer loop started")

        try:
            while self._running:
                msg = self._consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaException._PARTITION_EOF:
                        logger.debug("Reached end of partition")
                    else:
                        logger.error("Kafka error: %s", msg.error())
                    continue

                await self._process_message(msg)
        except Exception:
            logger.exception("Consumer loop crashed")
            self._running = False
            raise
        finally:
            self._running = False

    async def _process_message(self, msg) -> None:
        """Process individual Kafka message."""
        try:
            topic = msg.topic()
            key = msg.key().decode("utf-8") if msg.key() else "unknown"
            value = json.loads(msg.value().decode("utf-8"))

            logger.info(f"Processing event from topic {topic}: {key}")

            if topic == self._settings.kafka_topic_bus_delayed:
                await self._handle_bus_delayed(value, key)
            elif topic == self._settings.kafka_topic_congestion_alert:
                await self._handle_congestion_alert(value, key)
            else:
                logger.warning(f"Unknown topic: {topic}")
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON from message")
        except Exception:
            logger.exception("Error processing message")

    async def _handle_bus_delayed(self, event_data: dict, bus_id: str) -> None:
        """Handle bus delayed event: activate priority at intersection."""
        try:
            event = BusDelayedEvent(**event_data)

            # Map corridor to intersection_id (simplified: use corridor as ID)
            intersection_id = f"INT-{event.corridor.replace(' ', '_').upper()}"

            # Translate to NTCIP command
            ntcip_payload = NTCIPTranslator.translate_bus_delay_to_priority_command(
                intersection_id=intersection_id,
                delay_minutes=event.delay_minutes,
                max_payload_bytes=self._settings.ntcip_max_payload_bytes,
            )

            # Log NTCIP command
            logger.info(
                f"NTCIP Command (bus {bus_id}): {ntcip_payload[:100]}... (len={len(ntcip_payload)})"
            )

            # Update signal state in Redis
            await self._signal_repo.set_signal_state(
                intersection_id=intersection_id,
                state=SignalState.GREEN,
                timer_sec=min(event.delay_minutes * 10, 120),
                priority_override=True,
            )

            # Audit log: success
            audit_entry = AuditLogEntry(
                log_id=str(uuid4()),
                timestamp=datetime.now(timezone.utc),
                event_type="signal_priority_applied",
                intersection_id=intersection_id,
                bus_id=bus_id,
                priority_level="HIGH",
                status="success",
                details=f"Bus delayed {event.delay_minutes}min, NTCIP payload={len(ntcip_payload)} bytes",
            )
            await self._audit_repo.write_audit_log(audit_entry)

        except Exception as e:
            logger.exception(f"Failed to handle bus delay event: {e}")
            # Audit log: failure
            audit_entry = AuditLogEntry(
                log_id=str(uuid4()),
                timestamp=datetime.now(timezone.utc),
                event_type="signal_priority_applied",
                intersection_id="UNKNOWN",
                bus_id=bus_id,
                priority_level=None,
                status="failure",
                details=str(e),
            )
            await self._audit_repo.write_audit_log(audit_entry)

    async def _handle_congestion_alert(self, event_data: dict, key: str) -> None:
        """Handle congestion alert: adjust signal timing."""
        try:
            event = CongestionAlertEvent(**event_data)

            # Map corridor_id to intersection_id
            intersection_id = f"INT-{event.corridor_id.upper()}"

            # Translate to NTCIP command based on severity
            ntcip_payload = NTCIPTranslator.translate_congestion_to_command(
                intersection_id=intersection_id,
                severity=event.severity,
                max_payload_bytes=self._settings.ntcip_max_payload_bytes,
            )

            # Log NTCIP command
            logger.info(
                f"NTCIP Command (congestion severity={event.severity}): {ntcip_payload[:100]}... (len={len(ntcip_payload)})"
            )

            # Update signal state
            await self._signal_repo.set_signal_state(
                intersection_id=intersection_id,
                state=SignalState.RED,
                timer_sec=60 if event.severity <= 2 else 120,
                priority_override=event.severity >= 4,
            )

            # Audit log: success
            audit_entry = AuditLogEntry(
                log_id=str(uuid4()),
                timestamp=datetime.now(timezone.utc),
                event_type="congestion_response",
                intersection_id=intersection_id,
                bus_id=None,
                priority_level=None,
                status="success",
                details=f"Severity={event.severity}, predicted delay={event.predicted_delay_minutes}min, NTCIP payload={len(ntcip_payload)} bytes",
            )
            await self._audit_repo.write_audit_log(audit_entry)

        except Exception as e:
            logger.exception(f"Failed to handle congestion alert: {e}")
            audit_entry = AuditLogEntry(
                log_id=str(uuid4()),
                timestamp=datetime.now(timezone.utc),
                event_type="congestion_response",
                intersection_id="UNKNOWN",
                bus_id=None,
                priority_level=None,
                status="failure",
                details=str(e),
            )
            await self._audit_repo.write_audit_log(audit_entry)
