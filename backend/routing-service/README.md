# UrbanFlow — Routing Service

Planificador de rutas multimodales inteligente. Encuentra la mejor combinación de bus, metro, scooter y caminata entre dos puntos de la ciudad usando un grafo de transporte en Neo4j.

## Stack

`Python 3.11` · `FastAPI` · `Neo4j 5` · `Docker`

## Cómo levantar

```bash
# Desde la raíz del proyecto
docker compose up -d neo4j
docker compose up routing-service
```

La API queda disponible en `http://localhost:8000`.

La primera vez que arranca, siembra automáticamente datos semilla de la red de Santiago (11 estaciones, 2 líneas de bus, 1 línea de metro, transfers a pie y scooter). Si la base ya tiene datos, el seed se omite.

> Para desarrollo local: `uvicorn app.main:app --reload` (requiere Python 3.11 y Neo4j corriendo).

---

## Endpoints

### `POST /api/v1/routes` — Planificar ruta

Obtiene las mejores rutas entre un origen y un destino.

```bash
curl -X POST http://localhost:8000/api/v1/routes \
  -H "Content-Type: application/json" \
  -d '{
    "origin_lat": -33.456,
    "origin_lon": -70.648,
    "dest_lat": -33.442,
    "dest_lon": -70.662
  }'
```

**Parámetros:**

| Campo | Tipo | Default | Descripción |
|---|---|---|---|
| `origin_lat` | float | — | Latitud del origen |
| `origin_lon` | float | — | Longitud del origen |
| `dest_lat` | float | — | Latitud del destino |
| `dest_lon` | float | — | Longitud del destino |
| `modes` | string[] | `["bus","metro","walk","scooter"]` | Modos de transporte permitidos |
| `preference` | string | `"time"` | Criterio de optimización: `time`, `cost` o `co2` |

**Response `200 OK`:**

```json
{
  "route_id": "a1b2c3d4-...",
  "options": [
    {
      "total_time_min": 15.5,
      "total_cost": 1.5,
      "total_co2_kg": 0.267,
      "segments": [
        {
          "from_station": {
            "station_id": "parque_central",
            "name": "Parque Central",
            "type": "bus_stop"
          },
          "to_station": {
            "station_id": "plaza_armas",
            "name": "Plaza de Armas",
            "type": "bus_stop"
          },
          "transport_mode": "bus",
          "line": "B1",
          "travel_time_min": 5.0,
          "distance_km": 1.2
        }
      ]
    }
  ]
}
```

El servicio devuelve hasta 5 opciones ordenadas según la preferencia indicada. Cada opción contiene uno o más segmentos con el detalle del tramo.

**Response `404 NOT FOUND`:**

```json
{
  "detail": "No se encontró ninguna ruta entre el origen y destino especificados"
}
```

---

### `GET /api/v1/routes/{route_id}` — Obtener ruta cacheada

Recupera el resultado de una ruta previamente planificada (con validez de 1 hora).

```bash
curl http://localhost:8000/api/v1/routes/a1b2c3d4-...
```

**Response:** mismo formato que `POST /api/v1/routes`. Si expiró o no existe: `404`.

---

### `GET /api/v1/stops` — Listar estaciones

```bash
curl "http://localhost:8000/api/v1/stops?skip=0&limit=50"
```

| Parámetro | Default | Límite |
|---|---|---|
| `skip` | `0` | — |
| `limit` | `50` | 200 max |

---

### `GET /api/v1/health` — Health check

```bash
curl http://localhost:8000/api/v1/health
```

```json
{
  "status": "healthy",
  "service": "routing-service"
}
```

Si Neo4j no responde, devuelve `"status": "unhealthy"`.

---

## Variables de Entorno

| Variable | Default | Descripción |
|---|---|---|
| `NEO4J_URI` | `bolt://neo4j:7687` | URI de conexión a Neo4j |
| `NEO4J_USER` | `neo4j` | Usuario |
| `NEO4J_PASSWORD` | `password` | Contraseña |

---

## Seed Data

El servicio incluye una red de prueba de Santiago centro con 11 estaciones:

- **Bus B1:** Parque Central → Plaza de Armas → Mercado Central → Terminal
- **Bus B2:** Estadio Nacional → Parque Central → Plaza de Armas → Universidad
- **Metro M1:** Estación Norte → Estación Centro → Estación Sur
- **Scooter:** hubs céntricos con conexiones a estaciones cercanas
- **Walking:** transfers peatonales entre estaciones y paradas próximas

---

## Estructura

```
routing-service/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── core/
│   │   └── graph.py
│   ├── models/
│   │   ├── route.py
│   │   └── requests.py
│   ├── schemas/
│   │   └── responses.py
│   ├── routers/
│   │   ├── routes.py
│   │   └── stops.py
│   ├── services/
│   │   └── route_planner.py
│   └── seed/
│       └── loader.py
├── Dockerfile
├── requirements.txt
└── .env
```
