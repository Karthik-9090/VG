import psycopg2

conn = psycopg2.connect(host='localhost', database='vayuguard', user='postgres')
cur = conn.cursor()

cur.execute("""
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'aqi_historical' 
ORDER BY ordinal_position
""")

print("aqi_historical columns:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
