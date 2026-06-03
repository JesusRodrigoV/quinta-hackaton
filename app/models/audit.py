import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Clase base unificada para el mapeo relacional."""
    pass


class RegulatoryAuditLog(Base):
    """
    Representación física de la tabla de auditoría en PostgreSQL.
    Diseñada de forma agnóstica para guardar payloads polimórficos vía JSONB.
    """
    __tablename__ = "regulatory_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False,
        index=True
    )
    
    event_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        index=True
    )
    
    source_service: Mapped[str] = mapped_column(
        String(100), 
        nullable=False
    )
    
    actor: Mapped[str] = mapped_column(
        String(100), 
        nullable=False
    )
    
    payload: Mapped[dict] = mapped_column(
        JSONB, 
        nullable=False
    )
    
    hash_signature: Mapped[str] = mapped_column(
        String(64), 
        nullable=False
    )