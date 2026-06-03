"""
Integration tests against a real Neo4j instance.

Skipped automatically unless NEO4J_TEST_URI env var is set.
Usage:
    NEO4J_TEST_URI=bolt://localhost:7687 pytest tests/test_integration.py -v
"""
import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("NEO4J_TEST_URI"),
    reason="Set NEO4J_TEST_URI env var to run integration tests",
)


@pytest.fixture(scope="module")
def driver():
    from neo4j import AsyncGraphDatabase
    from app.core.graph import set_driver

    uri = os.environ["NEO4J_TEST_URI"]
    user = os.getenv("NEO4J_TEST_USER", "neo4j")
    password = os.getenv("NEO4J_TEST_PASSWORD", "password")

    d = AsyncGraphDatabase.driver(uri, auth=(user, password))
    set_driver(d)
    yield d
    set_driver(None)


@pytest.fixture(scope="module")
async def seeded_db(driver):
    from app.seed.loader import seed_database
    await seed_database()
    yield


class TestEndToEnd:
    async def test_nearest_stations_finds_parque_central(self, seeded_db):
        from app.services.route_planner import _nearest_stations
        stations = await _nearest_stations(-33.456, -70.648)
        assert len(stations) >= 1
        assert stations[0]["s"]["station_id"] == "parque_central"

    async def test_nearest_stations_returns_closest_first(self, seeded_db):
        from app.services.route_planner import _nearest_stations
        stations = await _nearest_stations(-33.442, -70.662)
        assert stations[0]["s"]["station_id"] == "terminal"

    async def test_path_parque_central_to_terminal(self, seeded_db):
        from app.services.route_planner import _paths_between
        paths = await _paths_between("parque_central", "terminal", ["bus"])
        assert len(paths) >= 1
        first = paths[0]
        assert first["total_sec"] > 0

    async def test_full_route_planning(self, seeded_db):
        from app.services.route_planner import plan_route
        from app.models.requests import RouteRequest
        req = RouteRequest(
            origin_lat=-33.456, origin_lon=-70.648,
            dest_lat=-33.442, dest_lon=-70.662,
            modes=["bus", "metro"],
            preference="time",
        )
        result = await plan_route(req)
        assert len(result.options) >= 1
        opt = result.options[0]
        assert opt.total_time_min > 0
        assert opt.total_cost >= 0
        assert len(opt.segments) >= 1

    async def test_save_and_retrieve_cached_route(self, seeded_db):
        from app.schemas.responses import RouteResponse, RouteOption, Segment, StationInfo
        from app.services.route_planner import save_route, get_cached_route
        seg = Segment(
            from_station=StationInfo(station_id="a", name="A", type="bus_stop"),
            to_station=StationInfo(station_id="b", name="B", type="bus_stop"),
            transport_mode="bus", line="B1",
            travel_time_min=5.0, distance_km=2.0,
        )
        opt = RouteOption(total_time_min=5.0, total_cost=0.70, total_co2_kg=0.107, segments=[seg])
        resp = RouteResponse(route_id="int-test", options=[opt])
        await save_route("int-test", resp)
        loaded = await get_cached_route("int-test")
        assert loaded is not None
        assert loaded.route_id == "int-test"
        assert loaded.options[0].total_cost == 0.70

    async def test_no_cyclic_paths_in_results(self, seeded_db):
        """
        Verifies that _paths_between never returns paths with repeated stations.
        """
        from app.services.route_planner import _paths_between
        paths = await _paths_between("parque_central", "terminal", ["bus", "metro", "walk"])
        for p in paths:
            ns = p["p"].nodes
            ids = [n["station_id"] for n in ns]
            assert len(ids) == len(set(ids)), f"Cyclic path detected: {ids}"
