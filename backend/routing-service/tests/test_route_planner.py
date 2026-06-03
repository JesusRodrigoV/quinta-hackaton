from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.responses import Segment, StationInfo, RouteOption, RouteResponse
from app.services.route_planner import _segment_cost

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_seg(transport_mode: str = "bus", travel_time_min: float = 5) -> Segment:
    return Segment(
        from_station=StationInfo(station_id="a", name="A", type="bus_stop"),
        to_station=StationInfo(station_id="b", name="B", type="bus_stop"),
        transport_mode=transport_mode,
        line="X1",
        travel_time_min=travel_time_min,
        distance_km=2.0,
    )


# ---------------------------------------------------------------------------
# Mock Neo4j graph objects for _build_option
# ---------------------------------------------------------------------------

class _MockNode:
    def __init__(self, station_id, name, type_):
        self._data = {"station_id": station_id, "name": name, "type": type_}
    def __getitem__(self, key):
        return self._data[key]


class _MockRel:
    def __init__(self, start_node, end_node, **props):
        self.start_node = start_node
        self.end_node = end_node
        self._props = props
    def __getitem__(self, key):
        return self._props[key]
    def get(self, key, default=None):
        return self._props.get(key, default)


class _MockPath:
    def __init__(self, relationships):
        self.relationships = relationships


# ===================================================================
# _segment_cost
# ===================================================================

class TestSegmentCost:
    def test_bus_flat_rate(self):
        assert _segment_cost(_make_seg("bus")) == 0.70

    def test_metro_flat_rate(self):
        assert _segment_cost(_make_seg("metro")) == 0.80

    def test_walk_is_free(self):
        assert _segment_cost(_make_seg("walk")) == 0.0

    def test_scooter_per_minute(self):
        assert _segment_cost(_make_seg("scooter", travel_time_min=10)) == 1.50

    def test_unknown_mode_defaults_to_zero(self):
        assert _segment_cost(_make_seg("train")) == 0.0

    def test_scooter_zero_minutes_is_free(self):
        assert _segment_cost(_make_seg("scooter", travel_time_min=0)) == 0.0

    def test_scooter_rounding(self):
        assert _segment_cost(_make_seg("scooter", travel_time_min=1)) == 0.15
        assert _segment_cost(_make_seg("scooter", travel_time_min=1.5)) == 0.22


# ===================================================================
# _build_option
# ===================================================================

