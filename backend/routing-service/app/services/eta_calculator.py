import logging
import math

from app.core.bus_tracker import get_bus_position, get_positions

logger = logging.getLogger(__name__)

AVG_WALK_SPEED_KMH = 5.0
AVG_BUS_SPEED_KMH = 20.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def estimate_eta(bus_id: str, dest_lat: float, dest_lon: float) -> dict | None:
    pos = get_bus_position(bus_id)
    if not pos:
        return None
    if pos["latitude"] is None or pos["longitude"] is None:
        return None
    dist_km = _haversine_km(
        pos["latitude"], pos["longitude"],
        dest_lat, dest_lon,
    )
    speed = pos.get("speed_kmh") or AVG_BUS_SPEED_KMH
    if speed <= 0:
        speed = AVG_BUS_SPEED_KMH
    eta_min = round((dist_km / speed) * 60, 1)
    return {
        "bus_id": bus_id,
        "distance_km": round(dist_km, 2),
        "eta_min": eta_min,
        "current_speed_kmh": speed,
        "bus_position": {
            "latitude": pos["latitude"],
            "longitude": pos["longitude"],
        },
    }
