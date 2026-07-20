#!/usr/bin/env python
"""Quick WAQI API connection test."""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

WAQI_API_KEY = os.getenv('WAQI_API_KEY')
CITIES = ['Chennai', 'Bengaluru', 'Hyderabad']

def test_waqi_connection():
    """Test WAQI API for all cities."""
    if not WAQI_API_KEY:
        print("❌ WAQI_API_KEY not found in .env")
        return False
    
    print(f"🔍 Testing WAQI API with key: {WAQI_API_KEY[:10]}...\n")
    
    all_success = True
    for city in CITIES:
        try:
            url = f"https://api.waqi.info/feed/{city}/?token={WAQI_API_KEY}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    aqi_data = data.get('data', {})
                    aqi = aqi_data.get('aqi', 'N/A')
                    print(f"✅ {city}: AQI = {aqi}")
                else:
                    print(f"⚠️  {city}: API status = {data.get('status')}")
                    all_success = False
            else:
                print(f"❌ {city}: HTTP {response.status_code}")
                all_success = False
                
        except requests.exceptions.Timeout:
            print(f"❌ {city}: Timeout (10s)")
            all_success = False
        except Exception as e:
            print(f"❌ {city}: Error - {e}")
            all_success = False
    
    return all_success

if __name__ == '__main__':
    success = test_waqi_connection()
    sys.exit(0 if success else 1)
