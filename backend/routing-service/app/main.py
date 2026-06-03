import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.bus_tracker import stop as stop_tracker
from app.core.bus_tracker import start as start_tracker
from app.core.graph import init_driver, close_driver
from app.core.kafka import init_kafka, close_kafka
from app.routers import buses, routes, stops
from app.seed.loader import seed_database
from app.services.route_planner import cleanup_expired_routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando Routing Service …")
    await init_driver()
    await seed_database()
    await cleanup_expired_routes()
    await init_kafka()
    await start_tracker()
    yield
    await stop_tracker()
    await close_kafka()
    await close_driver()
    logger.info("Routing Service finalizado")


app = FastAPI(
    title="UrbanFlow — Routing Service",
    description="Planificador de rutas multimodales con soporte para bus, metro, scooter y caminata",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api/v1", tags=["Routes"])
app.include_router(stops.router, prefix="/api/v1", tags=["Stops"])
app.include_router(buses.router, prefix="/api/v1", tags=["Buses"])
