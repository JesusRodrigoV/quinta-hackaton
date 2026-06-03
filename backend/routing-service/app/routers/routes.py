import logging
import uuid

from fastapi import APIRouter, HTTPException

from app.models.requests import RouteRequest
from app.schemas.responses import RouteResponse
from app.services.route_planner import plan_route, save_route, get_cached_route

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/routes", response_model=RouteResponse)
async def create_route(request: RouteRequest):
    result = await plan_route(request)
    if not result.options:
        raise HTTPException(
            404,
            "No se encontró ninguna ruta entre el origen y destino especificados",
        )

    route_id = str(uuid.uuid4())
    result.route_id = route_id
    try:
        await save_route(route_id, result)
    except Exception:
        logger.warning("Failed to cache route %s", route_id)
        result.route_id = None

    return result


@router.get("/routes/{route_id}", response_model=RouteResponse)
async def get_route(route_id: str):
    result = await get_cached_route(route_id)
    if not result:
        raise HTTPException(404, "Ruta no encontrada o expirada")
    return result
