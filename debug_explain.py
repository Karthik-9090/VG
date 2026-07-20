#!/usr/bin/env python3
"""
DEBUG: Check EXPLAIN ANALYZE output format
"""

import psycopg2
import json

conn = psycopg2.connect(
    host='localhost', port=5432, database='vayuguard',
    user='postgres', password=''
)
cursor = conn.cursor()

FORECAST_QUERY = """
SELECT lag_1, lag_3, lag_6, lag_12, lag_24,
       rolling_mean_6, rolling_mean_12, rolling_mean_24,
       rolling_std_6, rolling_std_12, rolling_std_24,
       hour, day_of_week, month, quarter, day_of_month
FROM engineered_features
WHERE city = %s
ORDER BY date DESC
LIMIT 1
"""

print("Running EXPLAIN ANALYZE...")
explain_sql = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {FORECAST_QUERY}"

try:
    cursor.execute(explain_sql, ('Chennai',))
    result = cursor.fetchone()
    
    print(f"\nResult type: {type(result)}")
    print(f"Result length: {len(result) if result else 0}")
    
    if result:
        raw = result[0]
        print(f"\nRaw result type: {type(raw)}")
        print(f"Raw result: {raw[:200] if isinstance(raw, str) else str(raw)[:200]}")
        
        # Try parsing
        if isinstance(raw, list):
            data = raw
        elif isinstance(raw, str):
            data = json.loads(raw)
        else:
            data = raw
        
        print(f"\nParsed data type: {type(data)}")
        print(f"Parsed data length: {len(data) if isinstance(data, list) else 'N/A'}")
        
        if isinstance(data, list):
            print(f"\nList contents:")
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    print(f"  [{i}]: dict with keys: {list(item.keys())}")
                else:
                    print(f"  [{i}]: {type(item).__name__}")
        
        # Try to extract timing
        print(f"\n\nAttempting to extract timing...")
        if isinstance(data, list) and len(data) > 1:
            if isinstance(data[1], dict) and 'Execution Time' in data[1]:
                print(f"✓ Found Execution Time: {data[1]['Execution Time']}")
                print(f"✓ Found Planning Time: {data[1]['Planning Time']}")
        else:
            print(f"Could not find timing in expected location")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

cursor.close()
conn.close()
