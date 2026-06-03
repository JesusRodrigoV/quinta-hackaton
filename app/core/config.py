import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Parámetros del Proyecto
    PROJECT_NAME: str = Field(default="Prediction Engine")
    VERSION: str = Field(default="1.0.0")
    
    # Configuración de Base de Datos
    DATABASE_URL: str
    
    # Configuración de Kafka Backbone
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_CONSUMER_GROUP: str
    KAFKA_TOPIC_TELEMETRY: str
    KAFKA_TOPIC_REROUTE: str
    
    # Paths de Archivos y Modelos
    S3_MOCK_PARQUET_PATH: str
    MODEL_WEIGHTS_PATH: str

    # Configuración del cargador: Lee el archivo .env e ignora variables extra de la máquina
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instancia única (Singleton) para ser importada en todo el proyecto
settings = Settings()