# VayuGuard Architecture

## Overview
VayuGuard is a production-ready air quality forecasting and health advisory platform with the following logical components:

- `data-pipeline`: Python-based ingestion and ETL service for OpenAQ and Open-Meteo
- `ml-service`: Python/FastAPI microservice for training, evaluation, and AQI prediction
- `backend`: Node.js/Express REST API for authentication, analytics, alerts, and orchestration
- `frontend`: React/Vite application for dashboards, forecasting, and administration
- `database`: PostgreSQL hosted on Supabase for all application data
- `monitoring`: Prometheus and Grafana for metrics and operational visibility

## Component Architecture

### 1. Data Ingestion Pipeline

Responsible for:
- Pulling AQI data from OpenAQ for Chennai, Bengaluru, Hyderabad
- Pulling weather data from Open-Meteo for the same cities
- Validating incoming payloads and cleaning missing values
- Removing duplicate records before insertion
- Logging ingestion metadata and failures into `ingestion_logs`
- Inserting raw and cleaned rows into PostgreSQL

Key files and responsibilities:
- `data-pipeline/ingest_aqi.py`
- `data-pipeline/ingest_weather.py`
- `data-pipeline/validate.py`
- `data-pipeline/db.py`
- `data-pipeline/config.yml`

### 2. ML Service

Responsible for:
- Loading historical AQI and weather data
- Engineering lag, rolling average, time, and weather features
- Training baseline, RandomForest, XGBoost models
- Selecting the best model using MAE, RMSE, MAPE
- Saving model artifacts and metadata to PostgreSQL and disk
- Serving predictions through FastAPI

Key files and responsibilities:
- `ml-service/train.py`
- `ml-service/evaluate.py`
- `ml-service/predict.py`
- `ml-service/app.py`
- `ml-service/model_metadata.py`

### 3. Node Backend

Responsible for:
- User authentication and role-based authorization using JWT
- Managing user and health profile data
- Handling alerts and alert subscription logic
- Integrating forecast and health advisory data into API responses
- Exposing analytics endpoints for average AQI, hotspots, trends, and exposures
- Forwarding forecast requests to the ML service when required

Key folders:
- `backend/controllers`
- `backend/routes`
- `backend/services`
- `backend/middleware`
- `backend/models`

### 4. Frontend

Responsible for:
- Login/Register flows
- Dashboard showing current AQI, weather, status, and forecast summary
- Forecast page with 24-hour prediction chart and risk summary
- Health advisory page for asthma, elderly, child, and outdoor worker profiles
- Analytics page for trends, hotspots, correlations, and city comparisons
- Admin page for user, alert, and statistics management
- Map page with Leaflet markers for city AQI locations

Key pages:
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/pages/Forecast.jsx`
- `frontend/src/pages/HealthAdvisory.jsx`
- `frontend/src/pages/Analytics.jsx`
- `frontend/src/pages/Admin.jsx`
- `frontend/src/pages/Login.jsx`
- `frontend/src/pages/Register.jsx`

## Data Flow

1. `data-pipeline` fetches and stores AQI and weather data in PostgreSQL.
2. `ml-service` reads PostgreSQL, trains models, writes forecasts and metadata.
3. `backend` reads PostgreSQL and invokes `ml-service` for on-demand predictions.
4. `frontend` consumes `backend` APIs for real-time dashboard, analytics, and advisories.

## Deployment Topology

- `frontend` deployed to Vercel
- `backend` deployed to Render as a Node web service
- `ml-service` deployed to Render as a Python web service
- `PostgreSQL` provisioned on Supabase
- Local development supported by Docker Compose
- CI/CD via GitHub Actions for build, lint, test, and deploy

## API Contracts

### FastAPI ML service

- `GET /health`
  - Response: `{ "status": "ok", "service": "ml-service" }`

- `GET /current-aqi`
  - Response: `{ "city": "Chennai", "aqi": 82, "category": "Moderate", "timestamp": "2026-06-04T10:00:00Z" }`

- `POST /forecast`
  - Request: `{ "city": "Hyderabad", "horizon": 24 }`
  - Response: `{ "city": "Hyderabad", "forecast": [{ "timestamp": "2026-06-05T10:00:00Z", "aqi": 94, "category": "Moderate" }], "model": "xgboost" }`

- `POST /health-risk`
  - Request: `{ "aqi": 140, "profile": "Asthma" }`
  - Response: `{ "riskLevel": "High", "advisory": "Limit outdoor exertion, use mask, follow asthma action plan." }`

### Node Backend

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/users`
- `GET /api/current-aqi`
- `POST /api/forecast`
- `GET /api/analytics/summary`
- `POST /api/alerts`
- `GET /api/alerts`

## Database Responsibilities

- `users`: authentication, roles, contact info
- `health_profiles`: user health sensitivities and advisory preferences
- `aqi_data`: city-specific AQI observations
- `weather_data`: weather observations matched by city and hour
- `forecasts`: 24-hour AQI prediction series
- `alerts`: user alert rules and status
- `model_metadata`: model metrics, version, selected model
- `ingestion_logs`: API ingestion metadata and errors

## Monitoring and Observability

- `backend` and `ml-service` export Prometheus metrics for request rates, latency, errors, and ingestion status
- Grafana dashboards visualize AQI ingestion, forecast accuracy, alert count, and system health
- Alerts are configured for ingestion failure, prediction service errors, and API uptime issues

## Testing Strategy

- Unit tests for individual modules in backend, ml-service, and data pipeline
- API integration tests for backend and FastAPI endpoints
- Data validation tests for ingestion and feature generation
- End-to-end smoke validation with local Docker Compose targeting the full stack

## Notes

This architecture document is the foundation for Phase 3 folder structure and Phase 4 database design.
