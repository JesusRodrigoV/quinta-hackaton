# Quinta Hackaton — UrbanFlow Technologies

Plataforma Inteligente de Movilidad Urbana.

## Microservicios

| Servicio | Puerto | Base de datos |
|----------|--------|---------------|
| `routing-service` | `:8000` | Neo4j (grafo) |

## Cómo levantar

```bash
docker compose up --build
```

## Endpoints — routing-service

- `POST /api/v1/routes` — Planificar ruta multimodal
- `GET /api/v1/stops`  — Listar paradas
- `GET /api/v1/health` — Health check
