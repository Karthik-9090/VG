#!/usr/bin/env python
"""Inspect WAQI API response detail."""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

WAQI_API_KEY = os.getenv('WAQI_API_KEY')
CITIES = ['Chennai', 'Bengaluru', 'Hyderabad']

for city in CITIES:
    try:
        url = f"https://api.waqi.info/feed/{city}/?token={WAQI_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('status') == 'ok':
            aqi_data = data.get('data', {})
            print(f"\n{'='*60}")
            print(f"🏙️  {city.upper()}")
            print(f"{'='*60}")
            print(f"AQI: {aqi_data.get('aqi')}")
            print(f"Time: {aqi_data.get('time')}")
            print(f"\nPollutants (iaqi):")
            iaqi = aqi_data.get('iaqi', {})
            for pollutant, val_dict in sorted(iaqi.items()):
                v = val_dict.get('v', 'N/A')
                print(f"  • {pollutant.upper()}: {v}")
        else:
            print(f"\n❌ {city}: {data.get('status')}")
            
    except Exception as e:
        print(f"\n❌ {city}: {e}")
