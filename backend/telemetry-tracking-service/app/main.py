# app/main.py
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import TimescaleTelemetryRepository
from app.exceptions import DatabaseUnavailableError, EventPublishError
from app.models import AcceptedResponse, HealthResponse, ReadinessResponse, TelemetryPayload
from app.producer import BusLocationProducer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()
telemetry_repository = TimescaleTelemetryRepository(settings)
bus_location_producer = BusLocationProducer(settings)


async def dispatch_pending_outbox_events(application: FastAPI) -> None:
    repository: TimescaleTelemetryRepository = application.state.telemetry_repository
    producer: BusLocationProducer = application.state.bus_location_producer

    while not application.state.outbox_dispatcher_stop.is_set():
        try:
            pending_events = await repository.list_pending_outbox_events(settings.outbox_batch_size)
            for event in pending_events:
                try:
                    await producer.publish_event(event.topic, event.key, event.payload)
                    await repository.mark_outbox_event_published(event.id)
                except EventPublishError as exc:
                    await repository.mark_outbox_event_failed(event.id, str(exc))
        except Exception:
            logger.exception("Outbox dispatcher iteration failed")

        try:
            await asyncio.wait_for(
                application.state.outbox_dispatcher_stop.wait(),
                timeout=settings.outbox_dispatch_interval_seconds,
            )
        except asyncio.TimeoutError:
            continue


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    application.state.telemetry_repository = telemetry_repository
    application.state.bus_location_producer = bus_location_producer
    application.state.outbox_dispatcher_stop = asyncio.Event()
    application.state.outbox_dispatcher_task = None

    try:
        await telemetry_repository.connect()
        await bus_location_producer.connect()
        application.state.outbox_dispatcher_task = asyncio.create_task(dispatch_pending_outbox_events(application))
        yield
    finally:
        application.state.outbox_dispatcher_stop.set()
        if application.state.outbox_dispatcher_task is not None:
            application.state.outbox_dispatcher_task.cancel()
            try:
                await application.state.outbox_dispatcher_task
            except asyncio.CancelledError:
                pass
        await bus_location_producer.close()
        await telemetry_repository.close()


app = FastAPI(
    title=settings.app_name,
    version="1.1.0",
    description="Receives bus GPS telemetry, persists it in TimescaleDB, and emits Kafka location events.",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": "Invalid telemetry payload", "errors": exc.errors()}),
    )


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.app_name, environment=settings.app_env)


@app.get("/ready", response_model=ReadinessResponse, tags=["health"])
async def readiness_check(request: Request) -> ReadinessResponse:
    database_ready = await request.app.state.telemetry_repository.health_check()
    kafka_ready = await request.app.state.bus_location_producer.health_check()
    ready = database_ready and kafka_ready

    if not ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "degraded",
                "database": "ok" if database_ready else "unavailable",
                "kafka": "ok" if kafka_ready else "unavailable",
            },
        )

    return ReadinessResponse(status="ok", database="ok", kafka="ok")


@app.post(
    "/api/v1/telemetry",
    response_model=AcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["telemetry"],
)
async def ingest_telemetry(payload: TelemetryPayload, request: Request) -> AcceptedResponse:
    topic = settings.kafka_topic_bus_location_updated

    try:
        outbox_event = await request.app.state.telemetry_repository.write_bus_telemetry(payload, topic)
    except DatabaseUnavailableError as exc:
        logger.exception("Telemetry persistence failed for bus_id=%s", payload.bus_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    try:
        await request.app.state.bus_location_producer.publish_event(
            outbox_event.topic,
            outbox_event.key,
            outbox_event.payload,
        )
        await request.app.state.telemetry_repository.mark_outbox_event_published(outbox_event.id)
    except EventPublishError as exc:
        await request.app.state.telemetry_repository.mark_outbox_event_failed(outbox_event.id, str(exc))
        logger.warning(
            "Telemetry stored but Kafka publish failed; event_id=%s will be retried by outbox",
            outbox_event.id,
        )

    return AcceptedResponse(
        message="Telemetry accepted",
        event_id=outbox_event.id,
        topic=topic,
    )
