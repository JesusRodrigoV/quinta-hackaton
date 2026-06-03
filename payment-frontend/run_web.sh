#!/bin/bash

# 1. Asegurar que la red existe
docker network create payment-net 2>/dev/null || true

# 2. Construir la imagen del Frontend
echo "Construyendo la imagen del Frontend..."
docker build -t payment-frontend-img .

# 3. Levantar el Frontend
echo "Iniciando el Frontend en http://localhost:8080"
docker run -d \
  --name payment-web \
  --network payment-net \
  -p 8080:80 \
  payment-frontend-img

echo "Frontend desplegado."
