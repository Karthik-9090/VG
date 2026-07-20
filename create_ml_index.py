#!/usr/bin/env python3
"""Create database index for ML service optimization."""
import psycopg2

try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='vayuguard',
        user='vayuguard_user',
        password='vayuguard_pass'
    )
    
    cursor = conn.cursor()
    
    # Create new optimized index (only if not exists)
    try:
        cursor.execute("""
        CREATE INDEX idx_engineered_features_city_date_v2 
        ON engineered_features(city, date DESC)
        """)
        print("[OK] Index created successfully")
    except psycopg2.Error as idx_err:
        if "already exists" in str(idx_err):
            print("[OK] Index already exists")
        else:
            raise idx_err
    
    conn.commit()
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"[ERROR] {e}")
    exit(1)
