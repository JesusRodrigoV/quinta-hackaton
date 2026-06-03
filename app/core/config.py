from typing import List
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Configuración de Pydantic Settings para apuntar al archivo .env
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    # Entorno y Proyecto
    ENVIRONMENT: str = Field(default="development")
    PROJECT_NAME: str = Field(default="UrbanFlow Audit Service")

    # Credenciales de Base de Datos
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str

    # Parámetros de Kafka Cluster
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_CONSUMER_GROUP: str = Field(default="audit-regulatory-group")

    # Tópicos de Eventos
    KAFKA_TOPIC_REROUTE: str
    KAFKA_TOPIC_TARIFF: str

    # Clave de encriptación interna para Hashes
    SECRET_CRYPTO_SALT: str

    # Propiedad calculada dinámicamente para construir la URL asíncrona de SQLAlchemy
    @computed_field
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Propiedad calculada para retornar la lista de tópicos a los que se suscribirá el Worker
    @computed_field
    @property
    def KAFKA_TOPICS(self) -> List[str]:
        return [self.KAFKA_TOPIC_REROUTE, self.KAFKA_TOPIC_TARIFF]


# Instancia global para importar en cualquier módulo del sistema
settings = Settings()