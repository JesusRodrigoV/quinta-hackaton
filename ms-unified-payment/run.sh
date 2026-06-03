#!/bin/bash

# 1. Crear red de Docker para comunicación interna
docker network create payment-net 2>/dev/null || true

# 2. Levantar PostgreSQL
echo "Iniciando PostgreSQL..."
docker run -d \
  --name payment-db \
  --network payment-net \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_DB=payments_db \
  -v $(pwd)/db/init.sql:/docker-entrypoint-initdb.d/init.sql \
  postgres:15-alpine

# 3. Construir la imagen de la Aplicación
echo "Construyendo la imagen de la App..."
docker build -t payment-service .

# 4. Levantar la Aplicación
echo "Iniciando la Aplicación..."
docker run -d \
  --name payment-app \
  --network payment-net \
  -p 3000:3000 \
  -e DB_HOST=payment-db \
  -e DB_USER=admin \
  -e DB_PASS=secret \
  -e DB_NAME=payments_db \
  payment-service

echo "Sistema desplegado sin Docker Compose."
