from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from uuid import UUID
from decimal import Decimal

from app.database import get_db
from app.services.reservation_service import ReservationService
from app.models import ReservationCreate, EndRideRequest

router = APIRouter(prefix="/api/v1/reservations", tags=["reservations"])


def _service(db=Depends(get_db)) -> ReservationService:
    return ReservationService(db)


@router.post("", status_code=201)
async def create_reservation(payload: ReservationCreate, svc: ReservationService = Depends(_service)):
    try:
        res = await svc.create_reservation(payload.user_id, payload.vehicle_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{id}")
async def get_reservation(id: str, svc: ReservationService = Depends(_service)):
    r = await svc.get_reservation(id)
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return r


@router.get("/user/{user_id}/active")
async def get_active(user_id: UUID, svc: ReservationService = Depends(_service)):
    r = await svc.get_active_by_user(user_id)
    if not r:
        raise HTTPException(status_code=404, detail="No active reservation")
    return r


@router.post("/{id}/unlock")
async def unlock(id: str, svc: ReservationService = Depends(_service)):
    try:
        res = await svc.unlock(id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/end-ride")
async def end_ride(id: str, payload: EndRideRequest, background_tasks: BackgroundTasks, svc: ReservationService = Depends(_service)):
    try:
        res = await svc.end_ride(id, payload.final_lat, payload.final_lng)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{id}")
async def cancel(id: str, svc: ReservationService = Depends(_service)):
    try:
        res = await svc.cancel_reservation(id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
