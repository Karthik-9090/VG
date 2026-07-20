#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432, database='vayuguard',
    user='postgres', password=''
)
cursor = conn.cursor()

# Check if index exists
print("[1] Checking if index exists...")
cursor.execute("""
    SELECT indexname FROM pg_indexes 
    WHERE tablename = 'engineered_features' 
    AND indexname = 'idx_engineered_features_city_date'
""")
result = cursor.fetchone()
if result:
    print(f"    ✓ Index exists: {result[0]}")
else:
    print(f"    ✗ Index does not exist")

# Check all indexes on table
print("\n[2] All indexes on engineered_features:")
cursor.execute("""
    SELECT indexname FROM pg_indexes 
    WHERE tablename = 'engineered_features'
    ORDER BY indexname
""")
for row in cursor.fetchall():
    print(f"    - {row[0]}")

# Check table size and row count
print("\n[3] Table statistics:")
cursor.execute("SELECT COUNT(*) FROM engineered_features")
row_count = cursor.fetchone()[0]
print(f"    Rows: {row_count:,}")

# Run EXPLAIN with more details
print("\n[4] EXPLAIN ANALYZE (with BUFFERS):")
query = """
SELECT lag_1, lag_3, lag_6
FROM engineered_features
WHERE city = 'Chennai'
ORDER BY date DESC
LIMIT 1
"""
explain_sql = f"EXPLAIN (ANALYZE, BUFFERS) {query}"
cursor.execute(explain_sql)

for row in cursor.fetchall():
    print(f"    {row[0]}")

cursor.close()
conn.close()
