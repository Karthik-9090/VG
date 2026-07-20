#!/usr/bin/env python
import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, database='vayuguard', user='vayuguard_user', password='vayuguard_pass')
cursor = conn.cursor()

# Check tables exist
tables = ['aqi_historical', 'aqi_data', 'prediction_logs', 'engineered_features']
print('=== Table Status ===')
for table in tables:
    cursor.execute(f"SELECT to_regclass('{table}') IS NOT NULL")
    exists = cursor.fetchone()[0]
    status = "✓" if exists else "✗"
    print(f'{table}: {status}')

# Check data in key tables
print('')
print('=== Data Counts ===')
cursor.execute('SELECT COUNT(*) FROM aqi_historical')
print(f'aqi_historical: {cursor.fetchone()[0]} records')

cursor.execute('SELECT COUNT(*) FROM aqi_data')
print(f'aqi_data: {cursor.fetchone()[0]} records')

cursor.execute('SELECT COUNT(*) FROM engineered_features')
print(f'engineered_features: {cursor.fetchone()[0]} records')

# Check indexes
print('')
print('=== Indexes ===')
cursor.execute("""
SELECT indexname FROM pg_indexes 
WHERE tablename IN ('aqi_historical', 'aqi_data', 'prediction_logs')
""")
for row in cursor.fetchall():
    print(f'  {row[0]}')

# Check constraints
print('')
print('=== Constraints ===')
cursor.execute("""
SELECT constraint_name, constraint_type 
FROM information_schema.table_constraints 
WHERE table_name IN ('aqi_historical', 'aqi_data')
""")
for row in cursor.fetchall():
    print(f'  {row[0]} ({row[1]})')

conn.close()
print('')
print('✓ Database validation complete')
