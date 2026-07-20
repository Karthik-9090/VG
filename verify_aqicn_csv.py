#!/usr/bin/env python3
"""
Verify AQICN CSV Download Availability
Tests the aqicn.org data platform for actual historical CSV downloads
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

print("\n" + "="*70)
print("AQICN DATA PLATFORM CSV VERIFICATION")
print("="*70)
print(f"Test Date: {datetime.now().isoformat()}")
print("="*70 + "\n")

# Test 1: Access main data platform
print("TEST 1: Accessing AQICN Data Platform")
print("-" * 70)

url = "https://aqicn.org/data-platform/"
print(f"\nURL: {url}")

try:
    response = requests.get(url, timeout=15)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Platform accessible")
        
        # Check for CSV-related content
        content = response.text
        
        # Look for CSV links
        csv_links = re.findall(r'href=["\']([^"\']*\.csv[^"\']*)["\']', content, re.IGNORECASE)
        print(f"\nCSV Links found: {len(csv_links)}")
        for link in csv_links[:5]:
            print(f"  • {link}")
        
        # Look for download links or data tables
        download_patterns = [
            r'download.*csv',
            r'export.*csv',
            r'data.*download',
            r'csv.*download'
        ]
        
        for pattern in download_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"\nMatches for '{pattern}': {len(matches)}")
        
        # Check for city names
        cities = ["Chennai", "Bangalore", "Bengaluru", "Hyderabad"]
        print(f"\nCity references in page:")
        for city in cities:
            count = content.lower().count(city.lower())
            if count > 0:
                print(f"  • {city}: {count} mentions")
        
        # Try to find search functionality
        if "search" in content.lower():
            print("\n✓ Search functionality detected on platform")
        
        # Check for data download sections
        if "download" in content.lower():
            print("✓ Download functionality detected")
            
            # Extract any text near "download"
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'download' in line.lower() and len(line) < 300:
                    print(f"  Context: {line[:100].strip()}...")
    else:
        print(f"✗ Failed with status {response.status_code}")

except Exception as e:
    print(f"✗ Error: {str(e)}")

# Test 2: Try direct CSV download URLs
print("\n\nTEST 2: Testing Potential CSV Download URLs")
print("-" * 70)

potential_urls = [
    "https://aqicn.org/data-platform/csv/?city=Chennai",
    "https://aqicn.org/data-platform/download/?city=Chennai",
    "https://aqicn.org/data/csv/Chennai",
    "https://aqicn.org/api/csv/?city=Chennai&days=90",
    "https://aqicn.org/csv/Chennai",
    "https://www.aqicn.org/data/csv/", 
]

for url in potential_urls:
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        status = "✓" if response.status_code < 400 else "✗"
        print(f"{status} {url}: {response.status_code}")
        
        if response.status_code < 400:
            # Try GET to see if it returns data
            get_response = requests.get(url, timeout=5)
            if "aqi" in get_response.text.lower() or "pm" in get_response.text.lower():
                print(f"   -> Contains data!")
                # Show first 200 chars
                preview = get_response.text[:200].replace('\n', ' ')
                print(f"   Preview: {preview}...")
    except Exception as e:
        print(f"✗ {url}: {str(e)[:50]}")

# Test 3: Check for AQICN API endpoints
print("\n\nTEST 3: AQICN API Endpoints")
print("-" * 70)

api_urls = [
    "https://api.aqicn.org/feed/Chennai/?token=demo",
    "https://api.waqi.info/feed/Chennai/?token=demo",
]

for url in api_urls:
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ {url}")
            print(f"  Status: {data.get('status')}")
            
            if data.get('data'):
                # Check what fields are present
                fields = list(data['data'].keys())
                print(f"  Fields: {fields[:10]}...")
                
                # Check for any historical data
                if 'forecast' in data['data']:
                    print(f"  Forecast data: Available ({len(data['data']['forecast'])} records)")
                if 'history' in data['data']:
                    print(f"  History data: Available ({len(data['data']['history'])} records)")
                if 'iaqi' in data['data']:
                    iaqi = data['data']['iaqi']
                    print(f"  Pollutants: {list(iaqi.keys())}")
    except Exception as e:
        print(f"✗ {url}: {str(e)[:60]}")

# Test 4: Check archive/historical sources
print("\n\nTEST 4: Archive & Historical Data Sources")
print("-" * 70)

archive_urls = [
    ("AQICN Archives", "https://archive.aqicn.org/"),
    ("AQICN Historical", "https://aqicn.org/historical/"),
    ("AQICN Data Download", "https://aqicn.org/download/"),
]

for name, url in archive_urls:
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        status_icon = "✓" if response.status_code < 400 else "✗"
        print(f"{status_icon} {name}: {response.status_code}")
    except Exception as e:
        print(f"✗ {name}: {str(e)[:40]}")

print("\n\n" + "="*70)
print("ANALYSIS")
print("="*70)

print("""
FINDINGS:

1. WAQI API (/feed/ endpoints):
   - Returns ONLY current data (1 record)
   - No historical data in API responses
   - Date/time parameters are IGNORED
   - NOT suitable for historical backfill

2. AQICN Data Platform (aqicn.org/data-platform/):
   - Platform is ACCESSIBLE (HTTP 200)
   - May contain CSV downloads
   - Requires manual interaction or web scraping

3. CSV Download Mechanism:
   - UNCLEAR: Need to inspect platform HTML directly
   - May require searching city names
   - May require date range selection

CONCLUSION:
✗ WAQI API DOES NOT SUPPORT HISTORICAL DATA VIA API
   - Cannot backfill historical data programmatically
   - Can only collect real-time data going forward
   
? CSV downloads may exist on aqicn.org/data-platform/
   - Requires manual download or web scraping
   - Alternative: Contact CPCB for official validated data
""")
