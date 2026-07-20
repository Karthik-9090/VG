import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='vayuguard',
    user='vayuguard_user',
    password='vayuguard_pass'
)

cur = conn.cursor()

# Check existing indexes
cur.execute("""
    SELECT indexname, indexdef 
    FROM pg_indexes 
    WHERE tablename='aqi_data' 
    ORDER BY indexname
""")

indexes = cur.fetchall()
print("Existing indexes on aqi_data:")
for idx_name, idx_def in indexes:
    print(f"  {idx_name}: {idx_def}")

if not indexes:
    print("  (No indexes found)")

# Check table size and row count
cur.execute("SELECT COUNT(*) FROM aqi_data")
row_count = cur.fetchone()[0]
print(f"\nTable size: {row_count} rows")

# Estimate query plan for the current query
cur.execute("""
    EXPLAIN ANALYZE
    SELECT aqi, pm25, pm10, no2, so2, co, o3, recorded_at
    FROM aqi_data
    WHERE city = 'Chennai'
    ORDER BY recorded_at DESC
    LIMIT 1
""")

plan = cur.fetchall()
print("\nCurrent query plan (without index):")
for line in plan:
    print(f"  {line[0]}")

conn.close()
