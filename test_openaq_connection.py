#!/usr/bin/env python
"""Test OpenAQ v3 API connection and retrieve sensor data."""

import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv('OPENAQ_API_KEY')
SENSOR_ID = 3917
ENDPOINT = f'https://api.openaq.org/v3/sensors/{SENSOR_ID}/days'

def test_openaq_connection():
    """Test OpenAQ API connection with sensor 3917."""
    
    print("=" * 80)
    print("OPENAQ API CONNECTION TEST")
    print("=" * 80)
    print()
    
    # Check API key
    print("STEP 1: API KEY STATUS")
    print("-" * 80)
    if not API_KEY:
        print("❌ ERROR: OPENAQ_API_KEY not found in environment variables")
        print("   Solution: Create .env file with OPENAQ_API_KEY=your_key")
        return
    else:
        print(f"✅ API Key Found: ********{API_KEY[-4:]}")
    print()
    
    # Test connection
    print("STEP 2: TESTING ENDPOINT")
    print("-" * 80)
    print(f"URL: {ENDPOINT}")
    print(f"Sensor ID: {SENSOR_ID}")
    print(f"Parameters: limit=10")
    print()
    
    try:
        # Make request with API key in header
        headers = {
            'X-API-Key': API_KEY,
            'Accept': 'application/json'
        }
        
        params = {
            'limit': 10
        }
        
        print("Sending request...")
        response = requests.get(ENDPOINT, headers=headers, params=params, timeout=10)
        
        # Print HTTP Status
        print()
        print("STEP 3: HTTP RESPONSE")
        print("-" * 80)
        print(f"Status Code: {response.status_code}")
        
        # Print Headers
        print()
        print("Response Headers:")
        print("-" * 80)
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        # Print Response Body
        print()
        print("STEP 4: RESPONSE BODY")
        print("-" * 80)
        
        try:
            response_data = response.json()
            print(f"Response Type: {type(response_data).__name__}")
            print(f"First 500 characters:")
            print("-" * 80)
            response_json = json.dumps(response_data, indent=2)
            print(response_json[:500])
            if len(response_json) > 500:
                print(f"... (truncated, total length: {len(response_json)} characters)")
            print()
            
            # Parse response
            print("STEP 5: SENSOR INFORMATION")
            print("-" * 80)
            
            if response.status_code == 200:
                print(f"✅ SUCCESS (200 OK)")
                print()
                
                if 'data' in response_data and len(response_data['data']) > 0:
                    sensor_info = response_data['data'][0]
                    
                    print(f"Sensor ID: {sensor_info.get('id', 'N/A')}")
                    print(f"Sensor Name: {sensor_info.get('name', 'N/A')}")
                    print(f"Parameter: {sensor_info.get('parameter', 'N/A')}")
                    print(f"Location: {sensor_info.get('location', 'N/A')}")
                    print(f"Country: {sensor_info.get('country', 'N/A')}")
                    print(f"Coordinates: {sensor_info.get('coordinates', 'N/A')}")
                    print()
                    print("Date Range Available:")
                    print(f"  First Measurement: {sensor_info.get('firstUpdated', 'N/A')}")
                    print(f"  Last Measurement: {sensor_info.get('lastUpdated', 'N/A')}")
                    
                    # Check data points
                    if 'results' in sensor_info:
                        print(f"  Data Points Available: {len(sensor_info['results'])}")
                        print()
                        print("Sample Data (first 3 records):")
                        for i, record in enumerate(sensor_info['results'][:3]):
                            print(f"    {i+1}. {record}")
                else:
                    print("⚠️  No data returned from API")
                    print(f"Full response: {json.dumps(response_data, indent=2)}")
                    
            elif response.status_code == 401:
                print(f"❌ UNAUTHORIZED (401)")
                print("   Your API key is invalid or expired")
                print(f"   Response: {response.text[:500]}")
                
            elif response.status_code == 403:
                print(f"❌ FORBIDDEN (403)")
                print("   Your API key doesn't have permission to access this endpoint")
                print(f"   Response: {response.text[:500]}")
                
            elif response.status_code == 404:
                print(f"❌ NOT FOUND (404)")
                print(f"   Sensor {SENSOR_ID} not found or endpoint doesn't exist")
                print(f"   Response: {response.text[:500]}")
                
            else:
                print(f"⚠️  HTTP {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
        except json.JSONDecodeError:
            print("Error parsing response as JSON")
            print(f"Response text: {response.text[:500]}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ CONNECTION ERROR: {e}")
        print("   Unable to reach OpenAQ API")
        
    except requests.exceptions.Timeout as e:
        print(f"❌ TIMEOUT ERROR: {e}")
        print("   Request took too long to complete")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
    
    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    test_openaq_connection()
