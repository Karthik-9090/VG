import psycopg2

conn = psycopg2.connect(host='127.0.0.1', port=5432, dbname='vayuguard', user='vayuguard_user', password='vayuguard_pass')
cur = conn.cursor()
cur.execute("SELECT id, city, aqi FROM aqi_data WHERE pm25 IS NULL OR pm10 IS NULL OR no2 IS NULL OR so2 IS NULL OR co IS NULL OR o3 IS NULL")
rows = cur.fetchall()
print('repairing', len(rows), 'rows')
for rid, city, aqi in rows:
    pm25 = max(1, int(aqi * 0.8))
    pm10 = max(2, int(aqi * 1.1))
    no2 = max(1, int(aqi * 0.3))
    so2 = max(1, int(aqi * 0.2))
    co = max(1, int(aqi * 0.1))
    o3 = max(1, int(aqi * 0.4))
    cur.execute(
        'UPDATE aqi_data SET pm25=%s, pm10=%s, no2=%s, so2=%s, co=%s, o3=%s WHERE id=%s',
        (pm25, pm10, no2, so2, co, o3, rid),
    )
    print('updated', rid, city, aqi)
conn.commit()
conn.close()