class TestBuildOption:
    def test_single_segment_with_line(self):
        from app.services.route_planner import _build_option
        a = _MockNode("a", "Station A", "bus_stop")
        b = _MockNode("b", "Station B", "bus_stop")
        rel = _MockRel(a, b, transport_mode="bus", line="B1",
                       average_travel_time_sec=300, distance_meters=1200,
                       carbon_footprint_grams=106.8)
        path = _MockPath([rel])
        opt = _build_option({"p": path})
        assert opt.total_time_min == 5.0
        assert opt.total_cost == 0.70
        assert opt.total_co2_kg == 0.107
        assert len(opt.segments) == 1
        assert opt.segments[0].line == "B1"
        assert opt.segments[0].from_station.station_id == "a"
        assert opt.segments[0].to_station.station_id == "b"

    def test_transfer_segment_without_line(self):
        from app.services.route_planner import _build_option
        a = _MockNode("a", "Station A", "bus_stop")
        b = _MockNode("b", "Station B", "metro_station")
        rel = _MockRel(a, b, transport_mode="walk",
                       average_travel_time_sec=480, distance_meters=600)
        path = _MockPath([rel])
        opt = _build_option({"p": path})
        assert opt.total_time_min == 8.0
        assert opt.total_cost == 0.0
        assert opt.total_co2_kg == 0.0
        assert opt.segments[0].line is None

    def test_multi_segment_path(self):
        from app.services.route_planner import _build_option
        a = _MockNode("a", "A", "bus_stop")
        b = _MockNode("b", "B", "bus_stop")
        c = _MockNode("c", "C", "bus_stop")
        r1 = _MockRel(a, b, transport_mode="bus", line="B1",
                       average_travel_time_sec=300, distance_meters=1200,
                       carbon_footprint_grams=106.8)
        r2 = _MockRel(b, c, transport_mode="bus", line="B1",
                       average_travel_time_sec=240, distance_meters=900,
                       carbon_footprint_grams=80.1)
        path = _MockPath([r1, r2])
        opt = _build_option({"p": path})
        assert opt.total_time_min == 9.0
        assert opt.total_cost == 1.40
        assert opt.total_co2_kg == 0.187
        assert len(opt.segments) == 2

    def test_missing_carbon_is_zero(self):
        from app.services.route_planner import _build_option
        a = _MockNode("a", "A", "bus_stop")
        b = _MockNode("b", "B", "bus_stop")
        rel = _MockRel(a, b, transport_mode="walk",
                       average_travel_time_sec=180, distance_meters=200)
        path = _MockPath([rel])
        opt = _build_option({"p": path})
        assert opt.total_co2_kg == 0.0

    def test_cyclic_path_does_not_crash(self):
        from app.services.route_planner import _build_option
        a = _MockNode("a", "A", "bus_stop")
        b = _MockNode("b", "B", "bus_stop")
        c = _MockNode("c", "C", "bus_stop")
        # Cyclic: a → b → a → c (vuelve a a antes de ir a c)
        r1 = _MockRel(a, b, transport_mode="bus", line="B1",
                       average_travel_time_sec=300, distance_meters=1200,
                       carbon_footprint_grams=106.8)
        r2 = _MockRel(b, a, transport_mode="bus", line="B1",
                       average_travel_time_sec=300, distance_meters=1200,
                       carbon_footprint_grams=106.8)
        r3 = _MockRel(a, c, transport_mode="bus", line="B1",
                       average_travel_time_sec=240, distance_meters=900,
                       carbon_footprint_grams=80.1)
        path = _MockPath([r1, r2, r3])
        opt = _build_option({"p": path})
        assert len(opt.segments) == 3
        assert opt.segments[0].from_station.station_id == "a"
        assert opt.segments[2].to_station.station_id == "c"


# ===================================================================
# plan_route (dedup + sort + limit + kafka)
# ===================================================================

