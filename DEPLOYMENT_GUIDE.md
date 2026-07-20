# Production-Grade Hourly AQI Collection Service - Deployment Guide

**Status:** ✅ Ready for Production  
**Version:** 1.0  
**Date:** 2026-06-15  

---

## 📋 Overview

The AQI Collection Service is a production-grade Python application that:
- ✅ Collects AQI data hourly from WAQI API
- ✅ Stores 12 data fields (AQI, pollutants, weather)
- ✅ Prevents duplicate records
- ✅ Logs all collections and errors
- ✅ Creates daily CSV backups
- ✅ Generates collection reports
- ✅ Supports multiple deployment methods

**Coverage:** Chennai, Bengaluru, Hyderabad  
**Data Retention:** Unlimited (PostgreSQL)  
**CSV Backups:** Daily (automatic)

---

## 📊 Data Fields Collected

| Field | Type | Unit | Source |
|-------|------|------|--------|
| AQI | Integer | Index (0-500) | WAQI |
| PM2.5 | Float | µg/m³ | WAQI |
| PM10 | Float | µg/m³ | WAQI |
| NO2 | Float | ppb | WAQI |
| O3 | Float | ppb | WAQI |
| SO2 | Float | ppb | WAQI |
| CO | Float | ppm | WAQI |
| Temperature | Float | °C | WAQI |
| Humidity | Float | % | WAQI |
| Wind Speed | Float | m/s | WAQI |
| Pressure | Float | mb | WAQI |
| Timestamp | DateTime | ISO 8601 | WAQI |

---

## 🔧 Prerequisites

### System Requirements
- Python 3.11+
- PostgreSQL 15+
- 512 MB RAM minimum
- 1 GB disk space for logs/backups
- Network access to WAQI API

### Dependencies
```
psycopg2-binary==2.9.9
schedule==1.2.0
python-dotenv==1.0.0
requests==2.31.0
```

### Configuration
```
.env file should contain:
  WAQI_API_KEY=<your_key>
  DB_HOST=localhost
  DB_PORT=5432
  DB_NAME=vayuguard
  DB_USER=vayuguard_user
  DB_PASSWORD=vayuguard_pass
```

---

## 🚀 Deployment Methods

### Method 1: Windows Task Scheduler (Windows Only)

**Best for:** Windows servers, local machines

#### Setup
```powershell
# Run as Administrator
python setup\setup_windows_task.py
```

#### Manual Configuration
1. Open Task Scheduler (taskschd.msc)
2. Create New Folder: `VayuGuard`
3. Right-click folder → Create Task
4. Set Trigger: `Hourly` (repeat every 1 hour)
5. Set Action: `Start program` → `python collector.py`
6. Set to run with highest privileges
7. Configure retry on failure (3 times, 5 min interval)

#### PowerShell Command
```powershell
Register-ScheduledTask `
  -TaskName "VayuGuard\AQI Collection" `
  -Action (New-ScheduledTaskAction -Execute "python" -Argument "C:\path\to\collector.py") `
  -Trigger (New-ScheduledTaskTrigger -Hourly) `
  -RunLevel Highest `
  -Force
```

#### Command Line
```cmd
schtasks /create /tn "VayuGuard\AQI Collection" `
  /tr "python C:\path\to\collector.py" `
  /sc hourly /mo 1 /f
```

#### Verification
- Task Scheduler → Task Scheduler Library → VayuGuard → AQI Collection
- Status should show "Ready"
- Last Run Result should show success code (0)

---

### Method 2: Cron (Linux/macOS)

**Best for:** Linux/macOS servers, production environments

#### Setup
```bash
chmod +x setup/setup_cron.sh
./setup/setup_cron.sh
```

#### Manual Configuration
```bash
# Edit crontab
crontab -e

# Add this line:
0 * * * * cd /path/to/vayuguard && python collector.py >> data-pipeline/logs/cron.log 2>&1
```

Explanation:
- `0` = minute 0
- `*` = every hour
- `* *` = every day, every month
- `*` = every day of week

#### Examples
```bash
# Every hour
0 * * * * python collector.py

# Every 2 hours
0 */2 * * * python collector.py

# Every hour during business hours (8 AM - 6 PM)
0 8-18 * * 1-5 python collector.py

# Every 30 minutes
*/30 * * * * python collector.py
```

#### Verification
```bash
# List current cron jobs
crontab -l

# View logs
tail -f data-pipeline/logs/cron.log

