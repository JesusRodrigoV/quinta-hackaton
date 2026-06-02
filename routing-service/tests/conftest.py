import pytest

from app.schemas.responses import RouteOption, RouteResponse, Segment, StationInfo

@pytest.fixture
def sample_segment():
    return Segment(
        from_station=StationInfo(station_id="a", name="A", type="bus_stop"),
        to_station=StationInfo(station_id="b", name="B", type="bus_stop"),
        transport_mode="bus",
        line="X1",
        travel_time_min=5.0,
        distance_km=2.0,
    )

@pytest.fixture
def sample_route_response():
    seg = Segment(
        from_station=StationInfo(station_id="a", name="A", type="bus_stop"),
        to_station=StationInfo(station_id="b", name="B", type="bus_stop"),
        transport_mode="bus",
        line="X1",
        travel_time_min=5.0,
        distance_km=2.0,
    )
    return RouteResponse(
        route_id="test-123",
        options=[
            RouteOption(
                total_time_min=5.0,
                total_cost=0.70,
                total_co2_kg=0.178,
                segments=[seg],
            ),
        ],
    )
