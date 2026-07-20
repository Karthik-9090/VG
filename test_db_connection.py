#!/usr/bin/env python3
"""
Quick database connectivity test
"""
import sys

try:
    import psycopg2
    print("[✓] psycopg2 module available")
except ImportError:
    print("[✗] psycopg2 not installed - installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary", "-q"])
    import psycopg2
    print("[✓] psycopg2 installed")

# Try connecting
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='vayuguard',
        user='postgres',
        password=''
    )
    print("[✓] Connected to vayuguard database")
    
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'engineered_features'
        )
    """)
    exists = cursor.fetchone()[0]
    
    if exists:
        print("[✓] Table 'engineered_features' exists")
        
        # Get row count
        cursor.execute("SELECT COUNT(*) FROM engineered_features")
        count = cursor.fetchone()[0]
        print(f"[✓] Table has {count:,} rows")
        
        # Get cities
        cursor.execute("SELECT DISTINCT city FROM engineered_features ORDER BY city")
        cities = [row[0] for row in cursor.fetchall()]
        print(f"[✓] Cities: {', '.join(cities)}")
    else:
        print("[✗] Table 'engineered_features' does not exist")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"[✗] Database connection failed: {e}")
    print(f"\nTroubleshooting:")
    print(f"  - Is PostgreSQL running?")
    print(f"  - Is database 'vayuguard' created?")
    print(f"  - Is user 'postgres' available?")
    sys.exit(1)

print("\n[✓] All checks passed - ready to run validation")
