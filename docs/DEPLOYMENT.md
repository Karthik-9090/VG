# Deployment Guide - VayuGuard

This document provides deployment recommendations and production-ready options for VayuGuard.

## Docker Compose (local integration)

The repository includes a root-level `docker-compose.yml` to run the full stack together:

```bash
docker compose up --build
```

Services launched:
- PostgreSQL: `localhost:5432`
- Backend API: `http://localhost:5000`
- ML service: `http://localhost:8001`
- Frontend: `http://localhost:8080`

## Frontend Deployment

### Static hosting

- Build with `npm run build` in `frontend/`.
- Deploy `frontend/dist` to Vercel, Netlify, or any static host.
- Set `VITE_API_URL` to the production backend API base URL.

### Docker deployment

- Build image from `frontend/Dockerfile`.
- Run on a web server or behind Nginx.
- Expose the container port `80`.

## Backend Deployment

### Cloud provider

- Supported by providers like Render, Fly, or AWS App Runner.
- The backend uses environment variables from `backend/.env.example`.
- Required variables:
  - `PORT`
  - `DB_HOST`
  - `DB_PORT`
  - `DB_NAME`
  - `DB_USER`
  - `DB_PASSWORD`
  - `JWT_SECRET`
  - `ML_SERVICE_URL`

### Docker deployment

- Build from `backend/Dockerfile`.
- Connect the backend to PostgreSQL and ML service using service hostnames or network aliases.

## ML Service Deployment

### Cloud provider

- Deploy `ml-service/` using Python-compatible hosting or Docker.
- The ML service uses `ml-service/config.yml` with env var substitution.
- Expose port `8001` and set `ML_SERVICE_URL` in the backend.

### Docker deployment

- Build from `ml-service/Dockerfile`.
- Ensure the container has access to the PostgreSQL database and any model artifacts.

## Database

- Apply `infra/schema.sql` to create the required PostgreSQL tables.
- Use a managed PostgreSQL instance for production.
- Create database credentials matching backend and ML service configuration.

## CI/CD

- Frontend: `.github/workflows/frontend-ci.yml`
- Backend: `.github/workflows/backend-ci.yml`
- ML Service: `.github/workflows/ml-service-ci.yml`

A production pipeline should include build/test steps, container image creation, and deployment to the chosen cloud provider.

## Production runbook

### Deploy the stack

1. Apply the schema from `infra/schema.sql` to your PostgreSQL instance.
2. Build and deploy services using Docker or your chosen cloud provider.
3. For local integration, run:
   ```bash
   docker compose up --build
   ```
4. Confirm the following endpoints:
   - Frontend: `http://localhost:8080`
   - Backend: `http://localhost:5000`
   - ML service: `http://localhost:8001`
   - Prometheus: `http://localhost:9090`
   - Grafana: `http://localhost:3000`

### Scheduled jobs

- Daily ingestion runs are configured with `.github/workflows/data-pipeline-schedule.yml`.
- Weekly retraining runs are configured with `.github/workflows/model-retrain-schedule.yml`.

### Monitoring and alerting

- Prometheus scrapes backend and ML service metrics from `prometheus/prometheus.yml`.
- Alert rules are defined in `prometheus/alerts.yml` and include service downtime and latency thresholds.
- Grafana dashboards are provisioned from `grafana/dashboards/vayuguard-overview.json`.

### Operational checks

- Verify `backend` and `ml-service` are up using Prometheus target status.
- Review Grafana dashboard panels for request latency, service availability, and alerting trends.
- If a service is down, inspect container logs and restart the affected service.

### Best practices

- Use HTTPS for frontend and API endpoints.
- Keep `JWT_SECRET` and database credentials secret.
- Monitor service health and log errors from backend, ML service, and PostgreSQL.
- Update the ML model periodically using the data pipeline and record version metadata in the ML database.
