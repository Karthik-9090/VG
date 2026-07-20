# VayuGuard - Production-Ready Air Quality Monitoring Platform

VayuGuard is a comprehensive hyperlocal air quality forecasting and health advisory platform with real-time AQI monitoring, personalized health advisories, and predictive forecasting capabilities.

---

## 🎯 Features

- **Real-Time AQI Monitoring**: Live air quality data for monitored cities (Chennai, Bengaluru, Hyderabad)
- **Health Advisories**: Profile-specific recommendations (General, Respiratory, Cardiac, Children, Elderly)
- **24/72-Hour Forecasting**: ML-powered AQI predictions with confidence metrics
- **Alert System**: Create custom AQI threshold alerts with notifications
- **Interactive Map**: Leaflet-based map visualization of AQI levels
- **Analytics Dashboard**: Trends, hotspots, and city comparisons
- **User Profiles**: Personalized health profile management
- **Admin Console**: User management and system monitoring
- **Prometheus/Grafana**: Production-grade metrics and dashboards

---

## 📐 Architecture Overview

### System Components

```
VayuGuard
├── Frontend (React 18 + Vite)
│   └── Dashboard, Forecasts, Health Advisory, Analytics, Map
├── Backend (Node.js/Express)
│   └── REST API, Authentication, Alerts, Analytics
├── ML Service (Python/FastAPI)
│   └── AQI Prediction, Health Risk Assessment
├── Data Pipeline (Python)
│   └── WAQI/OpenMeteo Integration, ETL
├── PostgreSQL Database
│   └── User data, Alerts, AQI history, Forecasts
└── Monitoring (Prometheus/Grafana)
    └── Metrics, Health Checks, Dashboards
```

### Service Responsibilities

**Frontend (React/Vite)**
- User dashboard with current AQI, weather, and status
- Real-time forecast charts and data export (CSV)
- Health advisory with profile-specific recommendations
- Alert management interface
- Interactive map with city AQI markers
- Analytics with trends and correlations
- User profile and authentication

**Backend (Node.js/Express)**
- JWT authentication and authorization
- REST API for all frontend features
- Alert creation, management, and soft-delete
- Analytics aggregation and trending
- ML service orchestration
- Database abstraction and security
- Prometheus metrics export

**ML Service (FastAPI)**
- Real-time AQI calculation by city
- 24/48/72-hour AQI forecasting
- Health risk assessment (5 profiles × 5 risk levels)
- Dynamic advisory generation
- Model training and evaluation
- Confidence score calculation

**Data Pipeline (Python)**
- Hourly AQI ingestion from WAQI (World Air Quality Index)
- Weather data fetch from OpenMeteo
- Data validation and cleaning
- Duplicate removal
- PostgreSQL persistence
- Ingestion metadata logging

### Data Flow

```
WAQI/OpenMeteo
       ↓
Data Pipeline (Python)
       ↓
PostgreSQL Database
       ↓
Backend (Node.js)  ← → ML Service (FastAPI)
       ↓
Frontend (React)
```

### API Contracts

**ML Service Endpoints**

```
GET  /health                      → Health check
GET  /current-aqi?city=Chennai    → Current AQI reading
POST /forecast                    → 24/48/72-hour predictions
POST /health-risk                 → Risk assessment & advisory
POST /health-risk-all            → All profiles risk levels
GET  /metrics                     → Prometheus metrics
```

**Backend API Endpoints**

```
POST   /api/auth/register        → Register new user
POST   /api/auth/login           → User login (JWT)
GET    /api/forecast/current-aqi → Current AQI by city
POST   /api/forecast/health-risk → Health risk calculation
POST   /api/forecast             → AQI forecasting
GET    /api/alerts               → List user alerts
POST   /api/alerts               → Create alert
DELETE /api/alerts/:id           → Delete alert
GET    /api/analytics/summary    → Summary stats
GET    /api/users                → User listing (admin)
```

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ (frontend & backend)
- **Python** 3.11+ (ml-service & data-pipeline)
- **PostgreSQL** 13+ (database)
- **Docker** (optional, for containerized deployment)

### Option 1: Docker Compose (Recommended)

```bash
# Clone and navigate to repository
cd vayuguard

# Start all services
docker compose up --build

# Services will be available at:
# Frontend:    http://localhost:8080
# Backend:     http://localhost:5000
# ML Service:  http://localhost:8001
# Prometheus:  http://localhost:9090
# Grafana:     http://localhost:3000
```

### Option 2: Local Development (Individual Services)

**Database Setup**
```bash
# Start PostgreSQL
# Apply schema from infra/schema.sql
psql -U postgres -h localhost < infra/schema.sql
```

**ML Service**
```bash
cd ml-service
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8001
```

**Backend**
```bash
cd backend
npm install
cp .env.example .env
npm start
# Runs on http://localhost:5000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3001
```

**Data Pipeline (Optional)**
```bash
cd data-pipeline
python -m pip install -r requirements.txt
python scheduler.py
```

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file in project root (or use `.env.example` as template):

```bash
# PostgreSQL
POSTGRES_DB=vayuguard
POSTGRES_USER=vayuguard_user
POSTGRES_PASSWORD=vayuguard_pass
DB_HOST=localhost
DB_PORT=5432
DB_NAME=vayuguard
DB_USER=vayuguard_user
DB_PASSWORD=vayuguard_pass

# Backend
PORT=5000
NODE_ENV=development
JWT_SECRET=your-secret-key-change-in-production
ML_SERVICE_URL=http://localhost:8001

# Frontend
VITE_API_URL=http://localhost:5000/api

# Data Pipeline
RUN_ONCE=false
INGESTION_INTERVAL=1
```

