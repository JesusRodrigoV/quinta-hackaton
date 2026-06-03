from app.schemas.responses import Segment, StationInfo
from app.services.route_planner import _segment_cost


def _make_seg(transport_mode: str = "bus", travel_time_min: float = 5) -> Segment:
    return Segment(
        from_station=StationInfo(station_id="a", name="A", type="bus_stop"),
        to_station=StationInfo(station_id="b", name="B", type="bus_stop"),
        transport_mode=transport_mode,
        line="X1",
        travel_time_min=travel_time_min,
        distance_km=2.0,
    )


class TestSegmentCost:
    def test_bus_flat_rate(self):
        assert _segment_cost(_make_seg("bus")) == 0.70

    def test_metro_flat_rate(self):
        assert _segment_cost(_make_seg("metro")) == 0.80

    def test_walk_is_free(self):
        assert _segment_cost(_make_seg("walk")) == 0.0

    def test_scooter_per_minute(self):
        assert _segment_cost(_make_seg("scooter", travel_time_min=10)) == 1.50
