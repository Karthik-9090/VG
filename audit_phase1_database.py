"""Phase 1: Database Validation Audit"""

import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

print("="*80)
print("PHASE 1: DATABASE VALIDATION AUDIT")
print(f"Timestamp: {datetime.now().isoformat()}")
print("="*80)
print()

try:
    # Connection
    print("[1/5] DATABASE CONNECTION TEST")
    print("-"*80)
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'vayuguard'),
        user=os.getenv('DB_USER', 'vayuguard_user'),
        password=os.getenv('DB_PASSWORD', 'vayuguard_pass')
    )
    cursor = conn.cursor()
    
    cursor.execute('SELECT version();')
    version = cursor.fetchone()[0]
    print(f"✓ CONNECTION SUCCESS")
    print(f"  PostgreSQL: {version}")
    print()
    
    # List tables
    print("[2/5] DATABASE TABLES")
    print("-"*80)
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    print(f"Tables found: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")
    print()
    
    # Schema verification
    print("[3/5] AQI_DATA TABLE SCHEMA")
    print("-"*80)
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'aqi_data'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    print(f"Columns: {len(columns)}")
    for col_name, data_type, nullable in columns:
        nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
        print(f"  {col_name:20} {data_type:15} {nullable_str}")
    print()
    
    # Indexes
    print("[4/5] INDEXES & CONSTRAINTS")
    print("-"*80)
    cursor.execute("""
        SELECT constraint_name, constraint_type
        FROM information_schema.table_constraints
        WHERE table_name = 'aqi_data'
        ORDER BY constraint_name;
    """)
    constraints = cursor.fetchall()
    print(f"Constraints: {len(constraints)}")
    for name, ctype in constraints:
        print(f"  {name:30} {ctype}")
    print()
    
    # Data verification
    print("[5/5] DATA STATISTICS")
    print("-"*80)
    cursor.execute("SELECT COUNT(*) FROM aqi_data;")
    total_records = cursor.fetchone()[0]
    print(f"Total records: {total_records}")
    print()
    
    if total_records > 0:
        cursor.execute("""
            SELECT
                city,
                COUNT(*) AS records,
                MIN(recorded_at) AS first_record,
                MAX(recorded_at) AS latest_record,
                COUNT(CASE WHEN aqi IS NULL THEN 1 END) as null_aqi,
                COUNT(CASE WHEN pm25 IS NULL THEN 1 END) as null_pm25
            FROM aqi_data
            GROUP BY city
            ORDER BY city;
        """)
        city_stats = cursor.fetchall()
        print("City Statistics:")
        for city, count, first, latest, null_aqi, null_pm25 in city_stats:
            print(f"\n  {city}:")
            print(f"    Records: {count}")
            print(f"    First: {first}")
            print(f"    Latest: {latest}")
            print(f"    Null AQI: {null_aqi}")
            print(f"    Null PM2.5: {null_pm25}")
    
    cursor.close()
    conn.close()
    
    print()
    print("="*80)
    print("✓ DATABASE VALIDATION: PASSED")
    print("="*80)

except Exception as e:
    print()
    print("="*80)
    print(f"✗ DATABASE VALIDATION: FAILED")
    print(f"Error: {e}")
    print("="*80)
    exit(1)
