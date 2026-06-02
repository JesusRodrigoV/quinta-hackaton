import logging
from typing import Dict
from app.kafka.producer import publish_event

logger = logging.getLogger(__name__)


async def publish_ride_started(vehicle_id: str, user_id: str, reservation_id: str, lat: float, lng: float) -> None:
    payload = {
        "vehicle_id": vehicle_id,
        "user_id": str(user_id),
        "reservation_id": reservation_id,
        "lat": lat,
        "lng": lng,
    }
    await publish_event("shared-mobility.ride.started", payload)


async def publish_ride_ended(reservation_id: str, duration_minutes: int, total_cost_usd: float) -> None:
    payload = {
        "reservation_id": reservation_id,
        "duration_minutes": duration_minutes,
        "total_cost_usd": total_cost_usd,
    }
    await publish_event("shared-mobility.ride.ended", payload)


async def publish_vehicle_damaged(vehicle_id: str, severity: str, reported_by: str) -> None:
    payload = {"vehicle_id": vehicle_id, "severity": severity, "reported_by": reported_by}
    await publish_event("shared-mobility.vehicle.damaged", payload)


async def publish_zone_understock(zone_lat: float, zone_lng: float, available_count: int) -> None:
    payload = {"zone_lat": zone_lat, "zone_lng": zone_lng, "available_count": available_count}
    await publish_event("shared-mobility.zone.understock", payload)
