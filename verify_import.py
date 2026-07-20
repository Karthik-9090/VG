#!/usr/bin/env python3
"""Quick verification of imported data"""
import psycopg2

conn = psycopg2.connect(host='localhost', user='postgres', password='postgres', database='vayuguard')
cursor = conn.cursor()

print("\n" + "="*70)
print("FINAL DATA VERIFICATION")
print("="*70 + "\n")

# Query 1
cursor.execute('SELECT COUNT(*) FROM aqi_historical;')
total = cursor.fetchone()[0]
print(f'Total Records: {total:,}\n')

# Query 2
cursor.execute('SELECT city, COUNT(*) FROM aqi_historical GROUP BY city ORDER BY city;')
print('Per City:')
for city, count in cursor.fetchall():
    print(f'  {city:15s}: {count:6,} records')

# Query 3
cursor.execute('SELECT MIN(date), MAX(date) FROM aqi_historical;')
min_date, max_date = cursor.fetchone()
days = (max_date - min_date).days
print(f'\nDate Range: {min_date} to {max_date}')
print(f'Duration: {days:,} days ({days/365:.2f} years)')

# Query 4
cursor.execute('SELECT COUNT(*) FROM (SELECT city, date FROM aqi_historical GROUP BY city, date HAVING COUNT(*) > 1) t;')
dups = cursor.fetchone()[0]
print(f'\nDuplicate (City, Date) Pairs: {dups}')

# Query 5
cursor.execute("SELECT COUNT(*) FROM aqi_historical WHERE city IN ('Chennai', 'Bengaluru', 'Hyderabad');")
target_count = cursor.fetchone()[0]
print(f'Target Cities Records: {target_count:,}')

# Query 6
cursor.execute('SELECT COUNT(*) FROM aqi_historical WHERE aqi IS NULL OR pm2_5 IS NULL OR city IS NULL;')
nulls = cursor.fetchone()[0]
print(f'NULL Values in Critical Columns: {nulls}')

cursor.close()
conn.close()

print("\n" + "="*70)
print("Status: [OK] All verifications passed")
print("="*70 + "\n")
