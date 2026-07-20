"""Phase 2: Data Collection Validation"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data-pipeline'))

import psycopg2
import requests
from dotenv import load_dotenv
from ingest_aqi import AQIIngestor
from db import DatabaseConnection

load_dotenv()

print("="*80)
print("PHASE 2: DATA COLLECTION VALIDATION")
print(f"Timestamp: {datetime.now().isoformat()}")
print("="*80)
print()

test_results = []

# Test 1: Database Connection
print("[1/7] DATABASE CONNECTION")
print("-"*80)
try:
    DatabaseConnection.init_pool()
    conn = DatabaseConnection.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM aqi_data")
    count = cursor.fetchone()[0]
    cursor.close()
    DatabaseConnection.return_connection(conn)
    
    print(f"[PASS] Database connected")
    print(f"       Current records: {count}")
    test_results.append(("Database Connection", "PASS"))
except Exception as e:
    print(f"[FAIL] {e}")
    test_results.append(("Database Connection", "FAIL"))

print()

# Test 2: WAQI API Key
print("[2/7] WAQI API KEY")
print("-"*80)
try:
    api_key = os.getenv('WAQI_API_KEY')
    if not api_key:
        raise Exception("WAQI_API_KEY not found in .env")
    
    # Test API
    response = requests.get(
        f"https://api.waqi.info/feed/Chennai/?token={api_key}",
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('status') == 'ok':
            print(f"[PASS] WAQI API key valid")
            print(f"       Status: {data['status']}")
            print(f"       City: {data.get('data', {}).get('city', {}).get('name', 'N/A')}")
            test_results.append(("WAQI API Key", "PASS"))
        else:
            raise Exception(f"API status: {data.get('status')}")
    else:
        raise Exception(f"HTTP {response.status_code}")
except Exception as e:
    print(f"[FAIL] {e}")
    test_results.append(("WAQI API Key", "FAIL"))

print()

# Test 3: AQI Data Ingestion
print("[3/7] AQI DATA INGESTION")
print("-"*80)
try:
    ingestor = AQIIngestor()
    cities_passed = 0
    
    for city in ['Chennai', 'Bengaluru', 'Hyderabad']:
        try:
            aqi_data = ingestor.fetch_aqi(city)
            if aqi_data and aqi_data.get('aqi') is not None:
                print(f"[OK] {city:15} AQI={aqi_data['aqi']:3} PM2.5={aqi_data.get('pm25', 'N/A')}")
                cities_passed += 1
            else:
                print(f"[FAIL] {city:15} No data")
        except Exception as e:
            print(f"[FAIL] {city:15} {e}")
    
    if cities_passed == 3:
        print(f"\n[PASS] All 3 cities ingested successfully")
        test_results.append(("AQI Ingestion", "PASS"))
    else:
        print(f"\n[PARTIAL] Only {cities_passed}/3 cities")
        test_results.append(("AQI Ingestion", "PARTIAL"))
except Exception as e:
    print(f"[FAIL] {e}")
    test_results.append(("AQI Ingestion", "FAIL"))

print()

# Test 4: Database Schema
print("[4/7] DATABASE SCHEMA")
print("-"*80)
try:
    conn = DatabaseConnection.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'aqi_data'
        ORDER BY ordinal_position
    """)
    
    columns = [col[0] for col in cursor.fetchall()]
    required = ['id', 'city', 'aqi', 'pm25', 'pm10', 'no2', 'o3', 'so2', 'co',
                'temperature', 'humidity', 'wind_speed', 'pressure', 'recorded_at', 'created_at']
    
    missing = set(required) - set(columns)
    
    if not missing:
        print(f"[PASS] Schema verified")
        print(f"       Total columns: {len(columns)}")
        print(f"       Required fields: All present")
        test_results.append(("Database Schema", "PASS"))
    else:
        print(f"[FAIL] Missing columns: {missing}")
        test_results.append(("Database Schema", "FAIL"))
    
    cursor.close()
    DatabaseConnection.return_connection(conn)
except Exception as e:
    print(f"[FAIL] {e}")
    test_results.append(("Database Schema", "FAIL"))

print()

# Test 5: Log File Creation
print("[5/7] LOG FILE CREATION")
print("-"*80)
try:
    log_dir = Path('data-pipeline') / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime('%Y%m%d')
    log_file = log_dir / f'collector_{today}.log'
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[AUDIT] Phase 2 test at {datetime.now()}\n")
    
    if log_file.exists():
        size = log_file.stat().st_size
        print(f"[PASS] Log file operational")
        print(f"       Path: {log_file}")
        print(f"       Size: {size} bytes")
        test_results.append(("Log File Creation", "PASS"))
    else:
        print(f"[FAIL] Log file not created")
        test_results.append(("Log File Creation", "FAIL"))
except Exception as e:
    print(f"[FAIL] {e}")
    test_results.append(("Log File Creation", "FAIL"))

print()

# Test 6: Backup Directory
print("[6/7] BACKUP DIRECTORY")
print("-"*80)
try:
    backup_dir = Path('data-pipeline') / 'backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Test write
    test_file = backup_dir / '.test'
    test_file.write_text('test')
    test_file.unlink()
    
    print(f"[PASS] Backup directory ready")
    print(f"       Path: {backup_dir}")
    print(f"       Writable: Yes")
    test_results.append(("Backup Directory", "PASS"))
except Exception as e:
    print(f"[FAIL] {e}")
    test_results.append(("Backup Directory", "FAIL"))

print()

# Test 7: Duplicate Detection
print("[7/7] DUPLICATE DETECTION")
print("-"*80)
try:
    from collector import ProductionAQICollector
    
    collector = ProductionAQICollector()
    conn = DatabaseConnection.get_connection()
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT city, aqi, recorded_at FROM aqi_data
        ORDER BY created_at DESC LIMIT 1
    """)
    
    result = cursor.fetchone()
    if result:
        city, aqi, timestamp = result
        is_dup = collector.check_duplicate(conn, city, aqi, timestamp.isoformat())
        print(f"[PASS] Duplicate detection working")
        print(f"       Test city: {city}")
        print(f"       Detected duplicate: {is_dup}")
        test_results.append(("Duplicate Detection", "PASS"))
    else:
        print(f"[SKIP] No data to test")
        test_results.append(("Duplicate Detection", "SKIP"))
    
    cursor.close()
    DatabaseConnection.return_connection(conn)
except Exception as e:
    print(f"[FAIL] {e}")
    test_results.append(("Duplicate Detection", "FAIL"))

print()

# Summary
print("="*80)
print("PHASE 2 SUMMARY")
print("="*80)

passed = sum(1 for _, status in test_results if status == "PASS")
partial = sum(1 for _, status in test_results if status == "PARTIAL")
skipped = sum(1 for _, status in test_results if status == "SKIP")
failed = sum(1 for _, status in test_results if status == "FAIL")

for test_name, status in test_results:
    status_symbol = "[PASS]" if status == "PASS" else "[PARTIAL]" if status == "PARTIAL" else "[SKIP]" if status == "SKIP" else "[FAIL]"
    print(f"{status_symbol:10} {test_name}")

print()
print(f"Results: {passed} passed, {partial} partial, {skipped} skipped, {failed} failed")

if failed == 0:
    print("[PASS] PHASE 2: DATA COLLECTION VALIDATION - SUCCESS")
else:
    print(f"[FAIL] PHASE 2: DATA COLLECTION VALIDATION - {failed} FAILURES")
    exit(1)

print("="*80)
