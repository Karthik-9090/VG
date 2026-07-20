#!/usr/bin/env python
"""
Phase 4: Performance Stress Testing
Tests the FastAPI endpoint under increasing concurrent load
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime
import statistics

async def make_request(session, url, payload, test_name):
    """Make a single HTTP request and return timing"""
    try:
        start = time.time()
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            await resp.json()
            elapsed = (time.time() - start) * 1000  # Convert to ms
            return {
                'status': resp.status,
                'latency_ms': elapsed,
                'success': resp.status == 200,
                'error': None
            }
    except asyncio.TimeoutError:
        return {
            'status': 504,
            'latency_ms': None,
            'success': False,
            'error': 'Timeout'
        }
    except Exception as e:
        return {
            'status': 500,
            'latency_ms': None,
            'success': False,
            'error': str(e)
        }

async def run_load_test(concurrent_users, requests_per_user):
    """Run load test with specified concurrency"""
    
    url = "http://127.0.0.1:8001/forecast"
    
    # Different payload for each test case
    test_payloads = [
        {"city": "Chennai", "aqi": 85.5, "pm2_5": 45.0, "pm10": 120.0, "no2": 35.0, "so2": 15.0, "co": 1.5, "o3": 0.0},
        {"city": "Bengaluru", "aqi": 120.0, "pm2_5": 65.0, "pm10": 150.0, "no2": 42.0, "so2": 20.0, "co": 2.0, "o3": 5.0},
        {"city": "Hyderabad", "aqi": 95.0, "pm2_5": 50.0, "pm10": 130.0, "no2": 38.0, "so2": 18.0, "co": 1.8, "o3": 2.0}
    ]
    
    results = []
    errors = []
    
    async with aiohttp.ClientSession() as session:
        # Create all tasks
        tasks = []
        for user_id in range(concurrent_users):
            for req_num in range(requests_per_user):
                payload = test_payloads[(user_id + req_num) % len(test_payloads)]
                task = make_request(session, url, payload, f"user_{user_id}_req_{req_num}")
                tasks.append(task)
        
        # Execute all tasks concurrently
        responses = await asyncio.gather(*tasks)
        
        for resp in responses:
            if resp['success']:
                results.append(resp['latency_ms'])
            else:
                errors.append(resp)
    
    return results, errors

def analyze_results(results, errors, concurrent_users, requests_per_user):
    """Analyze stress test results"""
    
    if not results:
        return None
    
    total_requests = len(results) + len(errors)
    successful_requests = len(results)
    failed_requests = total_requests - successful_requests
    error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
    
    stats = {
        'concurrent_users': concurrent_users,
        'requests_per_user': requests_per_user,
        'total_requests': total_requests,
        'successful_requests': successful_requests,
        'failed_requests': failed_requests,
        'error_rate_percent': round(error_rate, 2),
        'min_latency_ms': round(min(results), 2),
        'max_latency_ms': round(max(results), 2),
        'mean_latency_ms': round(statistics.mean(results), 2),
        'median_latency_ms': round(statistics.median(results), 2),
        'stdev_latency_ms': round(statistics.stdev(results), 2) if len(results) > 1 else 0,
        'p95_latency_ms': round(sorted(results)[int(len(results) * 0.95)], 2),
        'p99_latency_ms': round(sorted(results)[int(len(results) * 0.99)], 2),
        'throughput_rps': round(successful_requests / (max(results) / 1000) if results else 0, 2)
    }
    
    return stats

async def main():
    """Run complete stress test suite"""
    
    print("=" * 80)
    print("PHASE 4: API STRESS TEST REPORT")
    print("=" * 80)
    print(f"\nTest Started: {datetime.now().isoformat()}")
    print(f"Target Endpoint: POST http://127.0.0.1:8001/forecast")
    print(f"ML Service: FastAPI (Lasso Regression)")
    print("")
    
    # Test configurations
    test_configs = [
        {"concurrent_users": 10, "requests_per_user": 10, "name": "Light Load"},
        {"concurrent_users": 50, "requests_per_user": 5, "name": "Medium Load"},
        {"concurrent_users": 100, "requests_per_user": 3, "name": "Heavy Load"},
    ]
    
    all_results = []
    
    for config in test_configs:
        concurrent_users = config['concurrent_users']
        requests_per_user = config['requests_per_user']
        test_name = config['name']
        total_requests = concurrent_users * requests_per_user
        
        print(f"\n{'=' * 80}")
        print(f"TEST: {test_name}")
        print(f"  Concurrent Users: {concurrent_users}")
        print(f"  Requests per User: {requests_per_user}")
        print(f"  Total Requests: {total_requests}")
        print(f"{'=' * 80}")
        
        start_time = time.time()
        results, errors = await run_load_test(concurrent_users, requests_per_user)
        test_duration = time.time() - start_time
        
        # Calculate statistics
        if results:
            stats = analyze_results(results, errors, concurrent_users, requests_per_user)
            stats['total_requests'] = total_requests
            stats['successful_requests'] = len(results)
            stats['failed_requests'] = len(errors)
            stats['test_duration_seconds'] = round(test_duration, 2)
            stats['error_rate_percent'] = round((len(errors) / total_requests * 100), 2)
            
            print(f"\nResults:")
            print(f"  Requests: {len(results)} successful, {len(errors)} failed")
            print(f"  Error Rate: {stats['error_rate_percent']}%")
            print(f"  Test Duration: {test_duration:.2f} seconds")
            print(f"\nLatency Statistics (milliseconds):")
            print(f"  Min:     {stats['min_latency_ms']} ms")
            print(f"  Max:     {stats['max_latency_ms']} ms")
            print(f"  Mean:    {stats['mean_latency_ms']} ms")
            print(f"  Median:  {stats['median_latency_ms']} ms")
            print(f"  Std Dev: {stats['stdev_latency_ms']} ms")
            print(f"  P95:     {stats['p95_latency_ms']} ms")
            print(f"  P99:     {stats['p99_latency_ms']} ms")
            print(f"\nThroughput:")
            print(f"  Avg RPS: {stats['throughput_rps']} requests/second")
            
            all_results.append(stats)
        else:
            print(f"\n[ERROR] All requests failed!")
            if errors:
                print(f"First error: {errors[0]}")
    
    # Generate summary
    print(f"\n{'=' * 80}")
    print("STRESS TEST SUMMARY")
    print(f"{'=' * 80}")
    
    print(f"\nTarget Performance:")
    print(f"  Latency Target: < 500ms")
    print(f"  Error Rate Target: < 1%")
    print(f"  P95 Latency Target: < 750ms")
    
    print(f"\nResults Achieved:")
    for result in all_results:
        status = "PASS" if result['p95_latency_ms'] < 750 and result['error_rate_percent'] < 1 else "FAIL"
        print(f"\n  {result['concurrent_users']} concurrent users:")
        print(f"    Status: {status}")
        print(f"    P95 Latency: {result['p95_latency_ms']} ms (target: < 750ms)")
        print(f"    Error Rate: {result['error_rate_percent']}% (target: < 1%)")
        print(f"    Throughput: {result['throughput_rps']} RPS")
    
    print(f"\n{'=' * 80}")
    print(f"Test Completed: {datetime.now().isoformat()}")
    print(f"{'=' * 80}\n")

if __name__ == '__main__':
    asyncio.run(main())
