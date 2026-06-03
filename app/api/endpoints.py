from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas.audit import AuditLogResponse
from app.services.audit_service import AuditService

# Creamos el enrutador específico para las consultas
router = APIRouter(prefix="/audit", tags=["Auditoría Regulatoria"])


@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    event_type: Optional[str] = Query(None, description="Filtrar por tipo: reroute_executed o tariff_modification"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Fecha fin (ISO 8601)"),
    skip: int = Query(0, ge=0, description="Registros a saltar (Paginación offset)"),
    limit: int = Query(100, ge=1, le=500, description="Límite máximo de registros devueltos por página"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Consulta el historial inmutable de auditoría.
    
    Este endpoint permite a los analistas de la alcaldía filtrar los eventos
    automáticos del sistema de transporte y peajes. Los datos retornados 
    incluyen la firma criptográfica para validación manual si se requiere.
    """
    logs = await AuditService.get_logs(
        db=db,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return logs