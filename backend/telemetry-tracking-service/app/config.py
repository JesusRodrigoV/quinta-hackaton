# app/config.py
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(SERVICE_ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=SERVICE_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Telemetry & Tracking Service"
    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_bus_location_updated: str = "bus-location-updated"
    kafka_flush_timeout_seconds: int = Field(default=10, ge=1, le=60)

    timescaledb_host: str = "localhost"
    timescaledb_port: int = Field(default=5433, ge=1, le=65535)
    timescaledb_user: str = "urbanflow_user"
    timescaledb_password: str = "dev_password_123"
    timescaledb_database: str = "telemetry_db"
    timescaledb_min_pool_size: int = Field(default=1, ge=1)
    timescaledb_max_pool_size: int = Field(default=10, ge=1)

    outbox_dispatch_interval_seconds: int = Field(default=5, ge=1, le=300)
    outbox_batch_size: int = Field(default=100, ge=1, le=1000)
    outbox_stale_after_seconds: int = Field(default=60, ge=10, le=3600)

    @field_validator("timescaledb_max_pool_size")
    @classmethod
    def validate_pool_size(cls, value: int, info) -> int:
        min_pool_size = info.data.get("timescaledb_min_pool_size", 1)
        if value < min_pool_size:
            raise ValueError("TIMESCALEDB_MAX_POOL_SIZE must be greater than or equal to TIMESCALEDB_MIN_POOL_SIZE")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
