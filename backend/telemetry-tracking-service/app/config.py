# app/config.py
from functools import lru_cache
from os import getenv

from dotenv import load_dotenv
from pydantic import Field
from pydantic.dataclasses import dataclass

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = Field(default_factory=lambda: getenv("APP_NAME", "Telemetry & Tracking Service"))
    app_env: str = Field(default_factory=lambda: getenv("APP_ENV", "local"))

    kafka_bootstrap_servers: str = Field(default_factory=lambda: getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    kafka_topic_bus_location_updated: str = Field(
        default_factory=lambda: getenv("KAFKA_TOPIC_BUS_LOCATION_UPDATED", "bus-location-updated")
    )

    timescaledb_host: str = Field(default_factory=lambda: getenv("TIMESCALEDB_HOST", "localhost"))
    timescaledb_port: int = Field(default_factory=lambda: int(getenv("TIMESCALEDB_PORT", "5433")))
    timescaledb_user: str = Field(default_factory=lambda: getenv("TIMESCALEDB_USER", "urbanflow_user"))
    timescaledb_password: str = Field(default_factory=lambda: getenv("TIMESCALEDB_PASSWORD", "dev_password_123"))
    timescaledb_database: str = Field(default_factory=lambda: getenv("TIMESCALEDB_DATABASE", "telemetry_db"))
    timescaledb_min_pool_size: int = Field(default_factory=lambda: int(getenv("TIMESCALEDB_MIN_POOL_SIZE", "1")))
    timescaledb_max_pool_size: int = Field(default_factory=lambda: int(getenv("TIMESCALEDB_MAX_POOL_SIZE", "10")))


@lru_cache
def get_settings() -> Settings:
    return Settings()
