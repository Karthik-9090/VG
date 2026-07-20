#!/bin/bash
# Production deployment script

set -e

echo "VayuGuard Production Deployment"
echo "==============================="
echo ""

# Load environment
if [ ! -f ".env.production" ]; then
    echo "ERROR: .env.production not found"
    exit 1
fi

source .env.production

# Create backups directory
mkdir -p backups

echo "Building images..."
docker compose build --no-cache

echo "Pulling latest images..."
docker compose pull || true

echo "Stopping existing services..."
docker compose down || true

echo "Starting services..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo "Waiting for services to start..."
for i in {1..30}; do
    if curl -sf http://localhost/health >/dev/null 2>&1; then
        echo "Services healthy"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 5
done

echo "Checking service health..."
curl -f http://localhost/health || { echo "FAIL: Nginx"; exit 1; }
curl -f http://localhost:5000/api/health || { echo "FAIL: Backend"; exit 1; }
curl -f http://localhost:8001/health || { echo "FAIL: ML Service"; exit 1; }

echo ""
echo "Deployment successful!"
echo "Services:"
echo "  Frontend: http://localhost"
echo "  Backend:  http://localhost/api"
echo "  ML:       http://localhost/ml"
echo "  Grafana:  http://localhost:3000"
echo "  Prometheus: http://localhost:9090"
