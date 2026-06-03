import json
from aiokafka import AIOKafkaProducer
import asyncio

async def send_test_event():
    producer = AIOKafkaProducer(bootstrap_servers='localhost:9092')
    await producer.start()
    test_msg = {
        "bus_id": "TEST-BUS-001",
        "route_id": "R-101",
        "latitude": -16.5,
        "longitude": -68.1,
        "speed": 5.0, # Velocidad baja para forzar la detección de anomalía
        "timestamp": "2026-06-02T21:00:00"
    }
    await producer.send_and_wait("traffic.telemetry-gps", json.dumps(test_msg).encode('utf-8'))
    await producer.stop()
    print("✅ Evento de prueba enviado a Kafka.")

asyncio.run(send_test_event())