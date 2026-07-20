#!/usr/bin/env python3
"""
Phase A: API Runtime Validation

Tests:
- POST /forecast with real payloads
- Model loading verification
- Prediction logging verification
"""

import requests
import json
import time
from datetime import datetime
import psycopg2

# API Configuration
API_BASE = "http://localhost:8000"

# Database Configuration
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "vayuguard"
DB_USER = "postgres"
DB_PASSWORD = ""

print("=" * 80)
print("PHASE A - API RUNTIME VALIDATION")
print("=" * 80)
print()

# Test data for each city
test_payloads = {
    "Chennai": {
        "city": "Chennai",
        "aqi": 120,
        "pm2_5": 80,
        "pm10": 95,
        "no2": 22,
        "so2": 8,
        "co": 1.2,
        "o3": 30
    },
    "Bengaluru": {
        "city": "Bengaluru",
        "aqi": 95,
        "pm2_5": 65,
        "pm10": 78,
        "no2": 18,
        "so2": 6,
        "co": 0.9,
        "o3": 28
    },
    "Hyderabad": {
        "city": "Hyderabad",
        "aqi": 110,
        "pm2_5": 72,
        "pm10": 88,
        "no2": 20,
        "so2": 7,
        "co": 1.0,
        "o3": 32
    }
}

# Results
results = {
    "timestamp": datetime.now().isoformat(),
    "api_health": None,
    "predictions": {},
    "database_logs": {}
}

# STEP 1: Check API Health
print("STEP 1: Checking API health...")
try:
    response = requests.get(f"{API_BASE}/health", timeout=5)
    health_data = response.json()
    results["api_health"] = health_data
    
    print(f"[OK] API responding")
    print(f"     Status: {health_data.get('status')}")
    print(f"     Model Loaded: {health_data.get('model_loaded')}")
    print(f"     Model Version: {health_data.get('model_version')}")
    print(f"     Database Status: {health_data.get('database_status')}")
except Exception as e:
    print(f"[ERROR] API health check failed: {e}")
    results["api_health"] = {"error": str(e)}

print()

# STEP 2: Get baseline prediction count
print("STEP 2: Baseline prediction count...")
try:
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM prediction_logs")
    baseline_count = cursor.fetchone()[0]
    conn.close()
    print(f"[OK] Baseline: {baseline_count} predictions logged")
except Exception as e:
    print(f"[WARNING] Could not get baseline: {e}")
    baseline_count = 0

print()

# STEP 3: Execute POST /forecast requests
print("STEP 3: Executing POST /forecast requests...")
prediction_ids = []

for city, payload in test_payloads.items():
    print()
    print(f"  Testing: {city}")
    print(f"  Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(f"{API_BASE}/forecast", json=payload, timeout=10)
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            results["predictions"][city] = {
                "status": "SUCCESS",
                "response": data,
                "latency_ms": latency_ms,
                "timestamp": datetime.now().isoformat()
            }
            prediction_ids.append(data.get("prediction_id"))
            
            print(f"  [OK] Prediction successful")
            print(f"       Forecast AQI: {data.get('forecast_aqi')}")
            print(f"       Model: {data.get('model')}")
            print(f"       Version: {data.get('version')}")
            print(f"       Latency: {latency_ms:.1f}ms")
            print(f"       Prediction ID: {data.get('prediction_id')}")
        else:
            print(f"  [ERROR] HTTP {response.status_code}")
            print(f"  Response: {response.text}")
            results["predictions"][city] = {
                "status": "FAILED",
                "error": f"HTTP {response.status_code}",
                "response": response.text
            }
    except Exception as e:
        print(f"  [ERROR] Request failed: {e}")
        results["predictions"][city] = {
            "status": "ERROR",
            "error": str(e)
        }

print()

# STEP 4: Verify predictions logged to database
print("STEP 4: Verifying predictions logged to database...")
time.sleep(1)  # Give DB time to write

try:
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    cursor = conn.cursor()
    
    # Get new predictions
    cursor.execute("""
        SELECT id, city, input_aqi, predicted_aqi, model_version, timestamp, latency_ms
        FROM prediction_logs
        WHERE timestamp > NOW() - INTERVAL '1 minute'
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    
    logged_predictions = cursor.fetchall()
    results["database_logs"]["count"] = len(logged_predictions)
    results["database_logs"]["predictions"] = []
    
    for row in logged_predictions:
        pred_id, city, input_aqi, predicted_aqi, model_version, timestamp, latency_ms = row
        results["database_logs"]["predictions"].append({
            "id": int(pred_id),
            "city": city,
            "input_aqi": float(input_aqi) if input_aqi else None,
            "predicted_aqi": float(predicted_aqi),
            "model_version": model_version,
            "timestamp": timestamp.isoformat() if timestamp else None,
            "latency_ms": float(latency_ms) if latency_ms else None
        })
        
        print(f"[OK] Logged: {city} - Prediction: {predicted_aqi:.2f}, Latency: {latency_ms:.1f}ms")
    
    conn.close()
    
    if len(logged_predictions) == len(test_payloads):
        print(f"[OK] All {len(test_payloads)} predictions logged successfully")
    else:
        print(f"[WARNING] Expected {len(test_payloads)} but found {len(logged_predictions)}")
        
except Exception as e:
    print(f"[ERROR] Database verification failed: {e}")
    results["database_logs"]["error"] = str(e)

print()

# STEP 5: API Endpoints test
print("STEP 5: Testing GET /metrics endpoint...")
try:
    response = requests.get(f"{API_BASE}/metrics", timeout=5)
    if response.status_code == 200:
        metrics = response.json()
        results["metrics"] = metrics
        print(f"[OK] Metrics endpoint responding")
        print(f"     Total Requests: {metrics.get('total_requests')}")
        print(f"     Total Predictions: {metrics.get('total_predictions')}")
        print(f"     Average Latency: {metrics.get('average_latency_ms'):.2f}ms")
    else:
        print(f"[ERROR] HTTP {response.status_code}")
except Exception as e:
    print(f"[ERROR] Metrics endpoint failed: {e}")

print()

# STEP 6: Summary
print("=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)

all_passed = True

# Check API health
if results["api_health"] and results["api_health"].get("model_loaded"):
    print("[PASS] Model loading - Model loaded successfully")
else:
    print("[FAIL] Model loading - Model not loaded")
    all_passed = False

# Check predictions
successful_predictions = sum(1 for p in results["predictions"].values() if p.get("status") == "SUCCESS")
if successful_predictions == len(test_payloads):
    print(f"[PASS] Predictions generated - All {len(test_payloads)} cities predicted successfully")
else:
    print(f"[FAIL] Predictions generated - Only {successful_predictions}/{len(test_payloads)} successful")
    all_passed = False

# Check database logging
if results["database_logs"].get("count", 0) == len(test_payloads):
    print(f"[PASS] Database logging - All predictions logged to database")
else:
    print(f"[FAIL] Database logging - {results['database_logs'].get('count', 0)} predictions logged (expected {len(test_payloads)})")
    all_passed = False

print()

# Save results
with open("api_validation_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"[OK] Results saved to api_validation_results.json")
print()

# Final status
if all_passed:
    print("[PASS] PHASE A VALIDATION SUCCESSFUL")
else:
    print("[FAIL] PHASE A VALIDATION - SOME CHECKS FAILED")

print()
