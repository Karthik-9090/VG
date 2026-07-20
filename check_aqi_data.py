#!/usr/bin/env python
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='vayuguard',
    user='vayuguard_user',
    password='vayuguard_pass'
)
cur = conn.cursor()

# Check if aqi_data table has records
cur.execute('SELECT COUNT(*) FROM aqi_data')
count = cur.fetchone()[0]
print(f'AQI data rows: {count}')

if count > 0:
    cur.execute('SELECT city, aqi, pm25, pm10, no2, so2, co, o3, recorded_at FROM aqi_data ORDER BY recorded_at DESC LIMIT 3')
    print('\nLatest AQI records:')
    for row in cur.fetchall():
        city, aqi, pm25, pm10, no2, so2, co, o3, recorded_at = row
        print(f'  City: {city}')
        print(f'    AQI: {aqi}, PM2.5: {pm25}, PM10: {pm10}, NO2: {no2}, SO2: {so2}, CO: {co}, O3: {o3}')
        print(f'    Recorded: {recorded_at}')
        print()
else:
    print('No AQI data found in database!')

conn.close()
