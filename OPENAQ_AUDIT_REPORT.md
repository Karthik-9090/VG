# OPENAQ AUDIT REPORT

**Generated:** 2026-06-15  
**Purpose:** Document all OpenAQ references for removal and WAQI migration  
**Status:** Complete

---

## EXECUTIVE SUMMARY

**Total OpenAQ References Found:** 145  
**Files Affected:** 28  
**Removal Recommendation:** YES - Replace with WAQI

---

## PHASE 1 - REPOSITORY AUDIT FINDINGS

### Category 1: Core Ingestion Code (MUST REMOVE/REFACTOR)

| File Path | Line(s) | Content | Usage | Can Remove? | Action |
|-----------|---------|---------|-------|------------|--------|
| [data-pipeline/config.py](data-pipeline/config.py#L15) | 15 | `OPENAQ_API_URL = 'https://api.openaq.org/v1/latest'` | Config constant | YES | Remove, replace with WAQI_API_URL |
| [data-pipeline/ingest_aqi.py](data-pipeline/ingest_aqi.py#L13) | 13 | `self.api_url = config.OPENAQ_API_URL` | API endpoint reference | YES | Refactor to use WAQI |
| [data-pipeline/scheduler.py](data-pipeline/scheduler.py#L27) | 27 | `log_ingestion(conn, 'openaq', aqi_results['successful'], 'completed')` | Data source logging | YES | Update to 'waqi' |

### Category 2: Test/Verification Scripts (CAN DELETE)

| File Path | Line(s) | Content | Usage | Can Remove? | Action |
|-----------|---------|---------|-------|------------|--------|
| [test_openaq_connection.py](test_openaq_connection.py) | - | Entire file | Tests OpenAQ v3 API | YES | DELETE - No longer needed |
| [find_sensors.py](find_sensors.py) | - | Entire file | Searches OpenAQ sensors | YES | DELETE - No longer needed |
| [find_sensors_coords.py](find_sensors_coords.py) | - | Entire file | Coordinate-based sensor search | YES | DELETE - No longer needed |

### Category 3: ML Training Code (MUST REFACTOR)

| File Path | Line(s) | Content | Usage | Can Remove? | Action |
|-----------|---------|---------|-------|------------|--------|
| [ml-service/train.py](ml-service/train.py#L30-L53) | 30-53 | `fetch_real_data_openaq()` method | Attempted real data fetch | YES | Remove, use PostgreSQL instead |
| [ml-service/train.py](ml-service/train.py#L38) | 38 | `url = f"https://api.openaq.org/v2/latest"` | API URL | YES | Remove, query database |

### Category 4: Deployment/Configuration (MUST UPDATE)

| File Path | Line(s) | Content | Usage | Can Remove? | Action |
|-----------|---------|---------|-------|------------|--------|
| [deploy.py](deploy.py#L130-L200) | 130-200 | OpenAQ references in deployment | Deployment config | PARTIAL | Remove OpenAQ, keep WAQI |
| [docker-compose.yml](docker-compose.yml#L130) | 130 | `OPENAQ_API_KEY: ${OPENAQ_API_KEY}` | Environment variable | YES | Remove env var |
| [deployment-config.json](deployment-config.json#L17,27) | 17, 27 | `"data_source": "OpenAQ"` | Config metadata | YES | Update to WAQI |
| [.env](.env) | - | `OPENAQ_API_KEY=...` | API key storage | YES | Remove line, keep WAQI_API_KEY |

### Category 5: Documentation (UPDATE ONLY)

| File Path | Lines | Type | Action |
|-----------|-------|------|--------|
| [README.md](README.md#L34,70,80) | 34, 70, 80 | Main README | Replace OpenAQ with WAQI |
| [OPENAQ_CONNECTION_REPORT.md](OPENAQ_CONNECTION_REPORT.md) | All | Report | Archive/delete (superseded by WAQI) |
| [INGESTION_VERIFICATION_REPORT.md](INGESTION_VERIFICATION_REPORT.md) | Multiple | Report | Update with WAQI findings |
| docs/archived/ARCHITECTURE.md | 6, 18 | Architecture docs | Update references |
| docs/archived/BLUEPRINT_COMPLIANCE_REPORT.md | 36, 43, 735 | Compliance docs | Archive |
| docs/archived/COMPLETION_REPORT.md | 301 | Completion docs | Archive |
| docs/archived/IMPLEMENTATION.md | 71 | Implementation docs | Archive |
| docs/archived/PRODUCTION_READINESS_ASSESSMENT.md | Multiple | Assessment docs | Archive |
| docs/archived/PRODUCTION_AUDIT_REPORT.md | 90, 92, 388, 605 | Audit docs | Archive |
| docs/archived/REAL_DATA_SETUP.md | Multiple | Setup guide | Archive |
| docs/archived/TEST_EXECUTION_REPORT.md | 125, 153 | Test report | Archive |
| docs/archived/V2_UPGRADE_COMPLETE.md | Multiple | Upgrade docs | Archive |
| docs/archived/VERIFICATION_COMPLETE.md | 39, 369 | Verification docs | Archive |

### Category 6: Configuration Files (UPDATE)

| File Path | Property | Current Value | New Value | Action |
|-----------|----------|----------------|-----------|--------|
| [data-pipeline/config.py](data-pipeline/config.py) | OPENAQ_API_URL | `https://api.openaq.org/v1/latest` | DELETE | Remove constant |
| [data-pipeline/config.py](data-pipeline/config.py) | - | (add) | `WAQI_API_URL = 'https://api.waqi.info/feed'` | Add WAQI config |

---

## PHASE 2 - IMPACT ANALYSIS

### Direct Dependencies

```
config.py
├── OPENAQ_API_URL (used by ingest_aqi.py)
├── OPENAQ_API_KEY (from .env)
└── CITIES, CITY_COORDS (used for ingestion)

ingest_aqi.py
├── config.OPENAQ_API_URL
├── config.MAX_RETRIES
└── config.RETRY_BACKOFF

scheduler.py
├── ingest_aqi.AQIIngestor
└── log_ingestion() with 'openaq' source

train.py (ml-service)
├── fetch_real_data_openaq() method
└── Fallback to synthetic data
```

### Indirect Dependencies

- docker-compose.yml passes OPENAQ_API_KEY env var
- deploy.py tries to run openaq_fetcher.py (already deleted)
- Multiple archived docs reference OpenAQ

---

## PHASE 3 - REMOVAL STRATEGY

### Safe to Delete Immediately (No Dependencies)

1. [test_openaq_connection.py](test_openaq_connection.py) - Test file only
2. [find_sensors.py](find_sensors.py) - Exploration script only
3. [find_sensors_coords.py](find_sensors_coords.py) - Exploration script only

### Must Refactor Before Deleting

1. [data-pipeline/ingest_aqi.py](data-pipeline/ingest_aqi.py) - Core ingestion
   - Replace with WAQI API calls
   - Maintain same insert interface

2. [ml-service/train.py](ml-service/train.py) - Training pipeline
   - Remove fetch_real_data_openaq()
   - Use PostgreSQL directly

### Must Update (Keep Core Functionality)

1. [data-pipeline/config.py](data-pipeline/config.py) - Configuration
   - Remove OPENAQ_API_URL
   - Add WAQI_API_URL and WAQI_API_KEY

2. [docker-compose.yml](docker-compose.yml) - Orchestration
   - Remove OPENAQ_API_KEY env var
   - Add WAQI_API_KEY env var

3. [.env](.env) - Local environment
   - Remove OPENAQ_API_KEY
   - Add WAQI_API_KEY (from user setup)

---

## SUMMARY TABLE

| Category | Count | Action | Files |
|----------|-------|--------|-------|
| **Delete** | 3 | Remove entirely | test_openaq_connection.py, find_sensors.py, find_sensors_coords.py |
| **Refactor** | 2 | Rewrite with WAQI | ingest_aqi.py, train.py |
| **Update Config** | 4 | Modify content | config.py, docker-compose.yml, .env, deployment-config.json |
| **Update Docs** | 1 | Update main docs | README.md |
| **Archive Docs** | 12 | Move to archive | Various docs (already in docs/archived/) |

---

## NEXT STEPS (PHASE 2)

Proceed with:
1. Creating WAQI integration code
2. Refactoring ingest_aqi.py to use WAQI
3. Updating config.py with WAQI settings
4. Deleting obsolete test files
5. Updating README.md
6. Verifying all OpenAQ references removed

**Estimated Changes:** 8-10 files modified, 3 files deleted, 1 main documentation updated

---

**Report Status:** COMPLETE - Ready for Phase 2 execution
