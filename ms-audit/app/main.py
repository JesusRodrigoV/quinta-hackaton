import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.api.router import api_router
from app.workers.kafka_consumer import kafka_worker

# Configuración básica de logs para la consola
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("urbanflow.main")

# ==========================================
# 1. CICLO DE VIDA (LIFESPAN)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Controla los eventos de arranque y apagado del servidor.
    Todo lo que está antes del 'yield' se ejecuta al iniciar.
    Todo lo que está después del 'yield' se ejecuta al apagar (Ctrl+C).
    """
    logger.info(f"🟢 Iniciando {settings.PROJECT_NAME}...")
    
    # Encendemos el hilo del consumidor de Kafka
    await kafka_worker.start()
    
    yield # Aquí FastAPI levanta el servidor HTTP para recibir peticiones
    
    logger.info("🔴 Apagando servidor, limpiando conexiones...")
    # Apagamos Kafka de forma segura para no dejar hilos huérfanos
    await kafka_worker.stop()

# ==========================================
# 2. INSTANCIA DE FASTAPI
# ==========================================
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Microservicio inmutable de auditoría con validación criptográfica.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS para permitir que el Frontend consuma la API sin errores
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción, cambia esto por el dominio del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar los enrutadores oficiales
app.include_router(api_router)

# ==========================================
# 3. ENDPOINT DE DEBUG PARA LA HACKATHON
# ==========================================
# Solo para poder inyectar datos desde Postman sin necesidad de tener Kafka activo
from app.schemas.audit import AuditLogCreate
from app.services.audit_service import AuditService
from app.core.database import get_async_db

@app.post("/debug/inject-event", tags=["Hackathon Debug (Ignorar en Prod)"])
async def debug_inject_event(log_in: AuditLogCreate, db: AsyncSession = Depends(get_async_db)):
    """Simula la llegada de un evento para probar la creación de la cadena de bloques."""
    return await AuditService.create_log(db=db, log_in=log_in)