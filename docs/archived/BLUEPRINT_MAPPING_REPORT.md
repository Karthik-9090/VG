# Blueprint Mapping Report — VayuGuard

This report maps the project blueprint items to files in this repository and highlights remaining gaps.

## 1. Ingest & Data Pipeline
- Data ingestion scripts: [data-pipeline/ingest_aqi.py](data-pipeline/ingest_aqi.py), [data-pipeline/ingest_weather.py](data-pipeline/ingest_weather.py)
- Pipeline config and DB: [data-pipeline/config.yml](data-pipeline/config.yml), [data-pipeline/db.py](data-pipeline/db.py), [data-pipeline/requirements.txt](data-pipeline/requirements.txt)
- ETL orchestration: [data-pipeline/pipeline.py](data-pipeline/pipeline.py)

## 2. ML Service (training, prediction, health-risk)
- FastAPI app: [ml-service/app.py](ml-service/app.py)
- Prediction CLI / API: [ml-service/predict.py](ml-service/predict.py)
- Training & evaluation: [ml-service/train.py](ml-service/train.py), [ml-service/evaluate.py](ml-service/evaluate.py)
- Deep-learning optional: [ml-service/train_dl.py](ml-service/train_dl.py), [ml-service/requirements.txt](ml-service/requirements.txt)
- Config & model metadata: [ml-service/config.yml](ml-service/config.yml), [ml-service/models/](ml-service/models/)
- Python recommendation: [ml-service/PYTHON_RECOMMENDATION.md](ml-service/PYTHON_RECOMMENDATION.md)

## 3. Backend (API, auth, analytics)
- Server entry: [backend/server.js](backend/server.js)
- Configuration: [backend/config.js](backend/config.js)
- Postgres client: [backend/db.js](backend/db.js)
- Routes and controllers: [backend/routes/](backend/routes/), [backend/controllers/](backend/controllers/)
- Seed & scripts: [backend/scripts/seed_user.js](backend/scripts/seed_user.js), [backend/scripts/e2e_smoke.js](backend/scripts/e2e_smoke.js)

## 4. Frontend (React + Vite)
- Project: [frontend/package.json](frontend/package.json)
- Vite config: [frontend/vite.config.js](frontend/vite.config.js)
- Source app: [frontend/src/](frontend/src/)
- Dockerfile: [frontend/Dockerfile](frontend/Dockerfile)

## 5. DevOps / Containerization / CI
- Root compose: [docker-compose.yml](docker-compose.yml)
- Dockerfiles: [backend/Dockerfile](backend/Dockerfile), [ml-service/Dockerfile](ml-service/Dockerfile), [frontend/Dockerfile](frontend/Dockerfile)
- Infra schema: [infra/schema.sql](infra/schema.sql)
- CI workflows: [.github/workflows/backend-ci.yml](.github/workflows/backend-ci.yml), [.github/workflows/frontend-ci.yml](.github/workflows/frontend-ci.yml), [.github/workflows/ml-service-ci.yml](.github/workflows/ml-service-ci.yml), [.github/workflows/data-pipeline-schedule.yml](.github/workflows/data-pipeline-schedule.yml), [.github/workflows/model-retrain-schedule.yml](.github/workflows/model-retrain-schedule.yml), [.github/workflows/e2e-smoke.yml](.github/workflows/e2e-smoke.yml)

## 6. Monitoring & Observability
- Prometheus config: [prometheus/prometheus.yml](prometheus/prometheus.yml)
- Alert rules: [prometheus/alerts.yml](prometheus/alerts.yml), [prometheus/alerts_model.yml](prometheus/alerts_model.yml)
- Grafana provisioning & dashboards: [grafana/provisioning/](grafana/provisioning/), [grafana/dashboards/](grafana/dashboards/)
- Metrics export middleware in services: see `prometheus_metrics` middleware in [ml-service/app.py](ml-service/app.py) and [backend] metrics middleware ([backend/server.js](backend/server.js)).

## 7. Documentation & Runbooks
- Architecture & blueprint: [ARCHITECTURE.md](ARCHITECTURE.md), [BLUEPRINT_COMPLIANCE_REPORT.md](BLUEPRINT_COMPLIANCE_REPORT.md)
- Deployment & runbook: [DEPLOYMENT.md](DEPLOYMENT.md), [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md)
- Verification & completion: [VERIFICATION_COMPLETE.md](VERIFICATION_COMPLETE.md), [COMPLETION_REPORT.md](COMPLETION_REPORT.md)

## 8. Tests
- Backend unit/integration tests: [backend/tests/](backend/tests/)
- ML tests: [ml-service/tests/](ml-service/tests/)
- Data-pipeline tests: [data-pipeline/tests/](data-pipeline/tests/)

## 9. Secrets & CI examples
- `.env` examples: [backend/.env.example](backend/.env.example)
- Secrets example script: [deploy/secrets_example.sh](deploy/secrets_example.sh) (AWS CLI + jq example)

## 10. E2E smoke harness
- Harness file: [backend/scripts/e2e_smoke.js](backend/scripts/e2e_smoke.js)
- CI workflow to run harness: [.github/workflows/e2e-smoke.yml](.github/workflows/e2e-smoke.yml)

## Gaps and recommended actions (to reach 100% parity)
1. Deep-learning runtime compatibility
   - Risk: `tensorflow>=2.15.0` in [ml-service/requirements.txt](ml-service/requirements.txt) may not install on newer Python versions (e.g., 3.14). Recommendation: pin CI and deployment Python to 3.10/3.11 or switch DL code to PyTorch.
   - Files: [ml-service/requirements.txt](ml-service/requirements.txt), [ml-service/train_dl.py](ml-service/train_dl.py), [ml-service/PYTHON_RECOMMENDATION.md](ml-service/PYTHON_RECOMMENDATION.md)

2. Secrets manager integration
   - Repo contains examples and docs but no runtime adapter for a chosen secrets manager. Implement secrets retrieval and injection in service startup or CI deploy steps.
   - Files: [deploy/secrets_example.sh](deploy/secrets_example.sh), [backend/.env.example](backend/.env.example)

3. CI staging deploy + gated promotion
   - Current CI builds and E2E job exist; add a deploy-to-staging job that provisions cloud resources (or uses Docker Compose on a runner), then runs the E2E harness as a gate before promoting.
   - Files: [.github/workflows/e2e-smoke.yml](.github/workflows/e2e-smoke.yml)

4. Model monitoring automation and retrain trigger verification
   - Prometheus rules added; ensure ML service exports MAE/time-series metrics (`ml_model_mae` or similar) and workflows trigger retraining on alerts.
   - Files: [prometheus/alerts_model.yml](prometheus/alerts_model.yml), [.github/workflows/model-retrain-schedule.yml](.github/workflows/model-retrain-schedule.yml)

5. Final runbooks and UAT checklist
   - Verify per-role runbooks include exact deploy, rollback, and on-call instructions.
   - Files: [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md), [COMPLETION_REPORT.md](COMPLETION_REPORT.md)

## Conclusion
The repository implements the majority of the blueprint. To claim 100% parity you should complete the items listed under "Gaps and recommended actions" — I can implement any of these next (CI staging deploy, secrets wiring for your cloud provider, model-monitoring dashboards, or final runbook polish).
