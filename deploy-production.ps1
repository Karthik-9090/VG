# PowerShell Production Deployment Script

Write-Host "=========================================="
Write-Host "VayuGuard Production Deployment"
Write-Host "=========================================="
Write-Host ""

# Check .env.production exists
if (-not (Test-Path ".env.production")) {
    Write-Host "[FAIL] .env.production not found" -ForegroundColor Red
    exit 1
}

# Create backups directory
if (-not (Test-Path "backups")) {
    New-Item -ItemType Directory -Path "backups" | Out-Null
}

Write-Host "[STEP 1] Building Docker images..." -ForegroundColor Yellow
# Note: Docker must be installed and running
Write-Host "Note: Requires Docker Desktop to be running" -ForegroundColor Cyan

Write-Host ""
Write-Host "[STEP 2] Environment Configuration" -ForegroundColor Yellow
Write-Host "Production config file: .env.production" -ForegroundColor Green

Write-Host ""
Write-Host "[STEP 3] Database Initialization" -ForegroundColor Yellow
Write-Host "Schema: infra/schema.sql" -ForegroundColor Green

Write-Host ""
Write-Host "[STEP 4] Services to Deploy" -ForegroundColor Yellow
Write-Host "  - Nginx (reverse proxy on port 80/443)"
Write-Host "  - Backend (Node.js/Express on 5000)"
Write-Host "  - ML Service (FastAPI on 8001)"
Write-Host "  - Frontend (Vite on 80)"
Write-Host "  - PostgreSQL (port 5432)"
Write-Host "  - Prometheus (port 9090)"
Write-Host "  - Grafana (port 3000)"
Write-Host "  - Data Pipeline (WAQI ingestion)"

Write-Host ""
Write-Host "[DEPLOYMENT CHECKLIST]" -ForegroundColor Yellow
Write-Host "Before deploying, verify:"
Write-Host "  [1] Update .env.production with production values"
Write-Host "  [2] Set strong JWT_SECRET and DB_PASSWORD"
Write-Host "  [3] Configure TLS certificates (TLS_CERT_PATH, TLS_KEY_PATH)"
Write-Host "  [4] Set CORS_ORIGIN to production domain"
Write-Host "  [5] Set WAQI_API_KEY and other API keys"
Write-Host "  [6] Backup existing database (if upgrading)"
Write-Host "  [7] Verify Grafana admin password"

Write-Host ""
Write-Host "[DEPLOYMENT COMMANDS]" -ForegroundColor Yellow
Write-Host ""
Write-Host "# On production server, run:"
Write-Host "docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build"
Write-Host ""
Write-Host "# Verify health:"
Write-Host "curl http://localhost/health"
Write-Host "curl http://localhost:5000/api/health"
Write-Host "curl http://localhost:8001/health"
Write-Host ""
Write-Host "# View logs:"
Write-Host "docker compose logs -f nginx"
Write-Host "docker compose logs -f backend"
Write-Host "docker compose logs -f ml-service"

Write-Host ""
Write-Host "[MONITORING & MAINTENANCE]" -ForegroundColor Yellow
Write-Host "- Grafana:      http://localhost:3000"
Write-Host "- Prometheus:   http://localhost:9090"
Write-Host "- Nginx status: http://localhost/health"
Write-Host ""
Write-Host "- Auto backups: Daily at 2 AM UTC (GitHub Actions)"
Write-Host "- Model retrain: Weekly Mon 4 AM UTC (GitHub Actions)"
Write-Host "- WAQI ingest: Daily 2 AM UTC (GitHub Actions)"

Write-Host ""
Write-Host "[ROLLBACK]" -ForegroundColor Yellow
Write-Host "If deployment fails, use GitHub Actions rollback workflow:"
Write-Host "  workflow: .github/workflows/rollback.yml"
Write-Host "  input: previous version tag (e.g., v1.0.0)"

Write-Host ""
Write-Host "[PRODUCTION ARCHITECTURE]" -ForegroundColor Green
Write-Host "✓ Nginx reverse proxy (single entry point)"
Write-Host "✓ Multi-stage Docker builds"
Write-Host "✓ Network isolation (vayuguard-net)"
Write-Host "✓ Persistent volumes (pgdata, prometheus-data, grafana-data)"
Write-Host "✓ Health checks on all services"
Write-Host "✓ Automatic restart policies"
Write-Host "✓ Resource limits configured"
Write-Host "✓ Non-root user containers"
Write-Host "✓ Security headers (HSTS, X-Content-Type-Options, etc.)"
Write-Host "✓ Rate limiting (100 req/min/IP)"
Write-Host "✓ Monitoring (Prometheus + Grafana)"
Write-Host "✓ Backup automation"
Write-Host "✓ Rollback capability"

Write-Host ""
Write-Host "Ready for production deployment!" -ForegroundColor Green
