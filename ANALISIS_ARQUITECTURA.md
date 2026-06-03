# Análisis de Arquitectura - Sistema de Movilidad Multimodal

## Resumen Ejecutivo
La arquitectura propuesta para la "Quinta Hackaton" es un ecosistema de microservicios altamente especializado y desacoplado, diseñado para manejar alta disponibilidad, baja latencia y cumplimiento regulatorio. El uso de una arquitectura dirigida por eventos (Event-Driven Architecture) via Kafka es el núcleo que permite la independencia de los equipos.

## Evaluación de Microservicios

### 1. MS Route Planning (Neo4j)
- **Fortaleza:** El uso de Neo4j es la elección correcta para problemas de caminos mínimos. La integración con OSM da una base sólida de datos reales.
- **Punto a considerar:** La actualización del grafo en tiempo real puede ser costosa computacionalmente; se recomienda usar algoritmos incrementales.

### 2. MS Real-Time Tracking (InfluxDB + Redis)
- **Fortaleza:** Separar el estado actual (Redis) del histórico (InfluxDB) optimiza tanto la latencia de consulta como la eficiencia de almacenamiento.
- **Punto a considerar:** La ingesta de 4,500 buses requiere un tuning fino de los adaptadores MQTT.

### 3. MS Unified Payment (PostgreSQL + ISO 20022)
- **Fortaleza:** Enfoque en integridad ACID y estándares internacionales.
- **Punto a considerar:** La gestión de tarifas sociales en tiempo real añade complejidad lógica; debe estar bien versionada.

### 4. MS Traffic Signal (NTCIP + Redis)
- **Fortaleza:** Manejo de protocolos industriales (NTCIP) y arquitectura hexagonal para aislamiento.
- **Punto a considerar:** El SLA de <10s es crítico; el "dead-letter queue" de Kafka debe ser monitoreado de cerca.

### 5. MS Shared Mobility (MongoDB + Redis Geo)
- **Fortaleza:** MongoDB permite flexibilidad para diferentes tipos de vehículos (scooters, bicis). Redis Geo es ideal para búsquedas de proximidad.

### 6. MS Congestion Prediction (ML + InfluxDB)
- **Fortaleza:** Separación de entrenamiento (S3/SageMaker) e inferencia (Microservicio).
- **Punto a considerar:** El "model drift" debe ser monitoreado con los eventos reales vs predicciones.

### 7. MS Notification (Cassandra)
- **Fortaleza:** Cassandra maneja perfectamente el volumen masivo de logs y tokens.
- **Punto a considerar:** La lógica de "viaje activo" debe ser muy eficiente para no enviar spam.

### 8. MS Analytics (ClickHouse)
- **Fortaleza:** ClickHouse es imbatible para analítica en tiempo real sobre miles de millones de eventos.

### 9. MS Audit (PostgreSQL + SHA-256)
- **Fortaleza:** Inmutabilidad vía software (hash-chaining) es una solución elegante y de bajo costo para cumplimiento.

## Evaluación del Plan de Trabajo
- **Estrategia de Mocks:** El uso de MSW y stubs en Kong es la mejor decisión para evitar bloqueos entre equipos.
- **Independencia:** Los "Entregables Github" separados facilitan el CI/CD independiente.

## Conclusión
La arquitectura es robusta y escalable. Para una hackatón, el mayor desafío será la **infraestructura y orquestación** de tantos motores de base de datos distintos. Se recomienda usar Docker Compose o Kubernetes local desde el día 1.
