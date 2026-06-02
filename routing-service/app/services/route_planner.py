import json
import logging

from fastapi import HTTPException

from app.core.graph import get_driver
from app.core.kafka import publish
from app.models.requests import RouteRequest
from app.schemas.responses import RouteResponse, RouteOption, Segment, StationInfo

logger = logging.getLogger(__name__)

MODE_FLAT_COST = {
    "bus": 0.70,
    "metro": 0.80,
    "walk": 0.0,
    "scooter": 0.0,
}

SCOOTER_COST_PER_MIN = 0.15
G_TO_KG = 0.001


def _segment_cost(seg: Segment) -> float:
    if seg.transport_mode == "scooter":
        return round(seg.travel_time_min * SCOOTER_COST_PER_MIN, 2)
    return MODE_FLAT_COST.get(seg.transport_mode, 0.0)


async def _nearest_stations(lat: float, lon: float, limit: int = 3):
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:Station)
            WITH s, point({latitude: $lat, longitude: $lon}) AS origin
            RETURN s,
                   point.distance(point({latitude: s.latitude, longitude: s.longitude}), origin) AS dist
            ORDER BY dist ASC
            LIMIT $limit
            """,
            lat=lat, lon=lon, limit=limit,
        )
        return await result.data()


async def _paths_between(start_id: str, end_id: str, modes: list[str]):
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH p = (start:Station {station_id: $start_id})
                      -[r:CONNECTS_TO*..6]->
                      (end:Station {station_id: $end_id})
            WHERE ALL(rel IN r WHERE rel.transport_mode IN $modes)
            WITH p,
                 reduce(t = 0, rel IN relationships(p) | t + rel.average_travel_time_sec) AS total_sec
            RETURN p, total_sec
            ORDER BY total_sec ASC
            LIMIT 3
            """,
            start_id=start_id, end_id=end_id, modes=modes,
        )
        records = []
        async for record in result:
            records.append({"p": record["p"], "total_sec": record["total_sec"]})
        return records


def _build_option(record: dict) -> RouteOption:
    path = record["p"]
    segments = []
    total_co2_grams = 0.0
    for rel in path.relationships:
        seg = Segment(
            from_station=StationInfo(
                station_id=rel.start_node["station_id"],
                name=rel.start_node["name"],
                type=rel.start_node["type"],
            ),
            to_station=StationInfo(
                station_id=rel.end_node["station_id"],
                name=rel.end_node["name"],
                type=rel.end_node["type"],
            ),
            transport_mode=rel["transport_mode"],
            line=rel.get("line"),
            travel_time_min=round(rel["average_travel_time_sec"] / 60, 1),
            distance_km=round(rel["distance_meters"] / 1000, 2),
        )
        segments.append(seg)
        total_co2_grams += rel.get("carbon_footprint_grams", 0)
    total_cost = sum(_segment_cost(s) for s in segments)
    total_time_min = sum(s.travel_time_min for s in segments)
    return RouteOption(
        total_time_min=round(total_time_min, 1),
        total_cost=round(total_cost, 2),
        total_co2_kg=round(total_co2_grams * G_TO_KG, 3),
        segments=segments,
    )


async def save_route(route_id: str, response: RouteResponse):
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            CREATE (:CachedRoute {
                route_id: $route_id,
                response_json: $response_json,
                created_at: datetime()
            })
            """,
            route_id=route_id,
            response_json=response.model_dump_json(),
        )


async def get_cached_route(route_id: str) -> RouteResponse | None:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (r:CachedRoute {route_id: $route_id}) RETURN r",
            route_id=route_id,
        )
        record = await result.single()
        if not record:
            return None
        data = json.loads(record["r"]["response_json"])
        return RouteResponse(**data)


async def cleanup_expired_routes():
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (r:CachedRoute)
            WHERE r.created_at < datetime() - duration({hours: 1})
            DELETE r
            RETURN count(r) AS deleted
            """,
        )
        row = await result.single()
        count = row["deleted"]
        if count > 0:
            logger.info("Expired cached routes cleaned: %d", count)


async def plan_route(request: RouteRequest) -> RouteResponse:
    origin_stations = await _nearest_stations(request.origin_lat, request.origin_lon)
    dest_stations = await _nearest_stations(request.dest_lat, request.dest_lon)
    if not origin_stations or not dest_stations:
        raise HTTPException(404, "No stations found near origin or destination")
    all_options = []
    for o_station in origin_stations[:2]:
        for d_station in dest_stations[:2]:
            paths = await _paths_between(
                o_station["s"]["station_id"],
                d_station["s"]["station_id"],
                request.modes,
            )
            for record in paths:
                all_options.append(_build_option(record))
    seen: set[str] = set()
    unique: list[RouteOption] = []
    for opt in all_options:
        sig = "-".join(
            f"{s.from_station.station_id}>{s.to_station.station_id}"
            for s in opt.segments
        )
        if sig not in seen:
            seen.add(sig)
            unique.append(opt)
    sort_key = {"time": "total_time_min", "cost": "total_cost", "co2": "total_co2_kg"}
    pref = request.preference or "time"
    unique.sort(key=lambda x: getattr(x, sort_key.get(pref, "total_time_min")))
    await publish(
        "route:calculated",
        key=f"{request.origin_lat},{request.origin_lon}-{request.dest_lat},{request.dest_lon}",
        value={
            "options_count": len(unique),
            "best_time_min": unique[0].total_time_min if unique else None,
        },
    )
    return RouteResponse(options=unique[:5])
