#!/usr/bin/env python
"""Find OpenAQ sensors for Indian cities."""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('OPENAQ_API_KEY')

def find_sensors_by_city(city_name, country='India'):
    """Find sensors for a specific city."""
    
    print(f"\n{'='*80}")
    print(f"SEARCHING FOR SENSORS: {city_name}, {country}")
    print(f"{'='*80}")
    
    # Search for locations in the city
    url = 'https://api.openaq.org/v3/locations'
    
    headers = {
        'X-API-Key': API_KEY,
        'Accept': 'application/json'
    }
    
    params = {
        'city': city_name,
        'country_id': 'IN',  # India
        'limit': 50
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"Found: {len(data.get('results', []))} locations")
            
            if data.get('results'):
                for i, location in enumerate(data['results'][:5], 1):
                    print(f"\n{i}. Location: {location.get('name', 'N/A')}")
                    print(f"   ID: {location.get('id', 'N/A')}")
                    print(f"   Country: {location.get('country', 'N/A')}")
                    print(f"   City: {location.get('city', 'N/A')}")
                    
                    # Get sensors for this location
                    sensors = location.get('sensors', [])
                    if sensors:
                        print(f"   Sensors ({len(sensors)}):")
                        for sensor in sensors[:3]:
                            print(f"     - {sensor.get('name', 'N/A')} (ID: {sensor.get('id', 'N/A')})")
                            print(f"       Parameter: {sensor.get('parameter', {}).get('name', 'N/A')}")
                            print(f"       Last Updated: {sensor.get('lastUpdated', 'N/A')}")
            else:
                print("No locations found")
                
        else:
            print(f"Error: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("="*80)
    print("OPENAQ SENSOR SEARCH - INDIAN CITIES")
    print("="*80)
    
    cities = ['Chennai', 'Bengaluru', 'Hyderabad']
    
    for city in cities:
        find_sensors_by_city(city)
    
    print("\n" + "="*80)
    print("SEARCH COMPLETE")
    print("="*80)

if __name__ == '__main__':
    main()
