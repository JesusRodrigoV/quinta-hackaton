# Telemetry & Tracking Service

Microservicio FastAPI para recibir telemetria GPS de buses, persistirla en TimescaleDB y emitir eventos Kafka al topico `bus-location-updated`.

## Ejecutar localmente

```powershell
docker compose up -d timescaledb
cd backend/telemetry-tracking-service
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Kafka debe estar disponible en `localhost:9092`.

## Variables principales

El archivo `.env` real ya fue creado para desarrollo local:

```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_BUS_LOCATION_UPDATED=bus-location-updated
TIMESCALEDB_HOST=localhost
TIMESCALEDB_PORT=5433
TIMESCALEDB_USER=urbanflow_user
TIMESCALEDB_PASSWORD=dev_password_123
TIMESCALEDB_DATABASE=telemetry_db
```

## SQL de inicializacion

El script completo esta en `database/init.sql`. El comando exacto que convierte la tabla en hypertable es:

```sql
SELECT create_hypertable('bus_telemetry', 'timestamp', if_not_exists => TRUE);
```

## Payload

```json
{
  "bus_id": "BUS-102",
  "latitude": -16.4897,
  "longitude": -68.1193,
  "speed_kmh": 42.5,
  "timestamp": "2026-06-02T19:00:00Z"
}
```

## Endpoints

- `GET /health`: estado basico del proceso.
- `GET /ready`: valida conectividad a TimescaleDB y Kafka.
- `POST /api/v1/telemetry`: persiste telemetria y publica el evento.

## Robustez

- Pool async de TimescaleDB con `asyncpg`.
- Inicializacion idempotente de esquema.
- Outbox transaccional para no perder eventos si Kafka falla.
- Reintento en background de eventos pendientes.
- Productor Kafka idempotente con confirmacion de entrega.
- Manejo consistente de errores HTTP.
