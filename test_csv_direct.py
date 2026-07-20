#!/usr/bin/env python3
"""
Direct test of CSV endpoints to get actual data
"""

import requests
import csv
import io
from datetime import datetime

print("\n" + "="*70)
print("DIRECT CSV DATA RETRIEVAL TEST")
print("="*70)
print(f"Test Date: {datetime.now().isoformat()}")
print("="*70 + "\n")

# Test the identified endpoints
endpoints = [
    "https://aqicn.org/data-platform/csv/?city=Chennai",
    "https://aqicn.org/api/csv/?city=Chennai&days=90",
    "https://aqicn.org/csv/Chennai",
]

for url in endpoints:
    print(f"\nTesting: {url}")
    print("-" * 70)
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'Not specified')}")
        print(f"Content Length: {len(response.content)} bytes")
        
        # Check if it's CSV
        if 'text/csv' in response.headers.get('Content-Type', ''):
            print("✓ Response is CSV format")
        elif response.text.startswith('aqi,') or response.text.startswith('date,'):
            print("✓ Response contains CSV data")
        else:
            print("✗ Response appears to be HTML/Web page")
        
        # Show first 300 characters
        preview = response.text[:500]
        print(f"\nFirst 500 chars of response:")
        print("-" * 40)
        print(preview)
        print("-" * 40)
        
        # Try to parse as CSV
        try:
            if response.text and (',' in response.text or '\t' in response.text):
                lines = response.text.split('\n')[:5]
                print(f"\nFirst few lines:")
                for i, line in enumerate(lines):
                    if line.strip():
                        print(f"  {i}: {line[:80]}")
        except Exception as e:
            print(f"Note: {str(e)}")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")

print("\n\n" + "="*70)
print("DIRECT CSV TEST SUMMARY")
print("="*70)

# Now test with station-specific URLs
print("\nTrying station-specific endpoints...")

# Get list of station indices (if we can find them)
stations = {
    "Chennai": ["1016", "1015", "10308"],  # Common station indices
    "Bengaluru": ["1017", "1018"],
    "Hyderabad": ["1019"],
}

for city, indices in stations.items():
    print(f"\n{city}:")
    for idx in indices[:1]:  # Test first one
        url = f"https://aqicn.org/data/csv/{idx}"
        try:
            response = requests.get(url, timeout=5)
            print(f"  Station {idx}: {response.status_code}", end="")
            if response.status_code == 200:
                print(f" - {len(response.content)} bytes")
            else:
                print()
        except:
            pass

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)
print("""
CSV download endpoints appear to return HTML pages, not raw CSV data.
This suggests:
1. CSV download requires interaction with a web form
2. Or requires JavaScript/AJAX to retrieve actual data
3. Or requires a specific authentication/session

NEXT STEPS:
- Try manual download from aqicn.org/data-platform/ website
- Use web scraping with Selenium to trigger downloads
- Contact AQICN/WAQI for API access to historical data
- Use CPCB official API (if available)
""")
