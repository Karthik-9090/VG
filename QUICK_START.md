# VayuGuard AQI Collection Service - Quick Start Guide

**Status:** ✅ READY FOR PRODUCTION  
**Last Updated:** 2026-06-15 22:40  
**Tested On:** Windows 11 + PostgreSQL 18.4

---

## 🚀 5-Minute Quick Start

### Step 1: Verify Prerequisites
```bash
# Check Python
python --version

# Check PostgreSQL
psql --version

# Check WAQI API Key
cat .env | grep WAQI_API_KEY
```

### Step 2: Test Single Collection
```bash
# Windows
Set-Location C:\path\to\VG
$env:RUN_ONCE='1'; python collector.py

# Linux/macOS
cd /path/to/VG
RUN_ONCE=1 python collector.py
```

**Expected Output:**
```
[OK] ProductionAQICollector initialized
[COLLECT] Collecting data for Chennai...
[COLLECT] Collecting data for Bengaluru...
[COLLECT] Collecting data for Hyderabad...
Collection Summary:
  Total Records: 3
  Successful: 3
  Duplicates: 0
  Failed: 0
[OK] Report generated: DATA_COLLECTION_REPORT.md
```

### Step 3: Deploy Scheduler

**Choose ONE deployment method:**

#### Option A: Windows Task Scheduler (Windows)
```powershell
# Run as Administrator
python setup/setup_windows_task.py

# Verify
Get-ScheduledTask -TaskName "VayuGuard*" | Select-Object State, LastRunTime
```

#### Option B: Cron (Linux/macOS)
```bash
chmod +x setup/setup_cron.sh
./setup/setup_cron.sh

# Verify
crontab -l | grep collector
```

#### Option C: Docker (Any OS)
```bash
docker-compose up --build aqi-collector
```

### Step 4: Monitor
```bash
# View logs
tail -f data-pipeline/logs/collector_*.log

# Check data collection
psql -U vayuguard_user -d vayuguard -c "
  SELECT city, aqi, created_at 
  FROM aqi_data 
  ORDER BY created_at DESC 
  LIMIT 10;"

# View report
cat DATA_COLLECTION_REPORT.md
```

---

## 📊 What Gets Collected

For each of 3 cities (Chennai, Bengaluru, Hyderabad):
- **Every Hour:** AQI, PM2.5, PM10, NO2, O3, SO2, CO, Temperature, Humidity, Wind Speed, Pressure
- **Daily:** CSV backup of all collected data
- **Real-time:** Detailed logs to `data-pipeline/logs/`

---

## 📁 Directory Structure

```
VayuGuard/
├── collector.py                           # Main service (production-ready)
├── setup/
│   ├── setup_windows_task.py              # Windows Task Scheduler setup
│   ├── setup_cron.sh                      # Linux/macOS Cron setup
│   └── docker_deployment.py               # Docker setup guide
├── data-pipeline/
│   ├── logs/                              # Daily collection logs
│   ├── backups/                           # Daily CSV backups
│   ├── ingest_aqi.py                      # Data ingestion module
│   └── config.py                          # Configuration
├── .env                                   # Secrets (WAQI_API_KEY, DB credentials)
├── docker-compose.yml                     # Docker orchestration
└── DEPLOYMENT_GUIDE.md                    # Complete deployment documentation
```

---

## 🔍 Verify Installation

### Health Check
```bash
# Test database connectivity
python -c "
import psycopg2
from dotenv import load_dotenv
import os
load_dotenv()
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)
print('✓ Database OK')
conn.close()
"

# Test WAQI API
curl -s 'https://api.waqi.info/feed/Chennai/?token=YOUR_KEY' | jq '.status'
# Expected: "ok"

# Check scheduler status (Windows)
Get-ScheduledTask -TaskName "VayuGuard*" | Format-Table State, LastRunTime, NextRunTime

# Check scheduler status (Linux)
crontab -l | grep collector.py
```

---

## 🐛 Troubleshooting

### Issue: "No module named 'psycopg2'"
```bash
pip install psycopg2-binary
```

### Issue: "WAQI_API_KEY not found"
```bash
# Check .env file
cat .env

# Should contain:
# WAQI_API_KEY=your_key_here
```

### Issue: "Connection refused" (PostgreSQL)
```bash
# Windows: Start PostgreSQL service
Get-Service -Name postgresql* | Start-Service

# Linux: Start PostgreSQL
sudo systemctl start postgresql
```

### Issue: "Duplicate detected" every time
This is normal if running within the same hour. Duplicates are detected per hour.
Next hour will collect new data.

