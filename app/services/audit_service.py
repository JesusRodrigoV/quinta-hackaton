from datetime import datetime
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.audit import RegulatoryAuditLog
from app.schemas.audit import AuditLogCreate, ReroutePayloadSchema, TariffPayloadSchema
from app.core.security import calculate_block_hash


class AuditService:
    
    @staticmethod
    async def create_log(db: AsyncSession, log_in: AuditLogCreate) -> RegulatoryAuditLog:
        """
        Valida el payload dinámico, recupera el último hash de la base de datos,
        calcula la nueva firma criptográfica y persiste el log de forma asíncrona.
        """
        # 1. Validar la estructura interna del payload según el tipo de evento
        try:
            if log_in.event_type == "reroute_executed":
                ReroutePayloadSchema(**log_in.payload)
            elif log_in.event_type == "tariff_modification":
                TariffPayloadSchema(**log_in.payload)
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"El payload no cumple con el contrato del evento '{log_in.event_type}': {str(err)}"
            )

        # 2. Obtener el hash del último registro guardado (Bloque Anterior)
        query_latest = select(RegulatoryAuditLog.hash_signature).order_by(desc(RegulatoryAuditLog.timestamp)).limit(1)
        result = await db.execute(query_latest)
        latest_hash = result.scalar_one_or_none()

        # Si es el primer registro del sistema, usamos un hash génesis por defecto
        if not latest_hash:
            latest_hash = "0" * 64

        # 3. Calcular el nuevo hash criptográfico encadenado
        new_signature = calculate_block_hash(
            previous_hash=latest_hash,
            event_type=log_in.event_type,
            actor=log_in.actor,
            payload=log_in.payload
        )

        # 4. Crear la instancia del modelo ORM
        db_log = RegulatoryAuditLog(
            event_type=log_in.event_type,
            source_service=log_in.source_service,
            actor=log_in.actor,
            payload=log_in.payload,
            hash_signature=new_signature
        )

        # 5. Persistir en la base de datos
        db.add(db_log)
        await db.commit()
        await db.refresh(db_log)
        return db_log

    @staticmethod
    async def get_logs(
        db: AsyncSession,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[RegulatoryAuditLog]:
        """
        Consulta los logs de auditoría aplicando filtros avanzados y paginación estricta
        para los requerimientos de fiscalización de la alcaldía.
        """
        stmt = select(RegulatoryAuditLog)

        # Filtros opcionales dinámicos
        if event_type:
            stmt = stmt.where(RegulatoryAuditLog.event_type == event_type)
        if start_date:
            stmt = stmt.where(RegulatoryAuditLog.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(RegulatoryAuditLog.timestamp <= end_date)

        # Paginación y ordenamiento cronológico inverso (lo más reciente primero)
        stmt = stmt.order_by(desc(RegulatoryAuditLog.timestamp)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())