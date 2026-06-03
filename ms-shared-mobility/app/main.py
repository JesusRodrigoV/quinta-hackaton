import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.database import init_db, close_db, get_db
from app.kafka.producer import init_producer, close_producer
from app.kafka.consumer import start_consumer, stop_consumer
from app.routers import vehicles, reservations, health, damage_reports
from app.services.reservation_service import ReservationService

import asyncio

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await init_db()
    await init_producer()
    await start_consumer()

    # start scheduler
    scheduler = AsyncIOScheduler(timezone=settings.APSCHEDULER_TIMEZONE)
    db = get_db()
    res_svc = ReservationService(db)
    scheduler.add_job(res_svc.expire_worker, IntervalTrigger(seconds=60))
    scheduler.start()
    logger.info("Scheduler started")

    yield

    # shutdown
    try:
        scheduler.shutdown(wait=False)
    except Exception:
        logger.exception("Scheduler shutdown failed")
    await stop_consumer()
    await close_producer()
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)

    app.include_router(health.router)
    app.include_router(vehicles.router)
    app.include_router(reservations.router)
    app.include_router(damage_reports.router)

    return app


app = create_app()
