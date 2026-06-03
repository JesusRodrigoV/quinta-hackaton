from datetime import datetime
from sqlalchemy import String, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class PredictionLog(Base):
    """
    Representación física de la tabla 'prediction_logs' en PostgreSQL.
    Almacena el historial de telemetría analizada y desvíos recomendados.
    """
    __tablename__ = "prediction_logs"

    id: Mapped[int] = mapped_column(
        primary_key=True, 
        index=True, 
        autoincrement=True
    )
    
    bus_id: Mapped[str] = mapped_column(
        String(50), 
        index=True, 
        nullable=False
    )
    
    corridor_id: Mapped[str] = mapped_column(
        String(100), 
        nullable=False
    )
    
    congestion_level: Mapped[float] = mapped_column(
        Float, 
        nullable=False
    )
    
    # Almacenamos las rutas como strings serializados (pueden ser listas de coordenadas)
    original_route: Mapped[str] = mapped_column(
        String, 
        nullable=True
    )
    
    suggested_route: Mapped[str] = mapped_column(
        String, 
        nullable=True
    )
    
    # Captura automática del tiempo del servidor de Base de Datos con zona horaria
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )