#!/usr/bin/env python
"""Find OpenAQ sensors for Indian cities using coordinates."""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('OPENAQ_API_KEY')

# City coordinates
CITIES = {
    'Chennai': {'lat': 13.0827, 'lon': 80.2707},
    'Bengaluru': {'lat': 12.9716, 'lon': 77.5946},
    'Hyderabad': {'lat': 17.3850, 'lon': 78.4867}
}

def find_sensors_by_coordinates(city_name, lat, lon):
    """Find sensors near city coordinates."""
    
    print(f"\n{'='*80}")
    print(f"SEARCHING FOR SENSORS: {city_name}")
    print(f"Coordinates: {lat}, {lon}")
    print(f"{'='*80}")
    
    # Search for locations within radius
    url = 'https://api.openaq.org/v3/locations'
    
    headers = {
        'X-API-Key': API_KEY,
        'Accept': 'application/json'
    }
    
    # Try radius-based search
    params = {
        'coordinates': f'{lat},{lon}',
        'radius': 50,  # 50 km radius
        'limit': 50
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            print(f"Found: {len(results)} locations")
            
            if results:
                for i, location in enumerate(results, 1):
                    print(f"\n{i}. Location: {location.get('name', 'N/A')}")
                    print(f"   ID: {location.get('id', 'N/A')}")
                    print(f"   Country: {location.get('country', {}).get('name', 'N/A')}")
                    print(f"   Coordinates: {location.get('coordinates', {})}")
                    
                    # Get sensors for this location
                    sensors = location.get('sensors', [])
                    if sensors:
                        print(f"   Sensors ({len(sensors)}):")
                        for sensor in sensors:
                            param_name = sensor.get('parameter', {}).get('name', 'N/A')
                            sensor_id = sensor.get('id', 'N/A')
                            last_updated = sensor.get('lastUpdated', 'N/A')
                            print(f"     - ID: {sensor_id}")
                            print(f"       Parameter: {param_name}")
                            print(f"       Last Updated: {last_updated}")
                    else:
                        print("   No sensors at this location")
            else:
                print("⚠️  No locations found within 50 km radius")
                print("Response:", json.dumps(data, indent=2)[:500])
                
        else:
            print(f"Error: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("="*80)
    print("OPENAQ SENSOR SEARCH - INDIAN CITIES (BY COORDINATES)")
    print("="*80)
    
    for city_name, coords in CITIES.items():
        find_sensors_by_coordinates(city_name, coords['lat'], coords['lon'])
    
    print("\n" + "="*80)
    print("SEARCH COMPLETE")
    print("="*80)
    print("\nNOTE: If no sensors found, OpenAQ may have limited coverage in India")
    print("Alternative: Use alternative data sources like:")
    print("  - WAQI (World Air Quality Index)")
    print("  - IQAir API")
    print("  - NASA SEDAC data")

if __name__ == '__main__':
    main()
