"""Database and cache management for Traffic Light Service."""
import logging
from datetime import datetime, timezone

import asyncpg
import redis.asyncio as redis

from app.config import Settings
from app.exceptions import DatabaseUnavailableError, RedisUnavailableError
from app.models import AuditLogEntry, SignalState

logger = logging.getLogger(__name__)

INIT_AUDIT_SQL = """
CREATE TABLE IF NOT EXISTS signal_audit_log (
    log_id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    intersection_id VARCHAR(100) NOT NULL,
    bus_id VARCHAR(100),
    priority_level VARCHAR(50),
    status VARCHAR(20) NOT NULL,
    details TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signal_audit_timestamp
    ON signal_audit_log (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_signal_audit_intersection
    ON signal_audit_log (intersection_id);
"""


class SignalStateRepository:
    """Redis cache for real-time traffic signal state."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._redis: redis.Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._redis = redis.Redis(
                host=self._settings.redis_host,
                port=self._settings.redis_port,
                db=self._settings.redis_db,
                password=self._settings.redis_password,
                decode_responses=True,
            )
            await self._redis.ping()
            logger.info(
                "Redis connected to %s:%s",
                self._settings.redis_host,
                self._settings.redis_port,
            )
        except Exception:
            self._redis = None
            logger.exception("Failed to connect to Redis")
            raise

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None

    async def get_signal_state(self, intersection_id: str) -> dict | None:
        """Get current state of a traffic signal."""
        if self._redis is None:
            raise RedisUnavailableError("Redis is not connected")

        try:
            key = f"traffic_light:{intersection_id}"
            state = await self._redis.hgetall(key)
            return state if state else None
        except Exception:
            logger.exception("Failed to get signal state for %s", intersection_id)
            raise

    async def set_signal_state(
        self,
        intersection_id: str,
        state: SignalState,
        timer_sec: int = 60,
        priority_override: bool = False,
    ) -> None:
        """Set traffic signal state with optional priority override."""
        if self._redis is None:
            raise RedisUnavailableError("Redis is not connected")

        try:
            key = f"traffic_light:{intersection_id}"
            await self._redis.hset(
                key,
                mapping={
                    "current_state": state.value,
                    "timer_remaining_sec": timer_sec,
                    "priority_override_active": str(priority_override),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                },
            )
            await self._redis.expire(key, 3600)  # TTL: 1 hour
            logger.info(
                "Signal state set for %s: %s (priority=%s)",
                intersection_id,
                state.value,
                priority_override,
            )
        except Exception:
            logger.exception("Failed to set signal state for %s", intersection_id)
            raise


class AuditRepository:
    """PostgreSQL persistence for audit logs."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Connect to PostgreSQL."""
        try:
            self._pool = await asyncpg.create_pool(
                host=self._settings.postgres_host,
                port=self._settings.postgres_port,
                user=self._settings.postgres_user,
                password=self._settings.postgres_password,
                database=self._settings.postgres_database,
                min_size=1,
                max_size=10,
            )
            await self.initialize_schema()
            logger.info(
                "PostgreSQL pool connected to %s:%s/%s",
                self._settings.postgres_host,
                self._settings.postgres_port,
                self._settings.postgres_database,
            )
        except Exception:
            self._pool = None
            logger.exception("Failed to connect PostgreSQL")
            raise

    async def close(self) -> None:
        """Close PostgreSQL connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def initialize_schema(self) -> None:
        """Initialize database schema (idempotent)."""
        if self._pool is None:
            raise DatabaseUnavailableError("PostgreSQL pool is not connected")

        async with self._pool.acquire() as connection:
            await connection.execute(INIT_AUDIT_SQL)

    async def write_audit_log(self, entry: AuditLogEntry) -> None:
        """Write audit log entry (immutable append-only)."""
        if self._pool is None:
            raise DatabaseUnavailableError("PostgreSQL pool is not connected")

        try:
            async with self._pool.acquire() as connection:
                await connection.execute(
                    """
                    INSERT INTO signal_audit_log (
                        log_id,
                        timestamp,
                        event_type,
                        intersection_id,
                        bus_id,
                        priority_level,
                        status,
                        details
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8);
                    """,
                    entry.log_id,
                    entry.timestamp,
                    entry.event_type,
                    entry.intersection_id,
                    entry.bus_id,
                    entry.priority_level,
                    entry.status,
                    entry.details,
                )
        except Exception:
            logger.exception("Failed to write audit log for %s", entry.log_id)
            raise
