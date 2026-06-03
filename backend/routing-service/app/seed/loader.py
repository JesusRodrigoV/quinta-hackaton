import logging

from app.core.graph import get_driver

logger = logging.getLogger(__name__)

STATIONS = [
    {"station_id": "parque_central",  "name": "Parque Central",  "type": "bus_stop",      "latitude": -33.4560, "longitude": -70.6480},
    {"station_id": "plaza_armas",     "name": "Plaza de Armas",  "type": "bus_stop",      "latitude": -33.4510, "longitude": -70.6500},
    {"station_id": "mercado_central", "name": "Mercado Central", "type": "bus_stop",      "latitude": -33.4480, "longitude": -70.6550},
    {"station_id": "terminal",        "name": "Terminal",        "type": "bus_stop",      "latitude": -33.4420, "longitude": -70.6620},
    {"station_id": "estadio_nacional","name": "Estadio Nacional","type": "bus_stop",      "latitude": -33.4640, "longitude": -70.6420},
    {"station_id": "universidad",     "name": "Universidad",     "type": "bus_stop",      "latitude": -33.4470, "longitude": -70.6420},
    {"station_id": "estacion_norte",  "name": "Estacion Norte", "type": "metro_station", "latitude": -33.4380, "longitude": -70.6520},
    {"station_id": "estacion_centro", "name": "Estacion Centro","type": "metro_station", "latitude": -33.4490, "longitude": -70.6530},
    {"station_id": "estacion_sur",    "name": "Estacion Sur",   "type": "metro_station", "latitude": -33.4620, "longitude": -70.6580},
    {"station_id": "hub_centro",      "name": "Hub Centro",     "type": "scooter_hub",   "latitude": -33.4550, "longitude": -70.6470},
    {"station_id": "hub_norte",       "name": "Hub Norte",      "type": "scooter_hub",   "latitude": -33.4400, "longitude": -70.6550},
]

ROUTES = [
    # (from, to, mode, line, route_id, dist_m, time_sec, carbon_g)
    ("parque_central",  "plaza_armas",     "bus",  "B1", "B1", 1200, 300, 106.8),
    ("plaza_armas",     "mercado_central", "bus",  "B1", "B1",  900, 240,  80.1),
    ("mercado_central", "terminal",        "bus",  "B1", "B1", 1400, 360, 124.6),
    ("estadio_nacional","parque_central",  "bus",  "B2", "B2", 2000, 480, 178.0),
    ("parque_central",  "plaza_armas",     "bus",  "B2", "B2", 1200, 240, 106.8),
    ("plaza_armas",     "universidad",     "bus",  "B2", "B2", 1100, 300,  97.9),
    ("estacion_norte",  "estacion_centro", "metro","M1", "M1", 1500, 240,  42.0),
    ("estacion_centro", "estacion_sur",    "metro","M1", "M1", 1800, 300,  50.4),
]

TRANSFERS = [
    # (from, to, mode, dist_m, time_sec, carbon_g)
    ("plaza_armas",     "estacion_centro", "walk",   600, 480,  0.0),
    ("mercado_central", "estacion_centro", "walk",   200, 180,  0.0),
    ("parque_central",  "estacion_norte",  "walk",   800, 600,  0.0),
    ("terminal",        "estacion_sur",    "walk",   500, 420,  0.0),
    ("hub_centro",      "parque_central",  "scooter",100, 120,  2.2),
    ("hub_norte",       "estacion_norte",  "scooter",200, 180,  4.4),
]


async def seed_database():
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            "CREATE INDEX station_id_idx IF NOT EXISTS FOR (s:Station) ON (s.station_id)",
        )
        result = await session.run("MATCH (s:Station) RETURN count(s) AS count")
        row = await result.single()
        if row["count"] > 0:
            logger.info("Database already seeded — skipping")
            return
        logger.info("Seeding %d stations", len(STATIONS))
        for st in STATIONS:
            await session.run(
                "CREATE (s:Station {station_id: $station_id, name: $name, type: $type, latitude: $latitude, longitude: $longitude})",
                **st,
            )
        logger.info("Seeding %d route arcs (bidirectional)", len(ROUTES))
        for from_id, to_id, tmode, line, rid, dist_m, time_sec, carbon_g in ROUTES:
            for a, b in [(from_id, to_id), (to_id, from_id)]:
                await session.run(
                    """
                    MATCH (a:Station {station_id: $from_id}), (b:Station {station_id: $to_id})
                    CREATE (a)-[:CONNECTS_TO {
                        transport_mode: $transport_mode, line: $line, route_id: $route_id,
                        distance_meters: $distance_meters,
                        average_travel_time_sec: $average_travel_time_sec,
                        carbon_footprint_grams: $carbon_footprint_grams
                    }]->(b)
                    """,
                    from_id=a, to_id=b, transport_mode=tmode, line=line,
                    route_id=rid, distance_meters=dist_m,
                    average_travel_time_sec=time_sec, carbon_footprint_grams=carbon_g,
                )
        logger.info("Seeding %d transfer arcs (bidirectional)", len(TRANSFERS))
        for from_id, to_id, tmode, dist_m, time_sec, carbon_g in TRANSFERS:
            for a, b in [(from_id, to_id), (to_id, from_id)]:
                await session.run(
                    """
                    MATCH (a:Station {station_id: $from_id}), (b:Station {station_id: $to_id})
                    CREATE (a)-[:CONNECTS_TO {
                        transport_mode: $transport_mode,
                        distance_meters: $distance_meters,
                        average_travel_time_sec: $average_travel_time_sec,
                        carbon_footprint_grams: $carbon_footprint_grams
                    }]->(b)
                    """,
                    from_id=a, to_id=b, transport_mode=tmode,
                    distance_meters=dist_m, average_travel_time_sec=time_sec,
                    carbon_footprint_grams=carbon_g,
                )
        logger.info("Seed complete — %d stations, %d route arcs, %d transfers",
                     len(STATIONS), len(ROUTES), len(TRANSFERS))