### Issue: Task not running (Windows)
1. Open Task Scheduler
2. Look for: Task Scheduler Library > VayuGuard > AQI Collection
3. Right-click > Run
4. Check History tab for errors
5. Review logs in `data-pipeline/logs/`

---

## 📈 Monitoring Dashboard

### Real-time Collection Status
```bash
# Monitor continuously (5-second refresh)
while true; do
  clear
  echo "=== VayuGuard Collection Status ==="
  echo "Last 5 collections:"
  psql -U vayuguard_user -d vayuguard -c "
    SELECT city, aqi, created_at 
    FROM aqi_data 
    ORDER BY created_at DESC 
    LIMIT 5;" | head -10
  echo ""
  echo "Total records: $(psql -U vayuguard_user -d vayuguard -c "SELECT COUNT(*) FROM aqi_data;" | tail -2 | head -1)"
  sleep 5
done
```

### Log Monitoring
```bash
# Watch logs in real-time
tail -F data-pipeline/logs/collector_*.log | grep -E "\[(OK|FAIL|COLLECT|WARNING)\]"
```

### Database Query Examples
```sql
-- Latest data per city
SELECT city, aqi, pm25, temperature, created_at 
FROM aqi_data 
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- Hourly collection success rate (last 7 days)
SELECT 
  DATE_TRUNC('hour', created_at) as hour,
  COUNT(*) as collections
FROM aqi_data
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour DESC;

-- Duplicate detection rate
SELECT 
  COUNT(DISTINCT (city, DATE_TRUNC('hour', recorded_at))) as unique_hours,
  COUNT(*) as total_records,
  ROUND(100.0 * COUNT(*) / COUNT(DISTINCT (city, DATE_TRUNC('hour', recorded_at))), 1) as records_per_hour
FROM aqi_data;
```

---

## 📋 Deployment Checklist

- [ ] Python 3.11+ installed
- [ ] PostgreSQL 15+ running with vayuguard database
- [ ] .env file contains WAQI_API_KEY
- [ ] WAQI API key is valid (tested manually)
- [ ] Database connectivity verified
- [ ] Test run successful (RUN_ONCE=1)
- [ ] Logs created in data-pipeline/logs/
- [ ] Report generated (DATA_COLLECTION_REPORT.md)
- [ ] Scheduler deployed (Windows/Cron/Docker)
- [ ] First scheduled collection completed
- [ ] CSV backup directory ready (for 1 AM backup)
- [ ] Monitoring configured

---

## 🔄 Daily Operations

### 1. Monitor Collection
```bash
# Every hour (automatic)
collector.py runs and collects data from WAQI

# Every day at 01:00
- CSV backup created: data-pipeline/backups/aqi_data_YYYYMMDD.csv
- Report updated: DATA_COLLECTION_REPORT.md

# Every hour (real-time)
- Check logs: data-pipeline/logs/collector_YYYYMMDD.log
- Check report: DATA_COLLECTION_REPORT.md
```

### 2. Verify Data Quality
```bash
# Check for gaps (no data for > 2 hours)
psql -U vayuguard_user -d vayuguard << 'EOF'
SELECT 
  city,
  DATE_TRUNC('hour', created_at) as hour,
  COUNT(*) as count
FROM aqi_data
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY city, DATE_TRUNC('hour', created_at)
ORDER BY city, hour DESC;
EOF
```

### 3. Backup Management
```bash
# List backups
ls -lh data-pipeline/backups/

# Archive old backups (older than 30 days)
find data-pipeline/backups/ -name "*.csv" -mtime +30 -delete

# Export monthly data
tar -czf backups_$(date +%Y%m).tar.gz data-pipeline/backups/
```

---

## 📞 Support Resources

1. **Logs:** `data-pipeline/logs/collector_*.log` - Check for errors
2. **Report:** `DATA_COLLECTION_REPORT.md` - View collection statistics
3. **Database:** Query `aqi_data` table directly with psql
4. **WAQI Status:** https://waqi.info/ (check if API is down)
5. **Full Guide:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## ✅ Production Readiness Checklist

| Aspect | Status | Notes |
|--------|--------|-------|
| Core Functionality | ✅ | Collects, stores, reports AQI data |
| Data Integrity | ✅ | Duplicate detection prevents re-collection |
| Error Handling | ✅ | Comprehensive logging, retry logic |
| Persistence | ✅ | PostgreSQL with daily backups |
| Scalability | ✅ | Supports Docker, Kubernetes scaling |
| Monitoring | ✅ | Logs, reports, database queries |
| Documentation | ✅ | Complete guides and examples |
| Testing | ✅ | Manual test passed, 3 cities verified |

---

**🎯 You're ready to deploy!**

Next step: Choose your deployment method and run setup script.
