from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc

from app.core.database import get_async_db
from app.models.audit import RegulatoryAuditLog
from app.core.security import calculate_block_hash

router = APIRouter(prefix="/compliance", tags=["Cumplimiento e Integridad"])


@router.get("/verify-chain")
async def verify_ledger_integrity(db: AsyncSession = Depends(get_async_db)):
    """
    Auditoría Profunda: Recorre la base de datos secuencialmente desde su inicio,
    recalculando las firmas criptográficas para certificar matemáticamente que 
    ningún registro ha sido alterado, corrompido o borrado.
    """
    # 1. Obtener todos los registros en orden cronológico ESTRICTO
    stmt = select(RegulatoryAuditLog).order_by(asc(RegulatoryAuditLog.timestamp))
    result = await db.execute(stmt)
    all_logs = result.scalars().all()

    if not all_logs:
        return {"status": "ok", "message": "El ledger está vacío.", "is_valid": True}

    # 2. Iniciar la verificación desde el bloque génesis (ceros)
    previous_hash = "0" * 64
    corrupted_logs = []
    is_valid = True

    # 3. Recorrer la cadena bloque a bloque
    for log in all_logs:
        # Recalculamos matemáticamente el hash que debería tener este registro
        expected_hash = calculate_block_hash(
            previous_hash=previous_hash,
            event_type=log.event_type,
            actor=log.actor,
            payload=log.payload
        )

        # Si el hash calculado no coincide con el guardado en BD = MANIPULACIÓN
        if expected_hash != log.hash_signature:
            is_valid = False
            corrupted_logs.append({
                "id": str(log.id),
                "timestamp": log.timestamp,
                "expected_hash": expected_hash,
                "actual_hash": log.hash_signature
            })
            break # Rompemos el ciclo porque si un eslabón falla, el resto de la cadena también.

        # El hash actual se convierte en el previo para el siguiente ciclo
        previous_hash = log.hash_signature

    # 4. Generar reporte de cumplimiento
    if is_valid:
        return {
            "status": "success",
            "is_valid": True,
            "message": f"Auditoría superada: La cadena de {len(all_logs)} registros está intacta y es criptográficamente segura."
        }
    else:
        return {
            "status": "danger",
            "is_valid": False,
            "message": "¡ALERTA CRÍTICA! Se ha detectado manipulación o pérdida de datos en el ledger de auditoría.",
            "corrupted_blocks": corrupted_logs
        }