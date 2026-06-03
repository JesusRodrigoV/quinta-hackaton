import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ---------------------------------------------------------------------
# PASO 4.2 & 4.3: Integración con la Arquitectura de la Aplicación
# ---------------------------------------------------------------------
from app.core.config import settings
from app.db.base import Base
# Importamos el paquete de modelos para asegurar que SQLAlchemy registre la tabla en los metadatos
import app.models  

# Objeto de configuración de Alembic
config = context.config

# Inyectamos dinámicamente la URL del .env reemplazando cualquier valor del archivo .ini
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configura el sistema de logs nativo de Alembic
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Vinculamos los metadatos de nuestros modelos para activar el autogenerate
target_metadata = Base.metadata
# ---------------------------------------------------------------------


def run_migrations_offline() -> None:
    """Ejecuta las migraciones en modo 'offline' (genera scripts SQL sin conectarse)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Ejecuta las migraciones en el hilo de la conexión asíncrona activa."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Ejecuta las migraciones en modo 'online' (conectándose a la BD real)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())