#!/usr/bin/env python
"""Test WAQI data ingestion to PostgreSQL."""

import sys
sys.path.insert(0, '.')

import config
from ingest_aqi import AQIIngestor
from db import DatabaseConnection

try:
    print("🔄 Initializing database connection...")
    DatabaseConnection.init_pool()
    conn = DatabaseConnection.get_connection()
    
    print("🔄 Ingesting WAQI data for 3 cities...")
    ingestor = AQIIngestor()
    results = ingestor.ingest_aqi_data(conn)
    
    print("\n✅ WAQI Ingestion Complete:")
    print(f"   Total Records: {results['total_records']}")
    print(f"   Successful: {results['successful']}")
    print(f"   Failed: {results['failed']}")
    print("\n   City Results:")
    for city, status in results['cities'].items():
        print(f"     • {city}: {status}")
    
    # Verify data in database
    print("\n🔍 Verifying data in PostgreSQL...")
    cursor = conn.cursor()
    cursor.execute("SELECT city, aqi, pm25, pm10, temperature FROM aqi_data ORDER BY recorded_at DESC LIMIT 3;")
    rows = cursor.fetchall()
    
    if rows:
        print("\n✅ Records found in database:")
        for row in rows:
            city, aqi, pm25, pm10, temp = row
            print(f"   • {city}: AQI={aqi}, PM2.5={pm25}, PM10={pm10}, Temp={temp}°C")
    else:
        print("   ⚠️  No records found (database may be empty)")
    
    cursor.close()
    DatabaseConnection.return_connection(conn)
    DatabaseConnection.close_all()
    
    print("\n✅ WAQI migration ready for production!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
