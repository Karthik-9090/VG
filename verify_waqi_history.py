#!/usr/bin/env python3
"""
Verify WAQI Historical Data Availability
Tests actual API endpoints and download mechanisms for Chennai, Bengaluru, Hyderabad
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import sys

# Configuration
CITIES = ["Chennai", "Bengaluru", "Hyderabad"]
WAQI_API_BASE = "http://api.waqi.info"
WAQI_TOKEN = "demo"  # Public demo token

# Test endpoints and mechanisms
TEST_CONFIG = {
    "api_endpoints": [
        # Current data endpoint
        f"{WAQI_API_BASE}/feed/{{city}}/?token={WAQI_TOKEN}",
        # Try city names with comma-separated variations
        f"{WAQI_API_BASE}/feed/Chennai,India/?token={WAQI_TOKEN}",
        f"{WAQI_API_BASE}/feed/Bengaluru,India/?token={WAQI_TOKEN}",
        f"{WAQI_API_BASE}/feed/Hyderabad,India/?token={WAQI_TOKEN}",
    ],
    "search_endpoints": [
        # Search API if available
        f"{WAQI_API_BASE}/search/?keyword={{city}}&token={WAQI_TOKEN}",
    ],
    "historical_endpoints": [
        # Try historical data endpoints
        f"{WAQI_API_BASE}/history/{{city}}/?token={WAQI_TOKEN}",
        f"{WAQI_API_BASE}/data/{{city}}/?token={WAQI_TOKEN}",
    ],
}

results = {
    "timestamp": datetime.now().isoformat(),
    "test_results": {},
    "findings": [],
    "csv_availability": {},
    "historical_availability": False,
    "conclusion": ""
}

def test_api_endpoint(url: str, timeout: int = 10) -> Tuple[bool, dict, str]:
    """Test a single API endpoint"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            try:
                data = response.json()
                return True, data, ""
            except json.JSONDecodeError as e:
                return False, {}, f"Invalid JSON response: {str(e)}"
        else:
            return False, {}, f"HTTP {response.status_code}: {response.text[:200]}"
    except requests.exceptions.Timeout:
        return False, {}, "Request timeout"
    except requests.exceptions.ConnectionError as e:
        return False, {}, f"Connection error: {str(e)}"
    except Exception as e:
        return False, {}, f"Error: {str(e)}"

def analyze_response(data: dict) -> dict:
    """Analyze API response for historical data indicators"""
    analysis = {
        "has_data": False,
        "data_type": "unknown",
        "oldest_record": None,
        "newest_record": None,
        "record_count": 0,
        "is_historical": False,
        "fields_present": []
    }
    
    if not data:
        return analysis
    
    # Check if it's a feed response (current data)
    if data.get("status") == "ok" and data.get("data"):
        analysis["has_data"] = True
        analysis["data_type"] = "current_feed"
        
        feed_data = data["data"]
        if isinstance(feed_data, dict):
            analysis["fields_present"] = list(feed_data.keys())
            
            # Check for time information
            if "time" in feed_data:
                time_info = feed_data["time"]
                if isinstance(time_info, dict) and "s" in time_info:
                    analysis["newest_record"] = time_info["s"]
                    analysis["record_count"] = 1
            
            # Check for historical field
            if "history" in feed_data:
                analysis["is_historical"] = True
                if isinstance(feed_data["history"], list):
                    analysis["record_count"] = len(feed_data["history"])
                    if len(feed_data["history"]) > 0:
                        analysis["oldest_record"] = feed_data["history"][-1].get("time") if isinstance(feed_data["history"][-1], dict) else None
                        analysis["newest_record"] = feed_data["history"][0].get("time") if isinstance(feed_data["history"][0], dict) else None
    
    # Check if it's a search response
    elif data.get("status") == "ok" and data.get("results"):
        analysis["data_type"] = "search_results"
        if isinstance(data["results"], list):
            analysis["record_count"] = len(data["results"])
        analysis["fields_present"] = ["results"]
    
    return analysis

