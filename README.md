# Quinta Hackaton — UrbanFlow Technologies

Plataforma Inteligente de Movilidad Urbana.

## Microservicios

| Servicio | Puerto | Base de datos | Ubicación |
|----------|--------|---------------|-----------|
| `routing-service` | `:8001` | Neo4j (grafo) | `backend/routing-service/` |
| `telemetry-tracking-service` | `:8000` | TimescaleDB (series temporales) | `backend/telemetry-tracking-service/` |

## Cómo levantar

```bash
docker compose up --build
```

## Endpoints

### routing-service (`:8001`)

- `POST /api/v1/routes`   — Planificar ruta multimodal
- `GET  /api/v1/routes/{id}` — Obtener ruta cacheada
- `GET  /api/v1/stops`    — Listar paradas
- `GET  /api/v1/buses`    — Posiciones en vivo de los buses (desde Kafka)
- `GET  /api/v1/buses/{bus_id}` — Posición de un bus específico
- `GET  /api/v1/health`   — Health check

### Telemetría (Kafka)

El routing-service consume del topic `bus-location-updated` para mantener
posiciones actualizadas de los buses en memoria. No requiere TimescaleDB ni
el telemetry-tracking-service para funcionar.
