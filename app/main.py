import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# --- Importaciones de Auditoría (Andrés) ---
from app.core.config import settings
from app.api.router import api_router
from app.workers.kafka_consumer import kafka_worker
from app.schemas.audit import AuditLogCreate
from app.services.audit_service import AuditService
from app.core.database import get_async_db

# --- Importaciones de Movilidad (Natalia) ---
# Ojo: Asegúrate de que las configuraciones de su config.py se hayan mudado a core.config
from app.database import init_db, close_db, get_db
from app.kafka.producer import init_producer, close_producer
from app.kafka.consumer import start_consumer, stop_consumer
from app.routers import vehicles, reservations, health, damage_reports
from app.services.reservation_service import ReservationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("urbanflow.main")

# ==========================================
# 1. CICLO DE VIDA UNIFICADO (LIFESPAN)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🟢 Iniciando {getattr(settings, 'PROJECT_NAME', 'UrbanFlow API')}...")
    
    # -- 1A. Arranque Movilidad (Natalia) --
    await init_db()
    await init_producer()
    await start_consumer()
    
    scheduler = AsyncIOScheduler(timezone=getattr(settings, "APSCHEDULER_TIMEZONE", "UTC"))
    db = next(get_db()) # Asumiendo que get_db es un generador
    res_svc = ReservationService(db)
    scheduler.add_job(res_svc.expire_worker, IntervalTrigger(seconds=60))
    scheduler.start()
    logger.info("⏰ Scheduler de reservas iniciado")

    # -- 1B. Arranque Auditoría (Andrés) --
    await kafka_worker.start()
    
    yield # Servidor HTTP escuchando
    
    logger.info("🔴 Apagando servidor, limpiando conexiones...")
    
    # -- Apagado Auditoría --
    await kafka_worker.stop()
    
    # -- Apagado Movilidad --
    try:
        scheduler.shutdown(wait=False)
    except Exception:
        logger.exception("Error apagando el Scheduler")
    await stop_consumer()
    await close_producer()
    await close_db()

# ==========================================
# 2. INSTANCIA DE FASTAPI UNIFICADA
# ==========================================
app = FastAPI(
    title=getattr(settings, 'PROJECT_NAME', 'UrbanFlow API'),
    description="API Unificada: Movilidad Compartida y Auditoría Inmutable.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Registrar Enrutadores ---
app.include_router(api_router) # Rutas de Auditoría
app.include_router(health.router) # Rutas de Movilidad
app.include_router(vehicles.router)
app.include_router(reservations.router)
app.include_router(damage_reports.router)

# ==========================================
# 3. ENDPOINTS DE DEBUG
# ==========================================
@app.post("/debug/inject-event", tags=["Hackathon Debug (Ignorar en Prod)"])
async def debug_inject_event(log_in: AuditLogCreate, db: AsyncSession = Depends(get_async_db)):
    """Simula la llegada de un evento para probar la creación de la cadena de bloques."""
    return await AuditService.create_log(db=db, log_in=log_in)