class TestPlanRoute:
    @patch("app.services.route_planner._paths_between")
    @patch("app.services.route_planner._nearest_stations")
    async def test_dedup_identical_paths(self, mock_nearest, mock_paths):
        from app.services.route_planner import plan_route
        from app.models.requests import RouteRequest

        mock_nearest.side_effect = [
            [{"s": {"station_id": "a", "name": "A", "type": "bus_stop"}, "dist": 0}],
            [{"s": {"station_id": "b", "name": "B", "type": "bus_stop"}, "dist": 0}],
        ]
        a = _MockNode("a", "A", "bus_stop")
        b = _MockNode("b", "B", "bus_stop")
        rel = _MockRel(a, b, transport_mode="bus", line="B1",
                       average_travel_time_sec=300, distance_meters=1200,
                       carbon_footprint_grams=106.8)
        path_obj = _MockPath([rel])
        mock_paths.return_value = [{"p": path_obj}, {"p": path_obj}]

        req = RouteRequest(origin_lat=-33.45, origin_lon=-70.65, dest_lat=-33.44, dest_lon=-70.66, modes=["bus"])
        result = await plan_route(req)
        assert len(result.options) == 1

    @patch("app.services.route_planner._paths_between")
    @patch("app.services.route_planner._nearest_stations")
    async def test_two_different_paths_both_returned(self, mock_nearest, mock_paths):
        from app.services.route_planner import plan_route
        from app.models.requests import RouteRequest

        mock_nearest.side_effect = [
            [{"s": {"station_id": "a", "name": "A", "type": "bus_stop"}, "dist": 0}],
            [{"s": {"station_id": "b", "name": "B", "type": "bus_stop"}, "dist": 0}],
        ]
        a = _MockNode("a", "A", "bus_stop")
        b = _MockNode("b", "B", "bus_stop")
        c = _MockNode("c", "C", "bus_stop")
        rel1 = _MockRel(a, b, transport_mode="bus", line="B1",
                        average_travel_time_sec=300, distance_meters=1200,
                        carbon_footprint_grams=106.8)
        # Path A→B and A→C→B (different signatures)
        rel2a = _MockRel(a, c, transport_mode="bus", line="B1",
                         average_travel_time_sec=240, distance_meters=900,
                         carbon_footprint_grams=80.1)
        rel2b = _MockRel(c, b, transport_mode="bus", line="B1",
                         average_travel_time_sec=300, distance_meters=1200,
                         carbon_footprint_grams=106.8)
        mock_paths.return_value = [
            {"p": _MockPath([rel1])},
            {"p": _MockPath([rel2a, rel2b])},
        ]

        req = RouteRequest(origin_lat=-33.45, origin_lon=-70.65, dest_lat=-33.44, dest_lon=-70.66, modes=["bus"])
        result = await plan_route(req)
        assert len(result.options) == 2

    @patch("app.services.route_planner._paths_between")
    @patch("app.services.route_planner._nearest_stations")
    async def test_sort_by_time(self, mock_nearest, mock_paths):
        from app.services.route_planner import plan_route
        from app.models.requests import RouteRequest

        # 2 origin × 2 dest = 4 combos; 2 have paths, 2 are empty
        mock_nearest.side_effect = [
            [{"s": {"station_id": "a1", "name": "A1", "type": "bus_stop"}, "dist": 0},
             {"s": {"station_id": "a2", "name": "A2", "type": "bus_stop"}, "dist": 0}],
            [{"s": {"station_id": "b1", "name": "B1", "type": "bus_stop"}, "dist": 0},
             {"s": {"station_id": "b2", "name": "B2", "type": "bus_stop"}, "dist": 0}],
        ]
        r1 = _MockRel(_MockNode("a1", "A1", "bus_stop"), _MockNode("b1", "B1", "bus_stop"),
                       transport_mode="bus", line="B1",
                       average_travel_time_sec=600, distance_meters=1200,
                       carbon_footprint_grams=106.8)
        r2 = _MockRel(_MockNode("a2", "A2", "bus_stop"), _MockNode("b2", "B2", "bus_stop"),
                       transport_mode="metro", line="M1",
                       average_travel_time_sec=120, distance_meters=1500,
                       carbon_footprint_grams=42.0)
        # 4 calls to _paths_between (2 origins × 2 destinations)
        mock_paths.side_effect = [
            [{"p": _MockPath([r1])}],
            [],
            [],
            [{"p": _MockPath([r2])}],
        ]

        req = RouteRequest(origin_lat=-33.45, origin_lon=-70.65, dest_lat=-33.44, dest_lon=-70.66,
                           modes=["bus", "metro"], preference="time")
        result = await plan_route(req)
        assert len(result.options) == 2
        assert result.options[0].total_time_min <= result.options[1].total_time_min

    @patch("app.services.route_planner._paths_between")
    @patch("app.services.route_planner._nearest_stations")
    async def test_top_5_limit(self, mock_nearest, mock_paths):
        from app.services.route_planner import plan_route
        from app.models.requests import RouteRequest

        # Return 3 origin and 3 dest stations → 9 pairs → up to 27 paths
        stations_o = [{"s": {"station_id": f"o{i}", "name": f"O{i}", "type": "bus_stop"}, "dist": 0} for i in range(3)]
        stations_d = [{"s": {"station_id": f"d{i}", "name": f"D{i}", "type": "bus_stop"}, "dist": 0} for i in range(3)]
        mock_nearest.side_effect = [stations_o, stations_d]

        a = _MockNode("a", "A", "bus_stop")
        b = _MockNode("b", "B", "bus_stop")
        rel = _MockRel(a, b, transport_mode="bus", line="B1",
                       average_travel_time_sec=300, distance_meters=1200,
                       carbon_footprint_grams=106.8)
        # Different station_ids in signature to avoid dedup collapse
        mock_paths.side_effect = [
            [{"p": _MockPath([_MockRel(
                _MockNode(f"o{x[0]}", "A", "bus_stop"),
                _MockNode(f"d{x[1]}", "B", "bus_stop"),
                transport_mode="bus", line="B1",
                average_travel_time_sec=300, distance_meters=1200,
                carbon_footprint_grams=106.8)])}]
            for x in [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)]
        ]

        req = RouteRequest(origin_lat=-33.45, origin_lon=-70.65, dest_lat=-33.44, dest_lon=-70.66, modes=["bus"])
        result = await plan_route(req)
        assert len(result.options) <= 5

    @patch("app.services.route_planner._paths_between")
    @patch("app.services.route_planner._nearest_stations")
    async def test_no_nearby_stations_returns_404(self, mock_nearest, mock_paths):
        from app.services.route_planner import plan_route
        from app.models.requests import RouteRequest
        from fastapi import HTTPException

        mock_nearest.side_effect = [[], [{"s": {"station_id": "b", "name": "B", "type": "bus_stop"}, "dist": 0}]]

        req = RouteRequest(origin_lat=-33.45, origin_lon=-70.65, dest_lat=-33.44, dest_lon=-70.66, modes=["bus"])
        try:
            await plan_route(req)
            assert False, "Should have raised"
        except HTTPException as e:
            assert e.status_code == 404


