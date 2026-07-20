# 🎯 VayuGuard AQI Collector - Command Reference Card

## ⚡ Quick Commands

### Test & Verify
```bash
# Single collection cycle (test mode)
RUN_ONCE=1 python collector.py

# Full test suite (7 tests)
python test_collector.py

# Check database
psql -U vayuguard_user -d vayuguard -c "SELECT COUNT(*) FROM aqi_data;"
```

### View Logs
```bash
# Current day's logs (real-time)
tail -f data-pipeline/logs/collector_*.log

# View all logs
ls -lh data-pipeline/logs/

# Archive old logs
find data-pipeline/logs/ -name "*.log" -mtime +30 -archive
```

### Deploy (Choose One)

#### Windows Task Scheduler
```powershell
# Setup (run as Administrator)
python setup/setup_windows_task.py

# Verify
Get-ScheduledTask -TaskName "VayuGuard*" | Format-Table State, LastRunTime
```

#### Linux/macOS Cron
```bash
chmod +x setup/setup_cron.sh
./setup/setup_cron.sh

# Verify
crontab -l | grep collector
```

#### Docker
```bash
docker-compose up --build aqi-collector

# View logs
docker logs -f vayuguard-aqi-collector
```

### Monitor
```bash
# Database growth
watch -n 30 "psql -U vayuguard_user -d vayuguard -c 'SELECT COUNT(*) FROM aqi_data;'"

# Latest data
psql -U vayuguard_user -d vayuguard -c \
  "SELECT city, aqi, pm25, created_at FROM aqi_data ORDER BY created_at DESC LIMIT 5;"

# View report
cat DATA_COLLECTION_REPORT.md
```

---

## 📊 Database Queries

### Collection Statistics
```sql
-- Total records
SELECT COUNT(*) FROM aqi_data;

-- Records per city
SELECT city, COUNT(*) FROM aqi_data GROUP BY city;

-- Records per day (last 7 days)
SELECT DATE(created_at), COUNT(*) 
FROM aqi_data 
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY DATE DESC;

-- Average AQI per city
SELECT city, AVG(aqi) as avg_aqi, MAX(aqi) as max_aqi
FROM aqi_data
GROUP BY city;
```

### Data Quality
```sql
-- Check for gaps (missing hours)
SELECT city, DATE_TRUNC('hour', created_at) as hour, COUNT(*) as count
FROM aqi_data
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY city, hour
ORDER BY city, hour DESC;

-- Duplicate detection rate
SELECT 
  COUNT(*) as total,
  COUNT(DISTINCT (city, DATE_TRUNC('hour', recorded_at))) as unique_hourly_records,
  ROUND(100.0 * COUNT(*) / COUNT(DISTINCT (city, DATE_TRUNC('hour', recorded_at))), 1) as avg_per_hour
FROM aqi_data;

-- Latest timestamp per city
SELECT city, MAX(created_at) as latest_data
FROM aqi_data
GROUP BY city;
```

---

## 🔧 Troubleshooting

### Problem: Task not running
```bash
# Windows
Get-ScheduledTask -TaskName "VayuGuard*" -OutVariable task
$task | Start-ScheduledTask

# Check result
Get-ScheduledTask -TaskName "VayuGuard*" | Select-Object State, LastRunResult
```

### Problem: Database connection error
```bash
# Test connection
psql -h localhost -U vayuguard_user -d vayuguard -c "SELECT 1;"

# Check PostgreSQL service (Windows)
Get-Service -Name postgresql* | Select-Object Status, Name

# Check PostgreSQL service (Linux)
sudo systemctl status postgresql
```

### Problem: WAQI API key invalid
```bash
# Test API directly
curl -s 'https://api.waqi.info/feed/Chennai/?token=YOUR_KEY' | jq '.status'

# Check .env file
cat .env | grep WAQI_API_KEY

# Update if needed
echo "WAQI_API_KEY=new_key" >> .env
```

### Problem: No logs appearing
```bash
# Verify log directory exists
ls -la data-pipeline/logs/

# Create manually if missing
mkdir -p data-pipeline/logs

# Check permissions
chmod 755 data-pipeline/logs

# Run test
RUN_ONCE=1 python collector.py
```

---

