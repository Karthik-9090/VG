#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432, database='vayuguard',
    user='postgres', password=''
)
cursor = conn.cursor()

cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'engineered_features' 
    ORDER BY ordinal_position
""")

print("Engineered Features Table Schema:\n")
print(f"{'Column Name':<30} | {'Data Type':<15}")
print("-" * 50)
for col_name, data_type in cursor.fetchall():
    print(f"{col_name:<30} | {data_type:<15}")

conn.close()
