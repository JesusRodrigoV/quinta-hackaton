import pytest
from pydantic import ValidationError

from app.models.route import Station, Connection
from app.schemas.responses import StationInfo, Segment, RouteOption, RouteResponse


class TestStationModel:
    def test_valid_types(self):
        for t in ("bus_stop", "metro_station", "scooter_hub"):
            s = Station(station_id="x", name="X", type=t, latitude=0.0, longitude=0.0)
            assert s.type == t

    def test_invalid_type_raises(self):
        with pytest.raises(ValidationError):
            Station(station_id="x", name="X", type="helipuerto", latitude=0.0, longitude=0.0)


class TestConnectionModel:
    def test_minimal_connection(self):
        c = Connection(
            from_station_id="a", to_station_id="b",
            transport_mode="bus", distance_meters=1000,
            average_travel_time_sec=120, carbon_footprint_grams=50.0,
        )
        assert c.line is None
        assert c.route_id is None

    def test_full_connection(self):
        c = Connection(
            from_station_id="a", to_station_id="b",
            transport_mode="bus", line="B1", route_id="B1",
            distance_meters=1000, average_travel_time_sec=120,
            carbon_footprint_grams=50.0,
        )
        assert c.line == "B1"


class TestResponseModels:
    def test_station_info_all_types(self):
        for t in ("bus_stop", "metro_station", "scooter_hub"):
            si = StationInfo(station_id="x", name="X", type=t)
            assert si.type == t

    def test_segment_construction(self):
        si_a = StationInfo(station_id="a", name="A", type="bus_stop")
        si_b = StationInfo(station_id="b", name="B", type="bus_stop")
        seg = Segment(
            from_station=si_a, to_station=si_b,
            transport_mode="bus", line="X1",
            travel_time_min=5.0, distance_km=2.0,
        )
        assert seg.transport_mode == "bus"

    def test_route_option_construction(self):
        opt = RouteOption(total_time_min=10.0, total_cost=1.50, total_co2_kg=0.2, segments=[])
        assert opt.total_cost == 1.50

    def test_route_response_without_id(self):
        resp = RouteResponse(options=[])
        assert resp.route_id is None

    def test_route_response_with_id(self):
        resp = RouteResponse(route_id="abc", options=[])
        assert resp.route_id == "abc"

    def test_route_response_roundtrip(self):
        si_a = StationInfo(station_id="a", name="A", type="bus_stop")
        si_b = StationInfo(station_id="b", name="B", type="bus_stop")
        seg = Segment(
            from_station=si_a, to_station=si_b,
            transport_mode="bus", line="X1",
            travel_time_min=5.0, distance_km=2.0,
        )
        opt = RouteOption(total_time_min=5.0, total_cost=0.70, total_co2_kg=0.107, segments=[seg])
        original = RouteResponse(route_id="r1", options=[opt])
        raw = original.model_dump_json()
        restored = RouteResponse.model_validate_json(raw)
        assert restored.route_id == "r1"
        assert restored.options[0].total_time_min == 5.0
