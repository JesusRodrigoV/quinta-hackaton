from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

# 1. Crear el motor asíncrono utilizando el driver 'asyncpg'
# 'echo=True' imprimirá todas las consultas SQL en consola si estamos en desarrollo.
async_engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    future=True,
    pool_pre_ping=True,  # Verifica la validez de las conexiones antes de usarlas
    pool_size=20,        # Número base de conexiones concurrentes en el pool
    max_overflow=10      # Conexiones adicionales permitidas en ráfagas de tráfico
)

# 2. Configurar la fábrica de sesiones asíncronas (Session Factory)
# 'expire_on_commit=False' es vital en entornos asíncronos para evitar accesos perezosos (lazy loads) erróneos.
async_session_maker = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 3. Generador de Sesiones (Dependencia para inyectar en los Endpoints de FastAPI)
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Instancia una sesión de base de datos asíncrona para cada petición HTTP,
    realiza un yield de la sesión hacia el controlador y garantiza su cierre
    automático al finalizar la petición (incluso si ocurre un error).
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()