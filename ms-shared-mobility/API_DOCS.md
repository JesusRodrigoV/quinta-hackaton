# API Endpoints — Mobility Hub Service

**Resumen:** Documento que lista todos los endpoints del microservicio, los cuerpos de petición (request body) y los schemas usados (referencia a `app/models.py`).

**Health**
- **Endpoint:** GET `/health`
- **Descripción:** Estado general de la aplicación y conectividad a DB/Kafka.
- **Response (200):** `HealthResponse`
  - Ejemplo: `{ "status": "ok", "db": true, "kafka": true }`

**Vehicles**
- **Endpoint:** GET `/api/v1/vehicles/available?lat={lat}&lng={lng}&radius_meters={r}`
- **Descripción:** Busca vehículos `available` cerca usando `$geoNear`.
- **Response (200):** Lista de documentos `VehicleOut` con campo adicional `distance_meters` proporcionado por `$geoNear`.

- **Endpoint:** GET `/api/v1/vehicles/{vehicle_id}`
- **Descripción:** Obtener detalles de un vehículo.
- **Response (200):** `VehicleOut`.
- **Errors:** 404 si no existe.

- **Endpoint:** POST `/api/v1/vehicles`
- **Descripción:** Registrar un vehículo (admin).
- **Request Body:** `VehicleCreate`
  - Ejemplo:
    ```json
    {
      "vehicle_id": "VHC123",
      "type": "scooter",
      "battery_level": 85,
      "location": { "type": "Point", "coordinates": [-73.98, 40.75] },
      "status": "available"
    }
    ```
- **Response (201):** Documento creado (objeto `VehicleOut` con `_id`).

- **Endpoint:** PATCH `/api/v1/vehicles/{vehicle_id}/location`
- **Descripción:** Ping desde IoT; actualiza `location` y `battery_level`.
- **Request Body:** `VehicleLocationUpdate`
  - Ejemplo: `{ "lat": 40.75, "lng": -73.98, "battery_level": 80 }`
- **Response (200):** Documento `VehicleOut` actualizado.

**Reservations**
- **Endpoint:** POST `/api/v1/reservations`
- **Descripción:** Crear reserva; verifica que `vehicle.status == available` y que el usuario no tenga otra reserva activa. Operación atómica (transacción).
- **Request Body:** `ReservationCreate`
  - Ejemplo: `{ "user_id": "550e8400-e29b-41d4-a716-446655440000", "vehicle_id": "VHC123" }`
- **Response (201):** Documento de reserva (`ReservationOut`) con `status: active`.
- **Errors:** 400 si usuario ya tiene reserva o vehículo no disponible.

- **Endpoint:** GET `/api/v1/reservations/{id}`
- **Descripción:** Obtener reserva por id.
- **Response (200):** `ReservationOut`.
- **Errors:** 404 si no existe.

- **Endpoint:** GET `/api/v1/reservations/user/{user_id}/active`
- **Descripción:** Obtener reserva activa del usuario.
- **Response (200):** `ReservationOut` (si existe), 404 si no hay activa.

- **Endpoint:** POST `/api/v1/reservations/{id}/unlock`
- **Descripción:** Valida que la reserva esté `active` y no expirada (10 min). Cambia `status` a `fulfilled`, pone vehículo `in_use`, publica `shared-mobility.ride.started`.
- **Request Body:** none
- **Response (200):** `UnlockResponse` — `{ "reservation_id": "...", "unlocked": true }`
- **Errors:** 400 si no válida, 404 si no existe.

- **Endpoint:** POST `/api/v1/reservations/{id}/end-ride`
- **Descripción:** Finaliza viaje; calcula duración y costo ($0.15/min), marca vehículo `available`, publica `shared-mobility.ride.ended`, ejecuta comprobación de understock como BackgroundTask.
- **Request Body:** `EndRideRequest`
  - Ejemplo: `{ "final_lat": 40.75, "final_lng": -73.98 }`
- **Response (200):** Resumen: `{ "reservation_id": "...", "duration_minutes": 12, "total_cost": "1.80" }`

- **Endpoint:** DELETE `/api/v1/reservations/{id}`
- **Descripción:** Cancela una reserva activa; libera vehículo (set `current_user_id` null y `status: available`).
- **Response (200):** `{ "reservation_id": "...", "cancelled": true }`

**Damage Reports**
- **Endpoint:** POST `/api/v1/damage-reports`
- **Descripción:** Reporte de daño sobre un vehículo.
- **Request Body:** `DamageReportCreate`
  - Ejemplo:
    ```json
    {
      "vehicle_id": "VHC123",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "description": "Freno roto",
      "severity": "high"
    }
    ```
- **Behavior:** Si `severity` es `high` o `total_loss`, se marca vehículo `maintenance` y se publica `shared-mobility.vehicle.damaged`.
- **Response (200):** `{ "vehicle_id": "VHC123", "reported": true }`

**Eventos Kafka (producción)**
- `shared-mobility.ride.started` — Payload: `{ vehicle_id, user_id, reservation_id, lat, lng }`
- `shared-mobility.ride.ended` — Payload: `{ reservation_id, duration_minutes, total_cost_usd }`
- `shared-mobility.vehicle.damaged` — Payload: `{ vehicle_id, severity, reported_by }`
- `shared-mobility.zone.understock` — Payload: `{ zone_lat, zone_lng, available_count }`

**Eventos Kafka (consumo)**
- `payment.journey.completed` — Handler espera `{ reservation_id, payment_status, ... }`. Si `payment_status != 'approved'` cancela la reserva activa y libera vehículo.

**Schemas (referencia a `app/models.py`)**
- **`VehicleCreate`**: `vehicle_id: str`, `type: "scooter"|"ebike"`, `battery_level: int (0-100)`, `location: { type: "Point", coordinates: [lng, lat] }`, `status`.
- **`VehicleOut`**: `_id`, `vehicle_id`, `type`, `battery_level`, `location`, `status`, `current_user_id`.
- **`VehicleLocationUpdate`**: `lat: float`, `lng: float`, `battery_level: int`.
- **`ReservationCreate`**: `user_id: UUID`, `vehicle_id: str`.
- **`ReservationOut`**: `_id`, `user_id`, `vehicle_id`, `start_time`, `end_time?`, `total_cost?`, `status`.
- **`UnlockResponse`**: `reservation_id`, `unlocked: bool`.
- **`EndRideRequest`**: `final_lat`, `final_lng`.
- **`DamageReportCreate`**: `vehicle_id`, `user_id`, `description`, `severity: low|medium|high|total_loss`.
- **`HealthResponse`**: `status`, `db: bool`, `kafka: bool`.

**Códigos HTTP esperados**
- 200: OK para lecturas y acciones completadas.
- 201: Creación (vehículo, reserva).
- 400: Petición inválida (negocio/validación).
- 404: Recurso no encontrado.

**Notas operativas**
- La reserva expira si no se `unlock` en 10 minutos; un job APScheduler revisa y cancela reservas expiradas cada 60s.
- Las operaciones que afectan vehículo + reserva usan transacciones MongoDB (se requiere replica set, ver `docker-compose.yml`).
