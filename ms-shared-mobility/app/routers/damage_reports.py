from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.services.reservation_service import ReservationService
from app.models import DamageReportCreate

router = APIRouter(prefix="/api/v1", tags=["damage_reports"])


def _service(db=Depends(get_db)) -> ReservationService:
    return ReservationService(db)


@router.post("/damage-reports")
async def report_damage(payload: DamageReportCreate, svc: ReservationService = Depends(_service)):
    try:
        res = await svc.report_damage(payload.vehicle_id, payload.severity, str(payload.user_id), payload.description)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