print("\n" + "="*70)
print("WAQI HISTORICAL DATA VERIFICATION")
print("="*70)
print(f"Test Date: {datetime.now().isoformat()}")
print(f"Cities: {', '.join(CITIES)}")
print(f"API Base: {WAQI_API_BASE}")
print("="*70 + "\n")

# Test 1: Current data endpoints
print("TEST 1: Current Data Endpoints")
print("-" * 70)

for city in CITIES:
    print(f"\n[{city}] Testing current data endpoint...")
    url = f"{WAQI_API_BASE}/feed/{city}/?token={WAQI_TOKEN}"
    print(f"  URL: {url}")
    
    success, data, error = test_api_endpoint(url)
    
    if success:
        print(f"  ✓ Response received (200 OK)")
        analysis = analyze_response(data)
        print(f"  Status: {data.get('status')}")
        print(f"  Data Type: {analysis['data_type']}")
        print(f"  Records: {analysis['record_count']}")
        print(f"  Has 'history' field: {analysis['is_historical']}")
        
        if analysis["newest_record"]:
            print(f"  Latest Record Time: {analysis['newest_record']}")
        if analysis["oldest_record"]:
            print(f"  Oldest Record Time: {analysis['oldest_record']}")
        
        print(f"  Fields: {', '.join(analysis['fields_present'][:5])}...")
        
        results["test_results"][f"{city}_current"] = {
            "success": True,
            "analysis": analysis,
            "raw_response_keys": list(data.keys()) if isinstance(data, dict) else []
        }
        
        # Store the full data for later analysis
        if city not in results["test_results"]:
            results["test_results"][city] = {}
        results["test_results"][city]["current_response"] = data
    else:
        print(f"  ✗ Failed: {error}")
        results["test_results"][f"{city}_current"] = {
            "success": False,
            "error": error
        }

# Test 2: Try to search for city stations
print("\n\nTEST 2: Search Endpoints")
print("-" * 70)

for city in CITIES:
    print(f"\n[{city}] Testing search endpoint...")
    url = f"{WAQI_API_BASE}/search/?keyword={city}&token={WAQI_TOKEN}"
    print(f"  URL: {url}")
    
    success, data, error = test_api_endpoint(url)
    
    if success:
        print(f"  ✓ Response received (200 OK)")
        analysis = analyze_response(data)
        print(f"  Status: {data.get('status')}")
        print(f"  Results Count: {analysis['record_count']}")
        
        if data.get("results"):
            print(f"  Available Stations:")
            for i, result in enumerate(data["results"][:3]):
                print(f"    {i+1}. {result.get('station', {}).get('name', 'Unknown')}")
        
        results["test_results"][f"{city}_search"] = {
            "success": True,
            "record_count": analysis["record_count"]
        }
    else:
        print(f"  ✗ Failed: {error}")
        results["test_results"][f"{city}_search"] = {
            "success": False,
            "error": error
        }

# Test 3: Try historical endpoints
print("\n\nTEST 3: Historical Data Endpoints")
print("-" * 70)

for city in CITIES:
    print(f"\n[{city}] Testing historical endpoint...")
    
    for endpoint_pattern in TEST_CONFIG["historical_endpoints"]:
        url = endpoint_pattern.format(city=city)
        print(f"  URL: {url}")
        
        success, data, error = test_api_endpoint(url)
        
        if success:
            print(f"    ✓ Response received")
            analysis = analyze_response(data)
            print(f"    Status: {data.get('status')}")
            print(f"    Records: {analysis['record_count']}")
            results["findings"].append(f"Historical endpoint found: {url}")
        else:
            print(f"    ✗ {error[:60]}...")

# Test 4: Check AQICN data platform
print("\n\nTEST 4: AQICN Data Platform")
print("-" * 70)

print("\nAttempting to access aqicn.org/data-platform/...")

platform_urls = [
    "https://aqicn.org/data-platform/",
    "https://aqicn.org/api/csv/",
    "https://data.aqicn.org/",
]

