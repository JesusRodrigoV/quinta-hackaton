"""Custom exceptions for Traffic Light Service."""


class TrafficLightServiceError(Exception):
    """Base exception for service-level failures."""


class RedisUnavailableError(TrafficLightServiceError):
    """Raised when Redis is unavailable."""


class DatabaseUnavailableError(TrafficLightServiceError):
    """Raised when PostgreSQL audit database is unavailable."""


class EventConsumptionError(TrafficLightServiceError):
    """Raised when Kafka consumer fails."""


class NTCIPTranslationError(TrafficLightServiceError):
    """Raised when NTCIP payload translation fails."""
