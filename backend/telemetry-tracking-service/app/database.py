# app/database.py
import logging

import asyncpg

from app.config import Settings
from app.models import TelemetryPayload

logger = logging.getLogger(__name__)

INIT_SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS timescaledb;

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
            )
            await self.initialize_schema()
            logger.info(
                "TimescaleDB pool connected to %s:%s/%s",
                self._settings.timescaledb_host,
                self._settings.timescaledb_port,
                self._settings.timescaledb_database,
            )
        except Exception:
            self._pool = None
            logger.exception("Failed to connect TimescaleDB")
            raise

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def initialize_schema(self) -> None:
        if self._pool is None:
            raise RuntimeError("TimescaleDB pool is not connected")

        async with self._pool.acquire() as connection:
            await connection.execute(INIT_SCHEMA_SQL)

    async def write_bus_telemetry(self, payload: TelemetryPayload) -> None:
        if self._pool is None:
            raise RuntimeError("TimescaleDB pool is not connected")

        try:
            async with self._pool.acquire() as connection:
                await connection.execute(
                    """
                    INSERT INTO bus_telemetry (
                        bus_id,
                        latitude,
                        longitude,
                        speed_kmh,
                        timestamp
                    )
                    VALUES ($1, $2, $3, $4, $5);
                    """,
                    payload.bus_id,
                    payload.latitude,
                    payload.longitude,
                    payload.speed_kmh,
                    payload.timestamp,
                )
        except Exception:
            logger.exception(
                "Failed to write telemetry to TimescaleDB for bus_id=%s",
                payload.bus_id,
            )
            raise
