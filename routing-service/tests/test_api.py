from unittest.mock import MagicMock, AsyncMock

from app.core.graph import set_driver


# ===================================================================
# Health endpoint (tested directly via route handler)
# ===================================================================

class TestHealthEndpoint:
    async def test_health_healthy(self):
        from app.routers.stops import health
        mock_session = MagicMock()
        mock_session.run = AsyncMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        set_driver(mock_driver)
        try:
            result = await health()
            assert result["status"] == "healthy"
        finally:
            set_driver(None)

    async def test_health_missing_driver(self):
        from app.routers.stops import health
        set_driver(None)
        result = await health()
        assert hasattr(result, "status_code")
        assert result.status_code == 503

    async def test_health_db_failure(self):
        from app.routers.stops import health
        mock_session = MagicMock()
        mock_session.run = AsyncMock(side_effect=Exception("DB connection lost"))
        mock_driver = MagicMock()
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        set_driver(mock_driver)
        try:
            result = await health()
            assert result.status_code == 503
        finally:
            set_driver(None)


# ===================================================================
# Stops endpoint (tested directly via route handler)
# ===================================================================

class TestStopsEndpoint:
    async def test_list_stops_with_data(self):
        from app.routers.stops import list_stops
        mock_result = MagicMock()
        mock_result.data = AsyncMock(return_value=[
            {"s": {"station_id": "a", "name": "A", "type": "bus_stop"}},
            {"s": {"station_id": "b", "name": "B", "type": "metro_station"}},
        ])
        mock_session = MagicMock()
        mock_session.run = AsyncMock(return_value=mock_result)
        mock_driver = MagicMock()
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        set_driver(mock_driver)
        try:
            result = await list_stops()
            assert len(result["stops"]) == 2
            assert result["stops"][0].station_id == "a"
            assert result["stops"][1].station_id == "b"
        finally:
            set_driver(None)

    async def test_list_stops_empty(self):
        from app.routers.stops import list_stops
        mock_result = MagicMock()
        mock_result.data = AsyncMock(return_value=[])
        mock_session = MagicMock()
        mock_session.run = AsyncMock(return_value=mock_result)
        mock_driver = MagicMock()
        mock_driver.session.return_value.__aenter__.return_value = mock_session
        set_driver(mock_driver)
        try:
            result = await list_stops()
            assert result["stops"] == []
        finally:
            set_driver(None)
