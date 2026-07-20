#!/usr/bin/env python3
"""
PHASE 5: ML API VALIDATION - FINAL

Validates that the ML service API is fully functional with all endpoints working.
Tests:
  1. Service health check
  2. Forecast generation endpoint
  3. Health risk assessment endpoint
  4. Response format validation
"""

import requests
import json
import sys
import time

def test_api_connectivity():
    """Test if ML service is running"""
    try:
        response = requests.get('http://localhost:8001/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test 1: ML Service Health Check - PASS")
            print(f"   Status: {data.get('status', 'ok')}")
            return True
        else:
            print(f"❌ Test 1: ML Service Health Check - FAIL (Status: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Test 1: ML Service Health Check - FAIL (Connection refused - service not running)")
        return False
    except Exception as e:
        print(f"❌ Test 1: ML Service Health Check - FAIL ({e})")
        return False

def test_forecast_endpoint():
    """Test forecast generation endpoint"""
    try:
        payload = {
            'city': 'Chennai',
            'horizon': 24
        }
        
        response = requests.post('http://localhost:8001/forecast', 
                                json=payload, 
                                timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ['city', 'horizon', 'forecast_values', 'model_used', 'confidence']
            
            if all(field in data for field in required_fields):
                if isinstance(data['forecast_values'], list) and len(data['forecast_values']) > 0:
                    print("✅ Test 2: Forecast Endpoint - PASS")
                    print(f"   City: {data['city']}")
                    print(f"   Horizon: {data['horizon']} hours")
                    print(f"   Forecast values: {len(data['forecast_values'])} values")
                    print(f"   Sample: AQI values range {min(data['forecast_values'])}-{max(data['forecast_values'])}")
                    print(f"   Model: {data['model_used']}, Confidence: {data['confidence']:.2%}")
                    return True
                else:
                    print("❌ Test 2: Forecast Endpoint - FAIL (forecast_values not a list)")
                    return False
            else:
                print(f"❌ Test 2: Forecast Endpoint - FAIL (Missing required fields)")
                print(f"   Expected: {required_fields}")
                print(f"   Got: {list(data.keys())}")
                return False
        else:
            print(f"❌ Test 2: Forecast Endpoint - FAIL (Status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ Test 2: Forecast Endpoint - FAIL ({e})")
        return False

def test_health_risk_endpoint():
    """Test health risk assessment endpoint"""
    try:
        payload = {
            'aqi': 150,
            'profile': 'general'
        }
        
        response = requests.post('http://localhost:8001/health-risk',
                                json=payload,
                                timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ['aqi', 'profile', 'risk_level', 'risk_index', 'advisory', 'precautions']
            
            if all(field in data for field in required_fields):
                print("✅ Test 3: Health Risk Endpoint - PASS")
                print(f"   AQI: {data['aqi']}")
                print(f"   Profile: {data['profile']}")
                print(f"   Risk Level: {data['risk_level']}")
                print(f"   Risk Index: {data['risk_index']}")
                print(f"   Advisory: {data['advisory'][:50]}...")
                print(f"   Precautions: {len(data['precautions'])} recommended")
                return True
            else:
                print(f"❌ Test 3: Health Risk Endpoint - FAIL (Missing required fields)")
                print(f"   Expected: {required_fields}")
                print(f"   Got: {list(data.keys())}")
                return False
        else:
            print(f"❌ Test 3: Health Risk Endpoint - FAIL (Status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ Test 3: Health Risk Endpoint - FAIL ({e})")
        return False

def test_response_validation():
    """Validate response formats are valid JSON and properly structured"""
    try:
        # Test with various inputs to ensure robustness
        test_cases = [
            ('forecast', {'city': 'Bengaluru', 'horizon': 12}),
            ('health-risk', {'aqi': 50, 'profile': 'children'}),
        ]
        
        all_valid = True
        for endpoint, payload in test_cases:
            try:
                if endpoint == 'forecast':
                    r = requests.post(f'http://localhost:8001/{endpoint}', json=payload, timeout=5)
                else:
                    r = requests.post(f'http://localhost:8001/{endpoint}', json=payload, timeout=5)
                
                if r.status_code != 200:
                    print(f"❌ Response validation for {endpoint} failed (Status: {r.status_code})")
                    all_valid = False
                else:
                    # Verify JSON is valid and has expected structure
                    data = r.json()
                    if not isinstance(data, dict) or len(data) == 0:
                        print(f"❌ Response validation for {endpoint} failed (Invalid structure)")
                        all_valid = False
            except Exception as e:
                print(f"❌ Response validation for {endpoint} failed ({e})")
                all_valid = False
        
        if all_valid:
            print("✅ Test 4: Response Validation - PASS")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Test 4: Response Validation - FAIL ({e})")
        return False

def run_phase5_validation():
    """Run all Phase 5 tests"""
    print("\n" + "="*60)
    print("PHASE 5: ML API VALIDATION")
    print("="*60 + "\n")
    
    print("Configuration:")
    print("  - ML Service: http://localhost:8001")
    print("  - Health endpoint: /health")
    print("  - Forecast endpoint: POST /forecast")
    print("  - Health Risk endpoint: POST /health-risk\n")
    
    results = {
        'health_check': test_api_connectivity(),
        'forecast': test_forecast_endpoint(),
        'health_risk': test_health_risk_endpoint(),
        'response_validation': test_response_validation()
    }
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print("\n" + "="*60)
    print(f"PHASE 5 RESULTS: {passed}/{total} Tests Passed")
    print("="*60)
    
    if passed == total:
        print("\n✅ ML API IS FULLY OPERATIONAL")
        print("   - Service responds to all endpoints")
        print("   - Response formats are valid and complete")
        print("   - Ready for production use")
        return True
    else:
        print(f"\n⚠️  ML API OPERATIONAL WITH {total-passed} ISSUE(S)")
        return False

if __name__ == '__main__':
    success = run_phase5_validation()
    sys.exit(0 if success else 1)
