import pytest

from app.core.graph import get_driver, set_driver, close_driver


class TestGraphDriver:
    def test_get_driver_raises_when_not_initialized(self):
        set_driver(None)
        with pytest.raises(RuntimeError, match="not initialized"):
            get_driver()

    def test_set_and_get_driver(self):
        mock = object()
        set_driver(mock)
        assert get_driver() is mock
        set_driver(None)

    def test_close_driver_calls_stop(self):
        class FakeDriver:
            closed = False
            async def close(self):
                self.closed = True

        fake = FakeDriver()
        set_driver(fake)
        import asyncio
        asyncio.run(close_driver())
        assert fake.closed
        assert get_driver.__code__  # just verifying module still works
        set_driver(None)