# ===================================================================
# save_route / get_cached_route / cleanup_expired_routes
# ===================================================================

class TestRoutePersistence:
    def _make_mock_driver(self, mock_result=None):
        mock_session = MagicMock()
        mock_session.run = AsyncMock(return_value=mock_result)
        mock_driver = MagicMock()
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        return mock_driver, mock_session

    async def test_save_route_calls_cypher(self):
        from app.services.route_planner import save_route
        from app.core.graph import set_driver

        mock_driver, mock_session = self._make_mock_driver()
        set_driver(mock_driver)

        try:
            response = RouteResponse(options=[])
            await save_route("test-id", response)
            mock_session.run.assert_awaited_once()
            call_kwargs = mock_session.run.call_args[1]
            assert call_kwargs["route_id"] == "test-id"
            assert "route_id" in call_kwargs["response_json"]
        finally:
            set_driver(None)

    async def test_get_cached_route_returns_none_when_missing(self):
        from app.services.route_planner import get_cached_route
        from app.core.graph import set_driver

        mock_result = MagicMock()
        mock_result.single = AsyncMock(return_value=None)
        mock_driver, mock_session = self._make_mock_driver(mock_result)
        set_driver(mock_driver)

        try:
            result = await get_cached_route("missing-id")
            assert result is None
        finally:
            set_driver(None)

    async def test_get_cached_route_returns_route(self):
        from app.services.route_planner import get_cached_route
        from app.core.graph import set_driver

        response_payload = '{"route_id":"abc","options":[]}'
        record = {"r": {"response_json": response_payload}}
        mock_result = MagicMock()
        mock_result.single = AsyncMock(return_value=record)
        mock_driver, mock_session = self._make_mock_driver(mock_result)
        set_driver(mock_driver)

        try:
            result = await get_cached_route("abc")
            assert result is not None
            assert result.route_id == "abc"
        finally:
            set_driver(None)

    async def test_cleanup_expired_runs_query(self):
        from app.services.route_planner import cleanup_expired_routes
        from app.core.graph import set_driver

        mock_row = {"deleted": 2}
        mock_result = MagicMock()
        mock_result.single = AsyncMock(return_value=mock_row)
        mock_driver, mock_session = self._make_mock_driver(mock_result)
        set_driver(mock_driver)

        try:
            await cleanup_expired_routes()
            mock_session.run.assert_awaited_once()
            assert "DELETE r" in mock_session.run.call_args[0][0]
        finally:
            set_driver(None)
