# 📘 API Documentation - Payment & Billing Service

Este microservicio gestiona el ciclo de vida financiero de los ciudadanos en el sistema de transporte multimodal.

## 🔗 Endpoints Principales

### 1. Crear Usuario
**POST** `/users`
Crea un perfil de usuario con saldo inicial.
- **Body:**
  ```json
  {
    "identity_token": "STRING",
    "initial_balance": 100.00
  }
  ```

### 2. Registrar Tarjeta NFC
**POST** `/nfc/register`
Vincula una tarjeta física al ID de un usuario.
- **Body:**
  ```json
  {
    "tag_id": "STRING",
    "user_id": "UUID"
  }
  ```

### 3. Procesar Pago (Tap)
**POST** `/payments/tap`
Realiza el cobro de un tramo de viaje. Implementa transacciones **ACID**.
- **Body:**
  ```json
  {
    "user_id": "UUID",
    "amount": 2.75,
    "transport_mode": "bus | metro | scooter"
  }
  ```

### 4. Consultar Historial
**GET** `/users/{id}/transactions`
Retorna todas las transacciones realizadas por el usuario, ordenadas por fecha.

---

## 🛠️ Tecnologías
- **Runtime:** Node.js (TypeScript)
- **Database:** PostgreSQL 15
- **Orquestación:** Docker (Sin Compose)

---

## 🧪 Pruebas Rápidas (cURL)
```bash
# Crear Usuario
curl -X POST http://localhost:3000/users -H "Content-Type: application/json" -d '{"identity_token": "TKN-1", "initial_balance": 50.0}'

# Consultar Health
curl http://localhost:3000/health
```
