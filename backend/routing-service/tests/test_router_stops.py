from app.schemas.responses import StationInfo


def test_station_info_required_fields():
    obj = StationInfo(station_id="x", name="X", type="bus_stop")
    assert obj.station_id == "x"
    assert obj.name == "X"
    assert obj.type == "bus_stop"


def test_station_info_rejects_missing_type():
    from pydantic import ValidationError
    import pytest
    with pytest.raises(ValidationError):
        StationInfo(station_id="x", name="X")
