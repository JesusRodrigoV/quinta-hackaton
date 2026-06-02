# app/database.py
import json
import logging
from uuid import UUID

import asyncpg

from app.config import Settings
from app.exceptions import DatabaseUnavailableError
from app.models import OutboxEvent, TelemetryPayload

logger = logging.getLogger(__name__)

INIT_SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS bus_telemetry (
    id BIGSERIAL,
    bus_id VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    speed_kmh DOUBLE PRECISION NOT NULL CHECK (speed_kmh >= 0),
    timestamp TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, timestamp)
);

SELECT create_hypertable('bus_telemetry', 'timestamp', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_bus_telemetry_bus_id_time
    ON bus_telemetry (bus_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS telemetry_outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    aggregate_id VARCHAR(100) NOT NULL,
    topic VARCHAR(150) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'publishing', 'published')),
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_telemetry_outbox_pending
    ON telemetry_outbox (created_at ASC)
    WHERE status = 'pending';
"""

INSERT_TELEMETRY_WITH_OUTBOX_SQL = """
WITH event AS (
    SELECT gen_random_uuid() AS event_id
),
inserted_telemetry AS (
    INSERT INTO bus_telemetry (
        bus_id,
        latitude,
        longitude,
        speed_kmh,
        timestamp
    )
    VALUES ($1, $2, $3, $4, $5)
    RETURNING bus_id, latitude, longitude, speed_kmh, timestamp
),
inserted_outbox AS (
    INSERT INTO telemetry_outbox (
        id,
        event_type,
        aggregate_id,
        topic,
        payload,
        status
    )
    SELECT
        event.event_id,
        'bus.location.updated',
        inserted_telemetry.bus_id,
        $6,
        jsonb_build_object(
            'event_id', event.event_id::TEXT,
            'event_type', 'bus.location.updated',
            'bus_id', inserted_telemetry.bus_id,
            'latitude', inserted_telemetry.latitude,
            'longitude', inserted_telemetry.longitude,
            'speed_kmh', inserted_telemetry.speed_kmh,
            'timestamp', to_jsonb(inserted_telemetry.timestamp)
        ),
        'publishing'
    FROM event, inserted_telemetry
    RETURNING id, topic, aggregate_id, payload
)
SELECT id, topic, aggregate_id, payload
FROM inserted_outbox;
"""


class TimescaleTelemetryRepository:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        try:
            self._pool = await asyncpg.create_pool(
                host=self._settings.timescaledb_host,
                port=self._settings.timescaledb_port,
                user=self._settings.timescaledb_user,
                password=self._settings.timescaledb_password,
                database=self._settings.timescaledb_database,
                min_size=self._settings.timescaledb_min_pool_size,
                max_size=self._settings.timescaledb_max_pool_size,
                command_timeout=10,
            )
            await self.initialize_schema()
            await self.recover_stale_outbox_events()
            logger.info(
                "TimescaleDB pool connected to %s:%s/%s",
                self._settings.timescaledb_host,
                self._settings.timescaledb_port,
                self._settings.timescaledb_database,
            )
        except Exception as exc:
            self._pool = None
            logger.exception("Failed to connect TimescaleDB")
            raise DatabaseUnavailableError("TimescaleDB is unavailable") from exc

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def initialize_schema(self) -> None:
        if self._pool is None:
            raise DatabaseUnavailableError("TimescaleDB pool is not connected")

        async with self._pool.acquire() as connection:
            await connection.execute(INIT_SCHEMA_SQL)

    async def health_check(self) -> bool:
        if self._pool is None:
            return False

        try:
            async with self._pool.acquire() as connection:
                value = await connection.fetchval("SELECT 1;")
                return value == 1
        except Exception:
            logger.exception("TimescaleDB health check failed")
            return False

    async def recover_stale_outbox_events(self) -> None:
        if self._pool is None:
            raise DatabaseUnavailableError("TimescaleDB pool is not connected")

        async with self._pool.acquire() as connection:
            await connection.execute(
                """
                UPDATE telemetry_outbox
                SET status = 'pending',
                    last_error = 'Recovered stale publishing event during service startup'
                WHERE status = 'publishing'
                  AND created_at < NOW() - make_interval(secs => $1);
                """,
                self._settings.outbox_stale_after_seconds,
            )

    async def write_bus_telemetry(self, payload: TelemetryPayload, topic: str) -> OutboxEvent:
        if self._pool is None:
            raise DatabaseUnavailableError("TimescaleDB pool is not connected")

        try:
            async with self._pool.acquire() as connection:
                async with connection.transaction():
                    row = await connection.fetchrow(
                        INSERT_TELEMETRY_WITH_OUTBOX_SQL,
                        payload.bus_id,
                        payload.latitude,
                        payload.longitude,
                        payload.speed_kmh,
                        payload.timestamp,
                        topic,
                    )
                    if row is None:
                        raise DatabaseUnavailableError("Telemetry insert did not return an outbox event")
                    return self._row_to_outbox_event(row)
        except DatabaseUnavailableError:
            raise
        except Exception as exc:
            logger.exception("Failed to write telemetry to TimescaleDB for bus_id=%s", payload.bus_id)
            raise DatabaseUnavailableError("Failed to persist telemetry") from exc

    async def list_pending_outbox_events(self, limit: int) -> list[OutboxEvent]:
        if self._pool is None:
            raise DatabaseUnavailableError("TimescaleDB pool is not connected")

        async with self._pool.acquire() as connection:
            async with connection.transaction():
                rows = await connection.fetch(
                    """
                    WITH candidate_events AS (
                        SELECT id
                        FROM telemetry_outbox
                        WHERE status = 'pending'
                        ORDER BY created_at ASC
                        LIMIT $1
                        FOR UPDATE SKIP LOCKED
                    ),
                    claimed_events AS (
                        UPDATE telemetry_outbox
                        SET status = 'publishing'
                        WHERE id IN (SELECT id FROM candidate_events)
                        RETURNING id, topic, aggregate_id, payload
                    )
                    SELECT id, topic, aggregate_id, payload
                    FROM claimed_events;
                    """,
                    limit,
                )
        return [self._row_to_outbox_event(row) for row in rows]

    async def mark_outbox_event_published(self, event_id: UUID) -> None:
        if self._pool is None:
            raise DatabaseUnavailableError("TimescaleDB pool is not connected")

        async with self._pool.acquire() as connection:
            await connection.execute(
                """
                UPDATE telemetry_outbox
                SET status = 'published',
                    published_at = NOW(),
                    last_error = NULL
                WHERE id = $1;
                """,
                event_id,
            )

    async def mark_outbox_event_failed(self, event_id: UUID, error: str) -> None:
        if self._pool is None:
            raise DatabaseUnavailableError("TimescaleDB pool is not connected")

        async with self._pool.acquire() as connection:
            await connection.execute(
                """
                UPDATE telemetry_outbox
                SET attempts = attempts + 1,
                    status = 'pending',
                    last_error = LEFT($2, 1000)
                WHERE id = $1
                  AND status IN ('pending', 'publishing');
                """,
                event_id,
                error,
            )

    def _row_to_outbox_event(self, row: asyncpg.Record) -> OutboxEvent:
        payload = row["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)

        return OutboxEvent(
            id=row["id"],
            topic=row["topic"],
            key=row["aggregate_id"],
            payload=payload,
        )