# Check cron daemon status
sudo systemctl status cron  # Linux
launchctl list | grep cron  # macOS
```

---

### Method 3: Docker (Recommended for Production)

**Best for:** Container orchestration, cloud deployment, reproducible environments

#### Option A: Standalone Docker
```bash
# Build image
docker build -f Dockerfile.collector -t vayuguard-aqi-collector .

# Run container
docker run -d \
  --name vayuguard-aqi-collector \
  -e DB_HOST=localhost \
  -e DB_PORT=5432 \
  -e DB_NAME=vayuguard \
  -e DB_USER=vayuguard_user \
  -e DB_PASSWORD=vayuguard_pass \
  -e WAQI_API_KEY=<your_key> \
  -v $(pwd)/data-pipeline/logs:/app/data-pipeline/logs \
  -v $(pwd)/data-pipeline/backups:/app/data-pipeline/backups \
  vayuguard-aqi-collector
```

#### Option B: Docker Compose
```bash
# Add to docker-compose.yml:
services:
  aqi-collector:
    build:
      context: .
      dockerfile: Dockerfile.collector
    container_name: vayuguard-aqi-collector
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: vayuguard
      DB_USER: vayuguard_user
      DB_PASSWORD: vayuguard_pass
      WAQI_API_KEY: ${WAQI_API_KEY}
    volumes:
      - ./data-pipeline/logs:/app/data-pipeline/logs
      - ./data-pipeline/backups:/app/data-pipeline/backups

# Start:
docker-compose up --build aqi-collector
```

#### Option C: Docker Swarm
```bash
# Create service
docker service create \
  --name vayuguard-aqi-collector \
  --mode replicated \
  --replicas 1 \
  -e DB_HOST=postgres \
  -e WAQI_API_KEY=<key> \
  vayuguard-aqi-collector:latest
```

#### Option D: Kubernetes
```bash
kubectl apply -f k8s-aqi-collector.yaml
kubectl scale deployment vayuguard-aqi-collector --replicas 3
```

#### Docker Commands
```bash
# View logs
docker logs -f vayuguard-aqi-collector

# View collection logs
docker exec vayuguard-aqi-collector tail -f data-pipeline/logs/collector_*.log

# Execute manual collection
docker exec vayuguard-aqi-collector bash -c "RUN_ONCE=1 python collector.py"

# Stop container
docker stop vayuguard-aqi-collector

# Remove container
docker rm vayuguard-aqi-collector
```

---

### Method 4: Python Script (Development)

**Best for:** Development, testing, manual execution

```bash
# Single collection
RUN_ONCE=1 python collector.py

# Continuous scheduling
python collector.py

# Background execution (Linux/macOS)
nohup python collector.py > collector.log 2>&1 &

# Background execution (Windows)
start python collector.py
```

---

## 📝 Log Files

Logs are stored in `data-pipeline/logs/`:

```
collector_20260615.log    # Daily collection log
collector_20260616.log    # Previous day's log
cron.log                  # Cron execution log (Linux)
task_scheduler.log        # Windows Task Scheduler log
```

Log format:
```
2026-06-15 14:00:00 | INFO     | Starting AQI collection cycle
2026-06-15 14:00:02 | INFO     | Collecting data for Chennai...
2026-06-15 14:00:03 | INFO     | Success: AQI=74, PM2.5=74
2026-06-15 14:00:04 | INFO     | Collecting data for Bengaluru...
2026-06-15 14:00:05 | INFO     | Success: AQI=9, PM2.5=46
```

---

## 📊 CSV Backups

Daily backups stored in `data-pipeline/backups/`:

```
aqi_data_20260615.csv    # Daily backup
aqi_data_20260616.csv    # Previous day backup
```

CSV format:
```
city,aqi,pm25,pm10,no2,o3,so2,co,temperature,humidity,wind_speed,pressure,recorded_at,created_at
Hyderabad,99,99.0,73.0,6.7,11.8,6,7.4,32.0,46.89,0.57,1007.5,2026-06-15 17:00:23,2026-06-15 22:30:23
Bengaluru,9,46.0,24.0,12.3,8.7,1.3,3.1,35.9,47.0,0.2,686.0,2026-06-15 17:00:23,2026-06-15 22:30:23
```

---

## 📈 Report Generation

The service automatically generates `DATA_COLLECTION_REPORT.md` with:
- Total records collected
- Records per city
- Latest timestamps
- Daily collection summary
- Data completeness metrics

Example report:
```markdown
# AQI Data Collection Report

## Summary Statistics
| Metric | Value |
|--------|-------|
| Total Rows | 72 |
| Cities | 3 |
| Data Period | Last 7 days |