### Service Configuration Files

- `backend/config.js` - Backend configuration
- `ml-service/config.py` - ML service configuration
- `data-pipeline/config.py` - Pipeline configuration
- `prometheus/prometheus.yml` - Metrics scraping
- `grafana/provisioning/` - Dashboard provisioning

---

## 🧪 Testing

### Run All Tests

```bash
# Frontend tests
cd frontend && npm test

# Backend tests
cd backend && npm test

# ML Service tests
cd ml-service && pytest

# Data Pipeline tests
cd data-pipeline && pytest
```

---

## 📊 Monitoring & Observability

### Prometheus Metrics

Available at: `http://localhost:9090`

Scraped from:
- Backend: `http://localhost:5000/api/metrics`
- ML Service: `http://localhost:8001/metrics`

### Grafana Dashboards

Available at: `http://localhost:3000` (admin/admin)

Pre-configured dashboards:
- System Health
- Service Uptime
- Request Latency
- Error Rates
- AQI Trends

---

## 📈 Deployment

### Deployment Architecture

```
Vercel (Frontend)
      ↓
      └─→ Render (Backend Node.js) ←→ Render (ML Service Python)
                  ↓
           Supabase PostgreSQL
```

### Deployment Steps

1. **Database**: Apply `infra/schema.sql` to PostgreSQL instance
2. **Frontend**: Build and deploy to Vercel/Netlify
3. **Backend**: Deploy to Render or AWS App Runner
4. **ML Service**: Deploy to Render or Heroku
5. **Monitoring**: Set up Prometheus and Grafana

For detailed instructions, see: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## 📁 Project Structure

```
vayuguard/
├── frontend/                 # React 18 + Vite UI
│   ├── src/
│   │   ├── pages/           # Dashboard, Forecast, Advisory, Analytics, Map
│   │   ├── api/             # API client
│   │   ├── contexts/        # Auth context
│   │   └── index.css        # Global styles
│   ├── package.json
│   └── vite.config.js
├── backend/                  # Node.js + Express API
│   ├── routes/              # API endpoints
│   ├── services/            # Business logic
│   ├── middleware/          # Auth, error handling
│   ├── server.js
│   └── package.json
├── ml-service/              # Python + FastAPI ML
│   ├── app.py               # FastAPI application
│   ├── health_risk.py       # Advisory logic
│   ├── config.py
│   └── requirements.txt
├── data-pipeline/           # Python ETL
│   ├── ingest_aqi.py
│   ├── ingest_weather.py
│   ├── scheduler.py
│   └── requirements.txt
├── infra/                   # Infrastructure
│   └── schema.sql           # PostgreSQL schema
├── prometheus/              # Monitoring config
│   └── prometheus.yml
├── grafana/                 # Dashboards
│   └── provisioning/
├── .github/                 # CI/CD workflows
│   └── workflows/
├── docs/                    # Documentation
│   ├── DEPLOYMENT.md
│   └── archived/            # Historical reports
├── docker-compose.yml       # Local development
├── .env.example             # Configuration template
└── README.md                # This file
```

---

## 🔐 Security

### Best Practices

- **JWT Authentication**: Secure token-based auth with configurable expiry
- **Password Hashing**: bcryptjs for secure password storage
- **Environment Secrets**: All credentials via .env (never committed)
- **Database Credentials**: Configurable per environment
- **CORS Protection**: Enabled on backend API
- **Input Validation**: Express-validator on all endpoints
- **HTTPS Ready**: Deployable with SSL/TLS

### Security Checklist

- [ ] Change `JWT_SECRET` in production
- [ ] Use strong database passwords
- [ ] Enable HTTPS on all endpoints
- [ ] Rotate JWT secret periodically
- [ ] Monitor access logs
- [ ] Keep dependencies updated
- [ ] Review PostgreSQL permissions

---

## 🐛 Troubleshooting

### Frontend not connecting to backend
```bash
# Check VITE_API_URL in frontend .env
# Default: http://localhost:5000/api
# Verify backend is running on port 5000
curl http://localhost:5000/api/health
```

### Backend can't connect to database
```bash
# Verify PostgreSQL is running
psql -U vayuguard_user -h localhost -c "SELECT 1"

# Check DB_HOST, DB_PORT, DB_USER, DB_PASSWORD in .env
# Verify schema is applied: psql -U postgres < infra/schema.sql
```

### ML Service connection issues
```bash
# Verify FastAPI is running
curl http://localhost:8001/health

# Check ML_SERVICE_URL in backend .env
# Default: http://localhost:8001
```

### Docker Compose build failures
```bash
# Clean up containers and rebuild
docker compose down --volumes
docker compose up --build

# View service logs
docker compose logs [service-name]
```

---

## 📚 Additional Resources

- **Architecture Details**: See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **API Documentation**: Available at `/api/docs` when backend is running
- **Archived Reports**: [docs/archived/](docs/archived/)
- **Database Schema**: [infra/schema.sql](infra/schema.sql)
- **CI/CD Workflows**: [.github/workflows/](.github/workflows/)

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -m "Add your feature"`
3. Push to branch: `git push origin feature/your-feature`
4. Submit pull request

---

## 📄 License

VayuGuard is proprietary software. All rights reserved.

---

## 📞 Support

For issues, questions, or contributions:
- Create an issue in the repository
- Check existing documentation in `docs/`
- Review archived reports for historical context

---

**Last Updated**: 2026-06-15  
**Status**: Production Ready  
**Version**: 1.0.0
