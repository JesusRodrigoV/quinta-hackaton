import asyncio

from app.core.kafka import publish, set_producer, init_kafka, close_kafka


class TestKafkaNoBroker:
    def test_publish_without_producer_is_noop(self):
        set_producer(None)
        asyncio.run(publish("test", "key", {"value": 1}))

    def test_init_kafka_no_broker_returns_early(self):
        asyncio.run(init_kafka())

    def test_set_and_get_producer(self):
        mock = object()
        set_producer(mock)
        from app.core.kafka import _producer
        assert _producer is mock
        set_producer(None)

    def test_close_kafka_without_producer_is_noop(self):
        set_producer(None)
        asyncio.run(close_kafka())


class TestKafkaWithMock:
    def test_publish_with_mock_producer(self):
        mock = type("FakeProducer", (), {
            "stop": lambda self: None,
            "send": lambda self, topic, key=None, value=None: asyncio.sleep(0),
        })()
        set_producer(mock)
        asyncio.run(publish("t", "k", {"v": 1}))
        set_producer(None)