## Rows Per City
| City | Records | Latest Timestamp |
|------|---------|------------------|
| Chennai | 24 | 2026-06-15 22:30:23 |
| Bengaluru | 24 | 2026-06-15 22:30:23 |
| Hyderabad | 24 | 2026-06-15 22:30:23 |
```

---

## 🔍 Monitoring

### Health Checks

```bash
# Check database connectivity
python -c "
import psycopg2
conn = psycopg2.connect('host=localhost user=vayuguard_user password=vayuguard_pass dbname=vayuguard')
print('✅ Database OK')
conn.close()
"

# Check WAQI API
curl -s 'https://api.waqi.info/feed/Chennai/?token=YOUR_KEY' | jq '.status'

# Check latest collection
psql -U vayuguard_user -d vayuguard -c "
  SELECT city, aqi, created_at 
  FROM aqi_data 
  ORDER BY created_at DESC 
  LIMIT 3;"
```

### Metrics to Monitor

- **Collection Success Rate**: Successful / Total collections
- **API Response Time**: Should be < 5 seconds
- **Database Insert Time**: Should be < 100ms
- **Log File Size**: Should rotate daily
- **Disk Space**: Backups + logs should not exceed 10 GB

---

## 🚨 Troubleshooting

### Problem: Task not running (Windows)

**Solution:**
1. Check Task Scheduler → History tab
2. Run manually: `RUN_ONCE=1 python collector.py`
3. Check logs for errors
4. Verify PostgreSQL is running: `psql -U postgres`
5. Verify WAQI_API_KEY in .env

### Problem: Cron not executing (Linux)

**Solution:**
```bash
# Check cron daemon
sudo systemctl status cron

# Test cron entry
*/5 * * * * date >> /tmp/cron-test.log

# Check permissions
chmod 644 collector.py
chmod 755 data-pipeline/
```

### Problem: Database connection error

**Solution:**
```bash
# Test connection
psql -h localhost -U vayuguard_user -d vayuguard

# Check PostgreSQL service
pg_isready -h localhost

# Check .env file
cat .env | grep DB_
```

### Problem: WAQI API errors

**Solution:**
```bash
# Test API directly
curl 'https://api.waqi.info/feed/Chennai/?token=YOUR_KEY'

# Check rate limits
# WAQI free tier: 100 requests/minute

# Check API key validity in .env
echo $WAQI_API_KEY
```

---

## 🔐 Security Considerations

1. **API Keys**: Store WAQI_API_KEY in .env (not in version control)
2. **Database Passwords**: Use strong passwords, store in .env
3. **Logs**: Contain timestamps and city names only (no sensitive data)
4. **CSV Backups**: Store in secure location with restricted access
5. **Container Images**: Sign images, use private registries
6. **Network**: Use TLS/SSL for database connections in production

---

## 📦 Files Overview

```
VayuGuard/
├── collector.py                  # Main collection service
├── setup/
│   ├── setup_windows_task.py    # Windows Task Scheduler setup
│   ├── setup_cron.sh            # Linux/macOS Cron setup
│   ├── docker_deployment.py     # Docker deployment guide
│   └── vayuguard_aqi_collection.xml  # Windows Task XML
├── Dockerfile.collector         # Docker image definition
├── docker-compose.yml           # Docker Compose config
├── data-pipeline/
│   ├── logs/                    # Collection logs (daily)
│   ├── backups/                 # CSV backups (daily)
│   ├── collector_*.log          # Current logs
│   └── ingest_aqi.py           # Data ingestion module
└── DATA_COLLECTION_REPORT.md    # Generated report
```

---

## ✅ Post-Deployment Checklist

- [ ] WAQI_API_KEY obtained and configured
- [ ] Database connectivity verified
- [ ] PostgreSQL schema updated with new columns
- [ ] Deployment method selected (Windows/Cron/Docker)
- [ ] Setup script executed successfully
- [ ] Manual collection test passed (RUN_ONCE=1)
- [ ] Logs directory created and writable
- [ ] Backup directory created and writable
- [ ] First automated collection executed
- [ ] DATA_COLLECTION_REPORT.md generated
- [ ] Monitoring configured
- [ ] Alerts configured (optional)

---

## 📞 Support

For issues, check:
1. Log files: `data-pipeline/logs/collector_*.log`
2. Database: `SELECT * FROM aqi_data ORDER BY created_at DESC LIMIT 5;`
3. Report: `DATA_COLLECTION_REPORT.md`
4. WAQI Status: https://waqi.info/api/access/

---

**Status: ✅ PRODUCTION READY**
