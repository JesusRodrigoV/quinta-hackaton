from fastapi import APIRouter

from app.core.bus_tracker import get_positions, get_bus_position

router = APIRouter()


@router.get("/buses")
async def list_buses():
    positions = get_positions()
    return {
        "buses": positions,
        "count": len(positions),
    }


@router.get("/buses/{bus_id}")
async def get_bus(bus_id: str):
    pos = get_bus_position(bus_id)
    if not pos:
        from fastapi import HTTPException
        raise HTTPException(404, f"Bus {bus_id} not found")
    return pos
