"""Configuration management for Traffic Light Service."""
from functools import lru_cache
from os import getenv

from dotenv import load_dotenv
from pydantic import Field
from pydantic.dataclasses import dataclass

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = Field(default_factory=lambda: getenv("APP_NAME", "Traffic Light Control Service"))
    app_env: str = Field(default_factory=lambda: getenv("APP_ENV", "local"))

    # Kafka
    kafka_bootstrap_servers: str = Field(default_factory=lambda: getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    kafka_group_id: str = Field(default_factory=lambda: getenv("KAFKA_GROUP_ID", "traffic-light-service"))
    kafka_topic_bus_delayed: str = Field(default_factory=lambda: getenv("KAFKA_TOPIC_BUS_DELAYED", "tracking.bus.delayed"))
    kafka_topic_congestion_alert: str = Field(default_factory=lambda: getenv("KAFKA_TOPIC_CONGESTION_ALERT", "congestion.alert.created"))
    kafka_topic_signal_reroute: str = Field(default_factory=lambda: getenv("KAFKA_TOPIC_SIGNAL_REROUTE", "signal.reroute.confirmed"))

    # Redis
    redis_host: str = Field(default_factory=lambda: getenv("REDIS_HOST", "localhost"))
    redis_port: int = Field(default_factory=lambda: int(getenv("REDIS_PORT", "6379")))
    redis_db: int = Field(default_factory=lambda: int(getenv("REDIS_DB", "0")))
    redis_password: str | None = Field(default_factory=lambda: getenv("REDIS_PASSWORD", None))

    # PostgreSQL (Audit)
    postgres_host: str = Field(default_factory=lambda: getenv("POSTGRES_HOST", "localhost"))
    postgres_port: int = Field(default_factory=lambda: int(getenv("POSTGRES_PORT", "5432")))
    postgres_user: str = Field(default_factory=lambda: getenv("POSTGRES_USER", "urbanflow_user"))
    postgres_password: str = Field(default_factory=lambda: getenv("POSTGRES_PASSWORD", "dev_password_123"))
    postgres_database: str = Field(default_factory=lambda: getenv("POSTGRES_DATABASE", "audit_db"))

    # NTCIP
    ntcip_max_payload_bytes: int = Field(default_factory=lambda: int(getenv("NTCIP_MAX_PAYLOAD_BYTES", "256")))
    ntcip_reroute_timeout_sec: int = Field(default_factory=lambda: int(getenv("NTCIP_REROUTE_TIMEOUT_SEC", "10")))


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
