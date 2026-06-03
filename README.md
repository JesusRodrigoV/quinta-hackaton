
# Quinta Hackaton — UrbanFlow Technologies

Plataforma Inteligente de Movilidad Urbana.

## Microservicios

| Servicio | Puerto | Base de datos | Ubicación |
|----------|--------|---------------|-----------|
| `routing-service` | `:8001` | Neo4j (grafo) | `backend/routing-service/` |
| `telemetry-tracking-service` | `:8000` | TimescaleDB (series temporales) | `backend/telemetry-tracking-service/` |

## Cómo levantar

# Mobility Hub Service (UrbanFlow Tech)

FastAPI service implementing shared mobility vehicle reservations, ride lifecycle, and event publishing to Kafka.

Quick Start (requires Docker & Docker Compose):

```bash
docker compose up --build
```
## Endpoints

### routing-service (`:8001`)

- `POST /api/v1/routes` — Planificar ruta multimodal
- `GET /api/v1/stops`  — Listar paradas
- `GET /api/v1/health` — Health check

### telemetry-tracking-service (`:8000`)

- `POST /telemetry` — Recibir telemetría de buses
- `GET  /health`    — Health check
- `GET  /ready`     — Readiness check

The API will be available at http://localhost:8000. Health at `/health`.
# Quinta hackaton
