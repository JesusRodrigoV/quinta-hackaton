"""Main FastAPI application for Traffic Light Service."""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, status

from app.config import get_settings
from app.consumer import TrafficSignalConsumer
from app.database import AuditRepository, SignalStateRepository
from app.models import SignalState_Response

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()
signal_repo = SignalStateRepository(settings)
audit_repo = AuditRepository(settings)
consumer = TrafficSignalConsumer(settings, signal_repo, audit_repo)
consumer_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Manage service lifecycle: connect/disconnect and start consumer."""
    try:
        application.state.signal_repo = signal_repo
        application.state.audit_repo = audit_repo
        application.state.consumer = consumer

        await signal_repo.connect()
        await audit_repo.connect()
        await consumer.connect()

        # Start consumer in background task
        global consumer_task
        consumer_task = asyncio.create_task(consumer.start_consuming())

        logger.info("Traffic Light Service started successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise
    finally:
        if consumer_task and not consumer_task.done():
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass

        await consumer.close()
        await audit_repo.close()
        await signal_repo.close()
        logger.info("Traffic Light Service stopped")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Receives traffic signal events from Kafka, translates to NTCIP commands, and manages real-time signal state.",
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }


@app.get("/ready", tags=["health"])
async def readiness_check() -> dict[str, str]:
    """Readiness check: verify Redis and PostgreSQL connectivity."""
    try:
        # Test Redis
        await app.state.signal_repo._redis.ping()
        # Test PostgreSQL
        async with app.state.audit_repo._pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service dependencies not ready",
        )


@app.get(
    "/api/v1/signals/{intersection_id}",
    response_model=SignalState_Response | dict,
    tags=["signals"],
)
async def get_signal_state(intersection_id: str) -> SignalState_Response | dict:
    """Get current state of a traffic signal."""
    try:
        state = await app.state.signal_repo.get_signal_state(intersection_id)
        if state is None:
            return {
                "intersection_id": intersection_id,
                "current_state": "green",
                "timer_remaining_sec": 60,
                "priority_override_active": False,
                "last_updated": None,
                "message": "No state found; returning default",
            }
        return {
            "intersection_id": intersection_id,
            "current_state": state.get("current_state", "green"),
            "timer_remaining_sec": int(state.get("timer_remaining_sec", 60)),
            "priority_override_active": state.get("priority_override_active") == "True",
            "last_updated": state.get("last_updated"),
        }
    except Exception as e:
        logger.exception(f"Failed to get signal state for {intersection_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.get("/api/v1/audit/logs", tags=["audit"])
async def get_audit_logs(limit: int = 100, offset: int = 0) -> dict:
    """Retrieve recent audit logs for compliance review."""
    try:
        async with app.state.audit_repo._pool.acquire() as conn:
            logs = await conn.fetch(
                """
                SELECT log_id, timestamp, event_type, intersection_id, bus_id, 
                       priority_level, status, details
                FROM signal_audit_log
                ORDER BY timestamp DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
        return {"total": len(logs), "logs": [dict(log) for log in logs]}
    except Exception as e:
        logger.exception("Failed to retrieve audit logs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
