from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

from app.database import get_db
from app.models import VehicleCreate, VehicleLocationUpdate, VehicleOut
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/api/v1/vehicles", tags=["vehicles"])


def _vehicle_service(db=Depends(get_db)) -> VehicleService:
    return VehicleService(db)


@router.get("/available", response_model=List[dict])
async def get_available(lat: float, lng: float, radius_meters: int = 500, svc: VehicleService = Depends(_vehicle_service)):
    docs = await svc.find_available_nearby(lat, lng, radius_meters)
    # append distance_meters already present
    return docs


@router.get("/{vehicle_id}", response_model=dict)
async def get_vehicle(vehicle_id: str, svc: VehicleService = Depends(_vehicle_service)):
    v = await svc.get_vehicle(vehicle_id)
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return v


@router.post("", response_model=dict, status_code=201)
async def create_vehicle(payload: VehicleCreate, svc: VehicleService = Depends(_vehicle_service)):
    v = await svc.register_vehicle(payload)
    return v


@router.patch("/{vehicle_id}/location", response_model=dict)
async def update_location(vehicle_id: str, payload: VehicleLocationUpdate, svc: VehicleService = Depends(_vehicle_service)):
    v = await svc.update_location(vehicle_id, payload.lat, payload.lng, payload.battery_level)
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return v
