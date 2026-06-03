# app/exceptions.py
class TelemetryServiceError(Exception):
    """Base exception for service-level failures."""


class DatabaseUnavailableError(TelemetryServiceError):
    """Raised when TimescaleDB is unavailable or not initialized."""


class EventPublishError(TelemetryServiceError):
    """Raised when Kafka cannot publish an event."""
