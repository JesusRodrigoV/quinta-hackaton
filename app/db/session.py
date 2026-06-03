from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Paso 2.2: Configuración del motor asíncrono exclusivo
# echo=True mapeará todas las consultas SQL nativas en la terminal, ideal para depurar flujos durante la hackatón.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True
)

# Paso 2.3: Generador de sesiones asíncronas (Session Factory)
# Instancia configurada para manejar el ciclo de vida transaccional sin colisionar con el loop asíncrono.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependencia para FastAPI y procesos en segundo plano
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Generador asíncrono que provee una sesión de base de datos contextual.
    Garantiza la apertura, ejecución y el cierre seguro de la conexión (anti-fugas).
    """
    async with AsyncSessionLocal() as session:
        yield session