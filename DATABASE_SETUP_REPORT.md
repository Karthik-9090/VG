# Database Setup Report - VayuGuard

**Date:** 2026-06-15  
**Status:** ✅ **OPERATIONAL**  
**PostgreSQL Version:** 18.4  
**Database Name:** vayuguard  

---

## 1. PostgreSQL Installation

### System Configuration
- **OS:** Windows 11
- **PostgreSQL Installation Path:** `C:\Program Files\PostgreSQL\18\bin`
- **PostgreSQL Version:** 18.4 (x86_64-windows, msvc-19.44.35226)
- **Installation Method:** WinGet (`winget install PostgreSQL.PostgreSQL.18`)

### Verification
```
psql --version
→ psql (PostgreSQL) 18.4 ✓
```

---

## 2. Database & User Creation

The database and user were pre-configured. Verification confirms:

```sql
CREATE DATABASE vayuguard WITH ENCODING 'UTF8';
CREATE USER vayuguard_user WITH PASSWORD 'vayuguard_pass';
ALTER ROLE vayuguard_user WITH CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE vayuguard TO vayuguard_user;
```

**Verification Result:**
```
Connected User: vayuguard_user ✓
Connected Database: vayuguard ✓
Connection Timestamp: 2026-06-15 20:51:23.309501+05:30 ✓
```

---

## 3. Schema Initialization

### Source File
- **File:** [infra/schema.sql](infra/schema.sql)
- **Status:** ✅ Executed successfully
- **Execution Method:** `psql -U postgres -h localhost -d vayuguard -f infra/schema.sql`

### Schema Modifications Made
Fixed PostgreSQL syntax errors in the original schema definition:

**Issue 1:** Inline INDEX syntax (MySQL-style)
```sql
-- BEFORE (invalid in PostgreSQL):
CREATE TABLE aqi_data (
  id SERIAL PRIMARY KEY,
  city VARCHAR(100) NOT NULL,
  aqi INT NOT NULL,
  category aqi_category,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX_aqi (city, timestamp)  -- ❌ Invalid syntax
);

-- AFTER (valid PostgreSQL):
CREATE TABLE aqi_data (
  id SERIAL PRIMARY KEY,
  city VARCHAR(100) NOT NULL,
  aqi INT NOT NULL,
  category aqi_category,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Indexes created separately with CREATE INDEX
```

**Issue 2:** Similar fix applied to weather_data table

