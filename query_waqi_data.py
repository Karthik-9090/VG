#!/usr/bin/env python
"""Query database for latest WAQI records."""

import psycopg2

try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='vayuguard',
        user='postgres',
        password=''
    )
    cursor = conn.cursor()
    
    # Query latest records
    cursor.execute("""
        SELECT 
            city, aqi, pm25, pm10, no2, o3, so2, co,
            temperature, humidity, wind_speed, pressure,
            recorded_at, created_at
        FROM aqi_data
        ORDER BY created_at DESC
        LIMIT 5
    """)
    
    rows = cursor.fetchall()
    col_names = [desc[0] for desc in cursor.description]
    
    print(f"\n{'='*100}")
    print(f"Latest WAQI Records ({len(rows)} found)")
    print(f"{'='*100}\n")
    
    for i, row in enumerate(rows, 1):
        print(f"Record {i}:")
        for col_name, value in zip(col_names, row):
            print(f"  {col_name:20} = {value}")
        print()
    
    # Summary statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN pm25 IS NOT NULL THEN 1 END) as with_pm25,
            COUNT(CASE WHEN temperature IS NOT NULL THEN 1 END) as with_temp,
            COUNT(CASE WHEN humidity IS NOT NULL THEN 1 END) as with_humidity
        FROM aqi_data
    """)
    
    stats = cursor.fetchone()
    print(f"{'='*100}")
    print(f"Database Summary:")
    print(f"  Total Records: {stats[0]}")
    print(f"  With PM2.5: {stats[1]}")
    print(f"  With Temperature: {stats[2]}")
    print(f"  With Humidity: {stats[3]}")
    print(f"{'='*100}\n")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
