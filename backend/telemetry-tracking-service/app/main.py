# app/main.py
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request, status

from app.config import get_settings
from app.database import TimescaleTelemetryRepository
from app.models import AcceptedResponse, TelemetryPayload
from app.producer import BusLocationProducer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()
telemetry_repository = TimescaleTelemetryRepository(settings)
bus_location_producer = BusLocationProducer(settings)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    try:
        application.state.telemetry_repository = telemetry_repository
        application.state.bus_location_producer = bus_location_producer
        await telemetry_repository.connect()
        await bus_location_producer.connect()
        yield
    finally:
        await bus_location_producer.close()
        await telemetry_repository.close()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Receives bus GPS telemetry, persists it in TimescaleDB, and emits Kafka location events.",
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "environment": settings.app_env}


@app.post(
    "/api/v1/telemetry",
    response_model=AcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["telemetry"],
)
async def ingest_telemetry(payload: TelemetryPayload, request: Request) -> AcceptedResponse:
    try:
        await request.app.state.telemetry_repository.write_bus_telemetry(payload)
        await request.app.state.bus_location_producer.publish_bus_location_updated(payload)
    except RuntimeError as exc:
        logger.exception("Telemetry dependencies are not ready")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Telemetry ingestion failed for bus_id=%s", payload.bus_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to persist telemetry or publish event",
        ) from exc

    return AcceptedResponse(
        message="Telemetry accepted",
        topic=settings.kafka_topic_bus_location_updated,
    )