**Changes Made:** [infra/schema.sql](infra/schema.sql#L45-L53) and [infra/schema.sql](infra/schema.sql#L56-L64)

---

## 4. Database Tables

### Summary
✅ **All 8 tables created successfully**

| Table Name | Rows | Status |
|---|---|---|
| users | 0 | Ready |
| health_profiles | 0 | Ready |
| aqi_data | 0 | Ready |
| weather_data | 0 | Ready |
| forecasts | 0 | Ready |
| alerts | 0 | Ready |
| model_metadata | 0 | Ready |
| ingestion_logs | 0 | Ready |

### Detailed Schema

#### Table 1: users
```
Column       | Type                    | Constraints
------       | ----                    | -----------
id           | SERIAL PRIMARY KEY      | Auto-increment
email        | VARCHAR(255) NOT NULL   | UNIQUE index (idx_users_email)
password_hash| VARCHAR(255) NOT NULL   | Hashed passwords
name         | VARCHAR(255) NOT NULL   | User display name
role         | user_role               | DEFAULT 'user'
created_at   | TIMESTAMP               | DEFAULT CURRENT_TIMESTAMP
updated_at   | TIMESTAMP               | DEFAULT CURRENT_TIMESTAMP

Indexes:
- users_pkey (id)
- users_email_key (email UNIQUE)
- idx_users_email (email)

Foreign Keys Referenced By:
- alerts.user_id (ON DELETE CASCADE)
- health_profiles.user_id (ON DELETE CASCADE)
```

#### Table 2: health_profiles
```
Column       | Type                    | Constraints
------       | ----                    | -----------
id           | SERIAL PRIMARY KEY      | Auto-increment
user_id      | INTEGER NOT NULL        | FK → users(id) CASCADE
profile_type | health_profile_type     | Profile category
created_at   | TIMESTAMP               | DEFAULT CURRENT_TIMESTAMP

Constraints:
- UNIQUE(user_id, profile_type) - One profile type per user

Valid Profile Types: general, respiratory, cardiac, children, elderly
```

#### Table 3: aqi_data
```
Column     | Type                    | Constraints
------     | ----                    | -----------
id         | SERIAL PRIMARY KEY      | Auto-increment
city       | VARCHAR(100) NOT NULL   | City name
aqi        | INT NOT NULL            | AQI value (0-500+)
category   | aqi_category            | Categorical rating
timestamp  | TIMESTAMP               | DEFAULT CURRENT_TIMESTAMP

Indexes:
- aqi_data_pkey (id)
- idx_aqi_city_time (city, timestamp DESC) ← Performance index

Valid Categories: Good, Satisfactory, Moderately Polluted, Heavily Polluted, Severely Polluted
```

#### Table 4: weather_data
```
Column     | Type                    | Constraints
------     | ----                    | -----------
id         | SERIAL PRIMARY KEY      | Auto-increment
city       | VARCHAR(100) NOT NULL   | City name
temperature| FLOAT                   | Celsius
humidity   | FLOAT                   | Percentage
wind_speed | FLOAT                   | km/h
timestamp  | TIMESTAMP               | DEFAULT CURRENT_TIMESTAMP

Indexes:
- weather_data_pkey (id)
- idx_weather_city_time (city, timestamp DESC) ← Performance index
```

#### Table 5: forecasts
```
Column       | Type                    | Constraints
------       | ----                    | -----------
id           | SERIAL PRIMARY KEY      | Auto-increment
city         | VARCHAR(100) NOT NULL   | City name
horizon_hours| INT                     | Hours ahead (24, 48, 72)
forecast_data| JSONB                   | Raw forecast data
model_used   | VARCHAR(100)            | ML model version
created_at   | TIMESTAMP               | DEFAULT CURRENT_TIMESTAMP
valid_until  | TIMESTAMP               | Forecast expiry

Indexes:
- forecasts_pkey (id)
- idx_forecasts_city_time (city, created_at DESC) ← Performance index
```

#### Table 6: alerts
```
Column       | Type                    | Constraints
------       | ----                    | -----------
id           | SERIAL PRIMARY KEY      | Auto-increment
user_id      | INTEGER NOT NULL        | FK → users(id) CASCADE
city         | VARCHAR(100) NOT NULL   | City name
alert_type   | alert_type              | Alert category
comparison   | alert_comparison        | Comparison operator
threshold    | INT                     | Alert threshold value
is_active    | BOOLEAN                 | Alert status
created_at   | TIMESTAMP               | DEFAULT CURRENT_TIMESTAMP
updated_at   | TIMESTAMP               | DEFAULT CURRENT_TIMESTAMP

Indexes:
- alerts_pkey (id)
- idx_alerts_user (user_id) ← Foreign key index

Valid Alert Types: aqi_threshold, health_risk
Valid Comparisons: gt (>), lt (<), eq (=)
```

#### Table 7: model_metadata
```
Column          | Type                    | Constraints
------          | ----                    | -----------
id              | SERIAL PRIMARY KEY      | Auto-increment
model_name      | VARCHAR(100) NOT NULL   | Model identifier
model_version   | VARCHAR(50)             | Version string
performance_metrics| JSONB                | Accuracy, precision, recall, etc.
created_at      | TIMESTAMP               | DEFAULT CURRENT_TIMESTAMP
last_updated    | TIMESTAMP               | Last training time

Indexes:
- model_metadata_pkey (id)
```

#### Table 8: ingestion_logs
```
Column          | Type                    | Constraints
------          | ----                    | -----------
id              | SERIAL PRIMARY KEY      | Auto-increment
data_source     | VARCHAR(100)            | API or file source
records_ingested| INT                     | Count of records
status          | VARCHAR(50)             | 'success' or 'error'
error_message   | TEXT                    | Error details if failed
created_at      | TIMESTAMP               | DEFAULT CURRENT_TIMESTAMP

Indexes:
- ingestion_logs_pkey (id)
```

---

## 5. Custom Data Types (Enums)

✅ **All 5 enum types created successfully**

### Enum Definitions

#### 1. user_role
```
Values: admin, user
Usage: users.role (DEFAULT: 'user')
```

#### 2. health_profile_type
```
Values: general, respiratory, cardiac, children, elderly
Usage: health_profiles.profile_type
```

#### 3. aqi_category
```
Values:
  - Good
  - Satisfactory
  - Moderately Polluted
  - Heavily Polluted
  - Severely Polluted
Usage: aqi_data.category
```

#### 4. alert_type
```
Values: aqi_threshold, health_risk
Usage: alerts.alert_type
```

#### 5. alert_comparison
```
Values: gt (greater than), lt (less than), eq (equals)
Usage: alerts.comparison
```

---

## 6. Indexes & Performance

### Summary
✅ **15 indexes created (8 primary keys + 5 performance indexes + 2 unique constraints)**

### Performance Indexes

| Index Name | Table | Columns | Type | Purpose |
|---|---|---|---|---|
| idx_aqi_city_time | aqi_data | (city, timestamp DESC) | BTREE | Query by city + time |
| idx_weather_city_time | weather_data | (city, timestamp DESC) | BTREE | Query by city + time |
| idx_forecasts_city_time | forecasts | (city, created_at DESC) | BTREE | Query by city + creation time |
| idx_alerts_user | alerts | (user_id) | BTREE | Foreign key lookup |
| idx_users_email | users | (email) | BTREE | Email lookup |

### Unique Constraints

| Constraint | Table | Columns | Purpose |
|---|---|---|---|
| users_email_key | users | (email) | Prevent duplicate emails |
| health_profiles_user_id_profile_type_key | health_profiles | (user_id, profile_type) | One profile type per user |

---

## 7. Connection Verification

### Backend Connection Test
```sql
SELECT version() as postgresql_version,
       current_user as connected_user,
       current_database() as connected_db,
       NOW() as current_timestamp;
```

**Result:**
```
postgresql_version: PostgreSQL 18.4 on x86_64-windows, compiled by msvc-19.44.35226, 64-bit ✓
connected_user: vayuguard_user ✓
connected_db: vayuguard ✓
current_timestamp: 2026-06-15 20:51:23.309501+05:30 ✓
```

### Connection String
```
Host: localhost (or 127.0.0.1)
Port: 5432 (default PostgreSQL port)
Database: vayuguard
User: vayuguard_user
Password: vayuguard_pass

Connection URL (Node.js pg):
postgres://vayuguard_user:vayuguard_pass@localhost:5432/vayuguard

Connection URL (Python psycopg2):
postgresql://vayuguard_user:vayuguard_pass@localhost:5432/vayuguard
```

---

## 8. Row Count Summary

All tables initialized with zero rows and ready to receive data:

```
users               : 0 rows
health_profiles     : 0 rows
aqi_data            : 0 rows
weather_data        : 0 rows
forecasts           : 0 rows
alerts              : 0 rows
model_metadata      : 0 rows
ingestion_logs      : 0 rows
─────────────────────────────
TOTAL               : 0 rows
```

---

## 9. Docker Compose Configuration

For containerized deployment, docker-compose.yml includes automatic schema initialization:

```yaml
postgres:
  image: postgres:15
  container_name: vayuguard-postgres
  environment:
    POSTGRES_DB: vayuguard
    POSTGRES_USER: vayuguard_user
    POSTGRES_PASSWORD: vayuguard_pass
    POSTGRES_INITDB_ARGS: "-c max_connections=100"
  volumes:
    - pgdata:/var/lib/postgresql/data
    - ./infra/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
  ports:
    - '5432:5432'
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U vayuguard_user -d vayuguard"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 10s
```

**Key Features:**
- ✅ Auto-executes `schema.sql` on first startup via `/docker-entrypoint-initdb.d/01-schema.sql`
- ✅ Health checks verify PostgreSQL readiness before dependent services start
- ✅ Volume mapping persists data across container restarts
- ✅ Connection pooling configured (`max_connections=100`)

---

## 10. Next Steps

### Phase 2: Data Ingestion
1. Execute `data-pipeline/scheduler.py` to ingest OpenAQ and Open-Meteo data
2. Verify rows inserted into:
   - aqi_data (expected: ~100+ records per run)
   - weather_data (expected: ~100+ records per run)
   - ingestion_logs (expected: 1 success record per run)

### Phase 3: ML Model Training
1. Train forecasting model on historical aqi_data + weather_data
2. Insert model metadata and performance metrics into model_metadata table
3. Generate hourly forecasts and populate forecasts table

### Phase 4: Backend Service
1. Verify `backend/server.js` connects successfully with connection string
2. Enable `/api/analytics` to query aggregated data
3. Enable `/api/alerts` to manage user alerts against aqi_data thresholds

### Phase 5: Frontend Integration
1. Update `frontend/src/pages/Map.jsx` to fetch live aqi_data instead of mock data
2. Update `frontend/src/pages/Analytics.jsx` to fetch from `/api/analytics`
3. Update health advisory rankings based on user health_profiles

---

## 11. Troubleshooting

### Issue: "column does not exist" in schema.sql
**Solution:** PostgreSQL doesn't support inline INDEX syntax like MySQL. Define indexes separately using `CREATE INDEX` statements. ✅ Fixed in [infra/schema.sql](infra/schema.sql)

### Issue: psql output pagination fails on Windows
**Solution:** Use `-P pager=off` flag to disable paging:
```powershell
psql -U postgres -h localhost -d vayuguard -P pager=off -c "SELECT * FROM users;"
```

### Issue: Docker Desktop not available
**Solution:** Use local PostgreSQL 18 installation. Schema initialization works identically whether run in Docker or locally.

### Issue: PGPASSWORD not recognized
**Solution:** On PowerShell, use `$env:PGPASSWORD = "password"` syntax instead of export.

---

## 12. Verification Checklist

- ✅ PostgreSQL 18.4 installed and running
- ✅ Database `vayuguard` created
- ✅ User `vayuguard_user` created with proper permissions
- ✅ All 8 tables created with correct schema
- ✅ All 5 enum types created with correct values
- ✅ All 15 indexes created (8 PKs + 5 performance + 2 unique constraints)
- ✅ All foreign keys configured with CASCADE delete
- ✅ Schema syntax validated (fixed MySQL → PostgreSQL conversions)
- ✅ Connection test passed with vayuguard_user credentials
- ✅ All tables empty and ready for data ingestion
- ✅ docker-compose.yml configured for automatic schema initialization

---

## 13. Files Modified

| File | Changes | Status |
|---|---|---|
| [infra/schema.sql](infra/schema.sql) | Removed inline INDEX syntax from aqi_data and weather_data tables | ✅ Fixed |
| docker-compose.yml | Added volume mapping for schema.sql auto-initialization | ✅ Already configured |

---

**Report Generated:** 2026-06-15 20:51:23  
**Database Status:** ✅ **FULLY OPERATIONAL**  
**Ready for:** Data ingestion, model training, backend integration