## 📈 Performance Monitoring

### Check Collection Rate
```bash
# Collections per hour (last 24h)
psql -U vayuguard_user -d vayuguard << 'EOF'
SELECT 
  DATE_TRUNC('hour', created_at) as hour,
  COUNT(*) as collections,
  AVG(EXTRACT(EPOCH FROM (created_at - recorded_at))) as avg_latency_sec
FROM aqi_data
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;
EOF
```

### Data Completeness
```bash
# Check for missing data fields
psql -U vayuguard_user -d vayuguard << 'EOF'
SELECT 
  city,
  COUNT(*) as total,
  COUNT(pm25) as with_pm25,
  COUNT(temperature) as with_temperature,
  COUNT(humidity) as with_humidity
FROM aqi_data
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY city;
EOF
```

---

## 🐳 Docker Commands

### Build & Run
```bash
# Build image
docker build -f Dockerfile.collector -t vayuguard-aqi-collector .

# Run standalone
docker run -d \
  --name vayuguard-aqi-collector \
  -e WAQI_API_KEY=YOUR_KEY \
  -e DB_HOST=localhost \
  -v $(pwd)/data-pipeline/logs:/app/data-pipeline/logs \
  vayuguard-aqi-collector

# Use docker-compose
docker-compose up --build aqi-collector
```

### Monitor
```bash
# View logs
docker logs -f vayuguard-aqi-collector

# View collection logs
docker exec vayuguard-aqi-collector tail -f data-pipeline/logs/collector_*.log

# Check database from container
docker exec vayuguard-aqi-collector psql -h postgres -U vayuguard_user -d vayuguard \
  -c "SELECT COUNT(*) FROM aqi_data;"

# Stop container
docker stop vayuguard-aqi-collector

# Remove container
docker rm vayuguard-aqi-collector
```

---

## 📋 File Reference

| File | Purpose |
|------|---------|
| `collector.py` | Main service |
| `test_collector.py` | Test suite |
| `setup/setup_windows_task.py` | Windows deployment |
| `setup/setup_cron.sh` | Linux/macOS deployment |
| `setup/docker_deployment.py` | Docker guide |
| `Dockerfile.collector` | Container image |
| `QUICK_START.md` | 5-min guide |
| `DEPLOYMENT_GUIDE.md` | Complete guide |
| `PRODUCTION_SUMMARY.md` | Overview |
| `MANIFEST.md` | Checklist |
| `DATA_COLLECTION_REPORT.md` | Auto-generated report |

---

## 🔑 Environment Variables

```bash
# .env file (keep secret!)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=vayuguard
DB_USER=vayuguard_user
DB_PASSWORD=vayuguard_pass
WAQI_API_KEY=your_key_here
```

---

## 📞 Emergency Procedures

### Restart Collection
```bash
# Kill existing process
pkill -f "python collector.py"

# Restart
RUN_ONCE=1 python collector.py
```

### Clear Old Logs
```bash
# Archive and remove logs older than 90 days
find data-pipeline/logs/ -name "*.log" -mtime +90 -delete

# Archive to tarball
tar -czf logs_archive_$(date +%Y%m%d).tar.gz data-pipeline/logs/
```

### Reset Collection
```bash
# WARNING: This clears the database!
psql -U vayuguard_user -d vayuguard -c "TRUNCATE TABLE aqi_data;"

# Then restart collector
RUN_ONCE=1 python collector.py
```

---

## ✅ Health Check
```bash
#!/bin/bash
echo "=== VayuGuard Health Check ==="
echo "1. Database:"
psql -U vayuguard_user -d vayuguard -c "SELECT COUNT(*) FROM aqi_data;" || echo "FAIL"

echo "2. Logs:"
ls data-pipeline/logs/collector_*.log 2>/dev/null || echo "FAIL"

echo "3. API:"
curl -s https://api.waqi.info/feed/Chennai/?token=$WAQI_API_KEY | jq '.status' || echo "FAIL"

echo "4. Report:"
cat DATA_COLLECTION_REPORT.md | head -5 || echo "FAIL"

echo "Done!"
```

---

**Last Updated:** 2026-06-15  
**Version:** 1.0  
**Status:** ✅ PRODUCTION READY
