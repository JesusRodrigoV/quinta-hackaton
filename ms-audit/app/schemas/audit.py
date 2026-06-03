from datetime import datetime
from typing import Any, Dict, Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# ==========================================
# 1. ESQUEMAS DE PAYLOADS ESPECÍFICOS
# ==========================================

class ReroutePayloadSchema(BaseModel):
    """Estructura estricta para el payload de re-enrutamiento de buses."""
    corridor_id: str = Field(..., description="ID de la zona o corredor congestionado")
    bus_id: str = Field(..., description="Identificador único del vehículo/bus afectado")
    route_id: str = Field(..., description="Línea de transporte o ruta original")
    predicted_delay_minutes: int = Field(..., ge=0, description="Retraso proyectado en minutos")
    alternative_route_nodes: list[str] = Field(..., description="Nodos/Estaciones de desvío asignados")
    system_accuracy_score: float = Field(..., description="Métrica de confianza del modelo predictor")

class TariffPayloadSchema(BaseModel):
    """Estructura estricta para el payload de modificación de tarifas."""
    transport_mode: Literal["bus", "metro", "scooter"] = Field(..., description="Modo de transporte afectado")
    zone_id: str = Field(..., description="Zona geográfica o línea donde aplica el cambio")
    previous_tariff: float = Field(..., ge=0, description="Tarifa anterior en moneda local")
    new_tariff: float = Field(..., ge=0, description="Nueva tarifa decretada")
    approval_decree_number: str = Field(..., description="Número de resolución/decreto municipal de la alcaldía")


# ==========================================
# 2. ESQUEMAS GENÉRICOS DE AUDITORÍA (API)
# ==========================================

class AuditLogCreate(BaseModel):
    """Esquema base para procesar la llegada cruda de un evento."""
    event_type: Literal["reroute_executed", "tariff_modification"] = Field(...)
    source_service: str = Field(..., max_length=100)
    actor: str = Field(..., max_length=100)
    payload: Dict[str, Any] = Field(..., description="Datos libres que serán validados dinámicamente")


class AuditLogResponse(BaseModel):
    """Esquema de salida serializado para las consultas del Ente Regulador."""
    model_config = ConfigDict(from_attributes=True) # Permite leer modelos ORM de SQLAlchemy

    id: UUID
    timestamp: datetime
    event_type: str
    source_service: str
    actor: str
    payload: Dict[str, Any]
    hash_signature: str