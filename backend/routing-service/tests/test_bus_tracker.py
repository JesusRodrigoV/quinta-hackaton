import asyncio
import json

from app.core.bus_tracker import start, stop, get_positions, get_bus_position


class TestBusTrackerNoBroker:
    def test_start_without_broker_is_noop(self):
        asyncio.run(start())
        assert get_positions() == []
        asyncio.run(stop())

    def test_stop_without_start_is_noop(self):
        asyncio.run(stop())

    def test_get_positions_empty_initially(self):
        assert get_positions() == []

    def test_get_bus_position_unknown(self):
        assert get_bus_position("BUS-999") is None


class TestBusTrackerWithPosition:
    def test_get_positions_returns_stored(self):
        from app.core.bus_tracker import _positions
        _positions.clear()
        _positions["BUS-001"] = {
            "bus_id": "BUS-001",
            "latitude": -33.456,
            "longitude": -70.648,
            "speed_kmh": 30.0,
            "timestamp": "2026-06-02T19:00:00+00:00",
            "last_seen": "2026-06-02T19:00:01+00:00",
        }
        assert len(get_positions()) == 1
        assert get_positions()[0]["bus_id"] == "BUS-001"

    def test_get_bus_position_known(self):
        from app.core.bus_tracker import _positions
        _positions.clear()
        _positions["BUS-001"] = {"bus_id": "BUS-001", "latitude": -33.456}
        pos = get_bus_position("BUS-001")
        assert pos is not None
        assert pos["bus_id"] == "BUS-001"
        assert get_bus_position("BUS-XXX") is None
        _positions.clear()


class TestBusTrackerMessageHandling:
    def test_valid_message_stores_position(self):
        from app.core.bus_tracker import _positions, _handle_message
        _positions.clear()
        msg = type("Msg", (), {
            "topic": "bus-location-updated",
            "value": json.dumps({
                "bus_id": "BUS-042",
                "latitude": -33.45,
                "longitude": -70.65,
                "speed_kmh": 42.5,
                "timestamp": "2026-06-02T19:00:00+00:00",
            }).encode(),
        })()
        _handle_message(msg)
        assert "BUS-042" in _positions
        assert _positions["BUS-042"]["latitude"] == -33.45
        assert _positions["BUS-042"]["speed_kmh"] == 42.5
        _positions.clear()

    def test_invalid_json_does_not_crash(self):
        from app.core.bus_tracker import _positions, _handle_message
        _positions.clear()
        msg = type("Msg", (), {
            "topic": "bus-location-updated",
            "value": b"not-json",
        })()
        _handle_message(msg)
        assert len(get_positions()) == 0

    def test_message_without_bus_id_skipped(self):
        from app.core.bus_tracker import _positions, _handle_message
        _positions.clear()
        msg = type("Msg", (), {
            "topic": "bus-location-updated",
            "value": json.dumps({"latitude": -33.45}).encode(),
        })()
        _handle_message(msg)
        assert len(get_positions()) == 0

    def test_message_updates_existing_bus(self):
        from app.core.bus_tracker import _positions, _handle_message
        _positions.clear()
        _positions["BUS-001"] = {"bus_id": "BUS-001", "latitude": -33.0}
        msg = type("Msg", (), {
            "topic": "bus-location-updated",
            "value": json.dumps({
                "bus_id": "BUS-001",
                "latitude": -34.0,
                "longitude": -71.0,
                "speed_kmh": 10.0,
                "timestamp": "2026-06-02T20:00:00+00:00",
            }).encode(),
        })()
        _handle_message(msg)
        assert _positions["BUS-001"]["latitude"] == -34.0
        assert _positions["BUS-001"]["longitude"] == -71.0
        _positions.clear()
