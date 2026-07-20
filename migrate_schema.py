#!/usr/bin/env python
"""Apply WAQI schema migration to PostgreSQL."""

import psycopg2

try:
    print("🔄 Connecting to PostgreSQL as postgres superuser...")
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='vayuguard',
        user='postgres',
        password=''
    )
    cursor = conn.cursor()
    
    # Check current columns
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='aqi_data' ORDER BY ordinal_position")
    cols = [row[0] for row in cursor.fetchall()]
    print(f"\n📋 Current aqi_data columns ({len(cols)} total):")
    for col in cols:
        print(f"   • {col}")
    
    # Apply migration
    print("\n🔧 Applying schema migration...")
    migrations = [
        'ALTER TABLE aqi_data ADD COLUMN IF NOT EXISTS pm25 FLOAT;',
        'ALTER TABLE aqi_data ADD COLUMN IF NOT EXISTS pm10 FLOAT;',
        'ALTER TABLE aqi_data ADD COLUMN IF NOT EXISTS no2 FLOAT;',
        'ALTER TABLE aqi_data ADD COLUMN IF NOT EXISTS o3 FLOAT;',
        'ALTER TABLE aqi_data ADD COLUMN IF NOT EXISTS so2 FLOAT;',
        'ALTER TABLE aqi_data ADD COLUMN IF NOT EXISTS co FLOAT;',
        'ALTER TABLE aqi_data ADD COLUMN IF NOT EXISTS temperature FLOAT;',
        'ALTER TABLE aqi_data ADD COLUMN IF NOT EXISTS humidity FLOAT;',
        'ALTER TABLE aqi_data ADD COLUMN IF NOT EXISTS wind_speed FLOAT;',
        'ALTER TABLE aqi_data ADD COLUMN IF NOT EXISTS pressure FLOAT;',
        'ALTER TABLE aqi_data ADD COLUMN IF NOT EXISTS recorded_at TIMESTAMP;',
        'ALTER TABLE aqi_data ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;',
    ]
    
    for i, migration in enumerate(migrations, 1):
        cursor.execute(migration)
        print(f"   ✅ [{i}/{len(migrations)}] {migration[:55]}...")
    
    conn.commit()
    
    # Verify new columns
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='aqi_data' ORDER BY ordinal_position")
    new_cols = [row[0] for row in cursor.fetchall()]
    print(f"\n✅ Updated aqi_data schema ({len(new_cols)} total columns):")
    for col in new_cols:
        print(f"   • {col}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Schema migration complete!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
