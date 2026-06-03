# Traffic Light Control Service

Microservicio que traduce eventos de retrasos de buses y congestión (desde Kafka) a comandos NTCIP para semáforos. Mantiene estado en tiempo real en Redis y auditoría inmutable en PostgreSQL.

## Responsabilidades

- Consumir eventos `tracking.bus.delayed` y `congestion.alert.created` desde Kafka.
- Traducir eventos a comandos NTCIP (máx 256 bytes) para semáforos.
- Mantener estado actual de semáforos en Redis (latencia <1ms).
- Registrar todos los cambios en PostgreSQL para auditoría regulatoria.
- Re-enrutamiento de buses en <10 segundos desde detección de anomalía.

## Ejecutar localmente

```powershell
docker compose up -d --build
```

La API estará disponible en `http://localhost:8001`.

Para ver logs:

```powershell
docker compose logs -f traffic-light-service
```

Para detener todo:

```powershell
docker compose down
```

## Ejecutar solo la app fuera de Docker

```powershell
docker compose up -d redis postgres kafka kafka-init
cd backend/traffic-light-service
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Redis estará en `localhost:6379`, PostgreSQL en `localhost:5432`, Kafka en `localhost:9092`.

## Variables principales

El archivo `.env` debe contener:

```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_GROUP_ID=traffic-light-service
KAFKA_TOPIC_BUS_DELAYED=tracking.bus.delayed
KAFKA_TOPIC_CONGESTION_ALERT=congestion.alert.created

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=urbanflow_user
POSTGRES_PASSWORD=dev_password_123
POSTGRES_DATABASE=audit_db

NTCIP_MAX_PAYLOAD_BYTES=256
NTCIP_REROUTE_TIMEOUT_SEC=10
```

## Flujo de procesamiento

1. **Evento de Bus Retrasado**: `tracking.bus.delayed` (bus_id, route_id, delay_minutes, corridor, lat/lon, timestamp)
   - Extrae `intersection_id` del corridor.
   - Calcula duración en segundos: `min(delay_minutes * 10, 120)`.
   - Traduce a comando NTCIP: `ACTIVATE_PRIORITY|{intersection_id}|green|high|{duration}`.
   - Actualiza estado en Redis: `traffic_light:{intersection_id}` con estado GREEN y `priority_override_active=true`.
   - Registra en PostgreSQL: evento `signal_priority_applied` con status success/failure.

2. **Evento de Congestión**: `congestion.alert.created` (corridor_id, severity 1-5, predicted_delay_minutes, timestamp)
   - Mapea `corridor_id` a `intersection_id`.
   - Determina estado según severidad:
     - Severidad 1-2: RED 30s, prioridad NORMAL.
     - Severidad 3-4: RED 60s, prioridad HIGH.
     - Severidad 5: RED 120s, prioridad CRITICAL.
   - Traduce a comando NTCIP.
   - Actualiza Redis y registra auditoría.

## Endpoints

### Health & Readiness

- `GET /health`: estado básico del proceso.
- `GET /ready`: valida conectividad a Redis y PostgreSQL.

### Signal State

- `GET /api/v1/signals/{intersection_id}`: estado actual del semáforo.
  - Devuelve: `current_state`, `timer_remaining_sec`, `priority_override_active`, `last_updated`.
  - Ejemplo:
    ```powershell
    Invoke-RestMethod -Uri http://localhost:8001/api/v1/signals/INT-AVENIDA_PRINCIPAL
    ```

### Audit

- `GET /api/v1/audit/logs?limit=100&offset=0`: logs de auditoría para el regulador.
  - Devuelve array de eventos con timestamp, event_type, status, details.

## NTCIP Payload Format (Simplificado)

Formato: `COMMAND|INTERSECTION_ID|[SIGNAL_STATE]|[PRIORITY_LEVEL]|[DURATION_SEC]`

Ejemplos:

- Bus retrasado: `ACTIVATE_PRIORITY|INT-AVENIDA_PRINCIPAL|green|high|80`
- Congestión severa: `SET_SIGNAL_STATE|INT-CENTRO|red|critical|120`

**Restricción**: máximo 256 bytes (NTCIP V06.13 standard).

## Redis State Schema

Estructura Hash para cada semáforo:

```
Key: traffic_light:{intersection_id}
Fields:
  - current_state (string): "green" | "red" | "yellow"
  - timer_remaining_sec (int): segundos hasta cambio
  - priority_override_active (bool): "True" | "False"
  - last_updated (ISO 8601 datetime)
TTL: 3600 segundos (1 hora)
```

## PostgreSQL Audit Schema

Tabla `signal_audit_log` (append-only):

- `log_id` (UUID): identificador correlativo.
- `timestamp` (TIMESTAMPTZ): cuando ocurrió el evento.
- `event_type` (VARCHAR): "signal_priority_applied" | "congestion_response" | etc.
- `intersection_id` (VARCHAR): qué semáforo fue afectado.
- `bus_id` (VARCHAR, nullable): bus que causó la acción.
- `priority_level` (VARCHAR, nullable): "NORMAL" | "HIGH" | "CRITICAL".
- `status` (VARCHAR): "success" | "failure".
- `details` (TEXT): información adicional.

## Independencia

- El servicio funciona con eventos sintéticos simulados en Kafka.
- No depende de otros microservicios excepto del bus Kafka.
- Redis y PostgreSQL son totalmente configurables vía `.env`.

## Robustez

- Pool async de PostgreSQL con `asyncpg` + timeout.
- Conexión Redis con retry automático.
- Consumer Kafka con manejo de errores y re-balance.
- Deserialización JSON robusta con validación Pydantic.
- Logging centralizado para debugging.
- Auditoría inmutable de todas las acciones regulatorias.

## Criterios de Aceptación (MVP 70%)

✅ Consume eventos de Kafka: `tracking.bus.delayed` y `congestion.alert.created`.

✅ Traduce a NTCIP: payloads ≤256 bytes.

✅ Actualiza estado en Redis en tiempo real (<1ms latencia).

✅ Persiste logs de auditoría en PostgreSQL.

✅ Re-enrutamiento del bus en <10 segundos.

✅ Endpoints REST para consultar estado y auditoría.

✅ Health check + readiness check.