for url in platform_urls:
    print(f"\n  Testing: {url}")
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        print(f"    Status: {response.status_code}")
        if response.status_code < 400:
            print(f"    ✓ Accessible")
            results["csv_availability"]["platform_status"] = response.status_code
    except Exception as e:
        print(f"    ✗ Error: {str(e)[:50]}")

# Test 5: Try to get historical data via direct query parameters
print("\n\nTEST 5: Query Parameter Tests")
print("-" * 70)

for city in CITIES:
    print(f"\n[{city}] Testing query parameters...")
    
    # Try with date parameters
    test_urls = [
        f"{WAQI_API_BASE}/feed/{city}/?token={WAQI_TOKEN}&date=2026-01-01",
        f"{WAQI_API_BASE}/feed/{city}/?token={WAQI_TOKEN}&from=2026-01-01&to=2026-06-15",
        f"{WAQI_API_BASE}/feed/{city}/?token={WAQI_TOKEN}&days=90",
    ]
    
    for url in test_urls:
        params = url.split("?")[1] if "?" in url else ""
        print(f"  Params: {params}")
        
        success, data, error = test_api_endpoint(url)
        
        if success:
            analysis = analyze_response(data)
            if analysis["record_count"] > 1 or analysis["is_historical"]:
                print(f"    ✓ Found {analysis['record_count']} records")
                results["findings"].append(f"Historical parameter found: {url}")
            else:
                print(f"    - Standard response (1 record)")
        else:
            print(f"    ✗ {error[:50]}")

# Summary and Conclusion
print("\n\n" + "="*70)
print("SUMMARY")
print("="*70)

# Analyze findings
current_data_available = all(
    results["test_results"].get(f"{city}_current", {}).get("success", False)
    for city in CITIES
)

search_working = any(
    results["test_results"].get(f"{city}_search", {}).get("success", False)
    for city in CITIES
)

historical_found = any("historical" in finding.lower() for finding in results["findings"])

print(f"\n✓ Current Data Available: {current_data_available}")
print(f"✓ Search Endpoints Working: {search_working}")
print(f"✓ Historical Endpoints Found: {historical_found}")

# Generate detailed summary for each city
print("\n\nDETAILED CITY ANALYSIS:")
print("-" * 70)

for city in CITIES:
    print(f"\n{city}:")
    
    current = results["test_results"].get(f"{city}_current", {})
    if current.get("success"):
        analysis = current.get("analysis", {})
        print(f"  Current Data: ✓ Available")
        print(f"  Records in Response: {analysis.get('record_count', 0)}")
        print(f"  Latest Timestamp: {analysis.get('newest_record', 'N/A')}")
        print(f"  Has History Field: {analysis.get('is_historical', False)}")
    else:
        print(f"  Current Data: ✗ Error - {current.get('error', 'Unknown')}")

# Final conclusion
print("\n\n" + "="*70)
print("CONCLUSION")
print("="*70)

if not current_data_available:
    conclusion = "❌ UNABLE TO ACCESS WAQI API - No current data available"
elif historical_found:
    conclusion = "✓ Historical data endpoints found - Further investigation needed"
else:
    conclusion = "⚠️  ONLY CURRENT DATA AVAILABLE - WAQI API returns only today's data (1 record)"
    results["findings"].append("CRITICAL: WAQI API does NOT return historical data via standard endpoints")
    results["findings"].append("Only current/latest AQI reading is available per query")

results["conclusion"] = conclusion
print(f"\n{conclusion}")

print("\n\nKEY FINDINGS:")
for finding in results["findings"]:
    print(f"  • {finding}")

if not historical_found and current_data_available:
    print("\n⚠️  WARNING: Historical backfill via WAQI API appears NOT POSSIBLE")
    print("  - API returns only current data (1 record per city)")
    print("  - No history field in standard responses")
    print("  - No date/time query parameters accepted")
    print("\n  Alternative: CSV downloads may be available from aqicn.org/data-platform/")

# Save results
print("\n" + "="*70)
print("Saving detailed results to verify_waqi_results.json")
print("="*70)

with open("verify_waqi_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n✓ Results saved")
print("\nRun 'python verify_waqi_history.py' to re-run this verification")
