from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.workers.telemetry_consumer import telemetry_worker
from app.services.kafka_producer import event_producer

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prediction_engine")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- ARRANQUE: Conectando servicios ---
    logger.info(f"🚀 Iniciando {settings.PROJECT_NAME}...")
    
    # Iniciar productor
    await event_producer.start()
    
    # Iniciar consumidor (Corre en background)
    await telemetry_worker.start()
    
    logger.info("✅ Todos los servicios están operacionales.")
    
    yield
    
    # --- APAGADO: Limpiando recursos ---
    logger.info("🔴 Apagando motor...")
    await telemetry_worker.stop()
    await event_producer.stop()
    logger.info("🏁 Sistema detenido limpiamente.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "up", "version": settings.VERSION}