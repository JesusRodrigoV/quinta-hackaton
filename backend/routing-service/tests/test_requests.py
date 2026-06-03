import pytest
from pydantic import ValidationError

from app.models.requests import RouteRequest


class TestRouteRequestValidation:
    def test_valid_request(self):
        req = RouteRequest(
            origin_lat=-33.456, origin_lon=-70.648,
            dest_lat=-33.442, dest_lon=-70.662,
            modes=["bus", "metro"],
            preference="co2",
        )
        assert req.origin_lat == -33.456
        assert req.preference == "co2"

    def test_default_modes(self):
        req = RouteRequest(
            origin_lat=-33.45, origin_lon=-70.65,
            dest_lat=-33.44, dest_lon=-70.66,
        )
        assert req.modes == ["bus", "metro", "walk", "scooter"]

    def test_default_preference(self):
        req = RouteRequest(
            origin_lat=-33.45, origin_lon=-70.65,
            dest_lat=-33.44, dest_lon=-70.66,
        )
        assert req.preference == "time"

    def test_empty_modes_list(self):
        req = RouteRequest(
            origin_lat=-33.45, origin_lon=-70.65,
            dest_lat=-33.44, dest_lon=-70.66,
            modes=[],
        )
        assert req.modes == []

    def test_invalid_mode_raises(self):
        with pytest.raises(ValidationError):
            RouteRequest(
                origin_lat=0, origin_lon=0,
                dest_lat=1, dest_lon=1,
                modes=["avion"],
            )

    def test_invalid_preference_raises(self):
        with pytest.raises(ValidationError):
            RouteRequest(
                origin_lat=0, origin_lon=0,
                dest_lat=1, dest_lon=1,
                preference="altura",
            )

    def test_same_point_raises(self):
        with pytest.raises(ValidationError):
            RouteRequest(
                origin_lat=-33.456, origin_lon=-70.648,
                dest_lat=-33.4561, dest_lon=-70.6481,
            )

    def test_different_points_passes(self):
        req = RouteRequest(
            origin_lat=-33.456, origin_lon=-70.648,
            dest_lat=-33.442, dest_lon=-70.662,
        )
        assert req is not None

    def test_lat_out_of_bounds_raises(self):
        with pytest.raises(ValidationError):
            RouteRequest(
                origin_lat=100, origin_lon=0,
                dest_lat=0, dest_lon=0,
            )

    def test_lon_out_of_bounds_raises(self):
        with pytest.raises(ValidationError):
            RouteRequest(
                origin_lat=0, origin_lon=200,
                dest_lat=0, dest_lon=0,
            )

    def test_tokyo_coords_rejected_by_santiago_bbox(self):
        with pytest.raises(ValidationError, match="fuera del área"):
            RouteRequest(
                origin_lat=35.676, origin_lon=139.650,
                dest_lat=35.682, dest_lon=139.660,
            )

    def test_near_santiago_limit_passes(self):
        req = RouteRequest(
            origin_lat=-33.44, origin_lon=-70.65,
            dest_lat=-33.45, dest_lon=-70.66,
        )
        assert req is not None

    def test_exactly_at_bbox_boundary_ok(self):
        RouteRequest(
            origin_lat=-33.47, origin_lon=-70.67,
            dest_lat=-33.43, dest_lon=-70.64,
        )

    def test_just_outside_bbox_raises(self):
        with pytest.raises(ValidationError, match="fuera del área"):
            RouteRequest(
                origin_lat=-33.471, origin_lon=-70.650,
                dest_lat=-33.450, dest_lon=-70.660,
            )
