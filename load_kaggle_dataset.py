#!/usr/bin/env python3
"""
Load Kaggle AQI dataset into PostgreSQL aqi_historical table
With verification and reporting
"""

import pandas as pd
import psycopg2
from psycopg2 import sql
from datetime import datetime
import json

print("\n" + "="*80)
print("LOADING KAGGLE DATASET INTO POSTGRESQL")
print("="*80)
print(f"Load Time: {datetime.now().isoformat()}\n")

# Step 1: Load CSV dataset
print("STEP 1: Loading dataset from CSV...")
print("-" * 80)

try:
    df = pd.read_csv("indian_aqi_health_impact_2019_2024.csv")
    print(f"[OK] CSV loaded: {len(df):,} rows, {len(df.columns)} columns")
except Exception as e:
    print(f"[ERROR] Failed to load CSV: {str(e)}")
    exit(1)

# Step 2: Data cleaning
print("\nSTEP 2: Data Cleaning...")
print("-" * 80)

# Show initial state
print(f"Initial rows: {len(df):,}")
print(f"Duplicate rows before removal: {df.duplicated().sum():,}")

# Remove duplicates
df_clean = df.drop_duplicates().copy()
duplicates_removed = len(df) - len(df_clean)
print(f"Duplicate rows removed: {duplicates_removed:,}")
print(f"Rows after deduplication: {len(df_clean):,}")

# Handle missing values
print(f"\nMissing values by column:")
missing_cols = df_clean.isnull().sum()
for col, count in missing_cols[missing_cols > 0].items():
    pct = (count / len(df_clean)) * 100
    print(f"  {col}: {count:,} ({pct:.2f}%)")

# Fill missing values
df_clean['PM2.5'].fillna(df_clean['PM2.5'].mean(), inplace=True)
df_clean['Health_Impact_Score'].fillna(df_clean['Health_Impact_Score'].mean(), inplace=True)

print(f"Missing values after imputation: {df_clean.isnull().sum().sum():,}")

# Convert Date to datetime
df_clean['Date'] = pd.to_datetime(df_clean['Date'])

# Filter for target cities only
target_cities = ['Chennai', 'Bengaluru', 'Hyderabad']
df_target = df_clean[df_clean['City'].isin(target_cities)].copy()

print(f"\nFiltered for target cities:")
print(f"  Total rows: {len(df_target):,}")
for city in target_cities:
    count = len(df_target[df_target['City'] == city])
    print(f"  {city}: {count:,} rows")

# Step 3: Connect to PostgreSQL
print("\nSTEP 3: Connecting to PostgreSQL...")
print("-" * 80)

conn_params = {
    'host': 'localhost',
    'user': 'postgres',
    'password': 'postgres',
    'database': 'vayuguard',
    'port': 5432
}

try:
    conn = psycopg2.connect(**conn_params)
    print("[OK] Connected to PostgreSQL")
    print(f"  Host: {conn_params['host']}")
    print(f"  Database: {conn_params['database']}")
except Exception as e:
    print(f"[ERROR] Connection failed: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Ensure PostgreSQL is running")
    print("2. Verify credentials (user: postgres, password: postgres)")
    print("3. Check database 'vayuguard' exists")
    exit(1)

# Step 4: Create table
print("\nSTEP 4: Creating aqi_historical table...")
print("-" * 80)

cursor = conn.cursor()

# Drop table if exists
cursor.execute("DROP TABLE IF EXISTS aqi_historical CASCADE;")
print("[OK] Existing table dropped (if any)")

# Create table
create_table_sql = """
CREATE TABLE aqi_historical (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    city VARCHAR(50) NOT NULL,
    aqi INTEGER,
    pm2_5 FLOAT,
    pm10 FLOAT,
    no2 FLOAT,
    so2 FLOAT,
    co FLOAT,
    o3 FLOAT,
    temperature FLOAT,
    humidity FLOAT,
    wind_speed FLOAT,
    rainfall FLOAT,
    pressure FLOAT,
    vehicle_count INTEGER,
    industrial_activity_index FLOAT,
    health_impact_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(city, date)
);
"""

try:
    cursor.execute(create_table_sql)
    conn.commit()
    print("[OK] Table created successfully")
except Exception as e:
    print(f"[ERROR] Failed to create table: {str(e)}")
    conn.rollback()
    exit(1)

# Step 5: Insert data
print("\nSTEP 5: Inserting data into PostgreSQL...")
print("-" * 80)

insert_sql = """
INSERT INTO aqi_historical 
(date, city, aqi, pm2_5, pm10, no2, so2, co, o3, temperature, humidity, 
 wind_speed, rainfall, pressure, vehicle_count, industrial_activity_index, 
 health_impact_score)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (city, date) DO NOTHING;
"""

try:
    rows_inserted = 0
    rows_skipped = 0
    
    for idx, row in df_target.iterrows():
        try:
            cursor.execute(insert_sql, (
                row['Date'],
                row['City'],
                int(row['AQI']) if pd.notna(row['AQI']) else None,
                float(row['PM2.5']) if pd.notna(row['PM2.5']) else None,
                float(row['PM10']) if pd.notna(row['PM10']) else None,
                float(row['NO2']) if pd.notna(row['NO2']) else None,
                float(row['SO2']) if pd.notna(row['SO2']) else None,
                float(row['CO']) if pd.notna(row['CO']) else None,
                float(row['O3']) if pd.notna(row['O3']) else None,
                float(row['Temperature']) if pd.notna(row['Temperature']) else None,
                float(row['Humidity']) if pd.notna(row['Humidity']) else None,
                float(row['Wind_Speed']) if pd.notna(row['Wind_Speed']) else None,
                float(row['Rainfall']) if pd.notna(row['Rainfall']) else None,
                float(row['Pressure']) if pd.notna(row['Pressure']) else None,
                int(row['Vehicle_Count']) if pd.notna(row['Vehicle_Count']) else None,
                float(row['Industrial_Activity_Index']) if pd.notna(row['Industrial_Activity_Index']) else None,
                float(row['Health_Impact_Score']) if pd.notna(row['Health_Impact_Score']) else None,
            ))
            rows_inserted += 1
        except psycopg2.IntegrityError:
            rows_skipped += 1
            conn.rollback()
            continue
        except Exception as e:
            print(f"[WARNING] Row {idx} failed: {str(e)}")
            continue
        
        # Commit every 100 rows
        if rows_inserted % 100 == 0:
            conn.commit()
            print(f"  Progress: {rows_inserted:,} rows inserted...")
    
    conn.commit()
    print(f"[OK] Data insertion complete")
    print(f"  Rows inserted: {rows_inserted:,}")
    print(f"  Rows skipped (duplicates): {rows_skipped:,}")
    
except Exception as e:
    print(f"[ERROR] Insertion failed: {str(e)}")
    conn.rollback()
    exit(1)

# Step 6: Verification queries
print("\nSTEP 6: VERIFICATION QUERIES")
print("=" * 80)

verification_results = {}

# Query 1: Total row count
print("\nQUERY 1: SELECT COUNT(*) FROM aqi_historical;")
print("-" * 80)
cursor.execute("SELECT COUNT(*) as total_rows FROM aqi_historical;")
result = cursor.fetchone()
total_rows = result[0]
print(f"Total Rows: {total_rows:,}\n")
verification_results['total_rows'] = total_rows

# Query 2: Records per city
print("QUERY 2: SELECT city, COUNT(*) FROM aqi_historical GROUP BY city ORDER BY city;")
print("-" * 80)
cursor.execute("SELECT city, COUNT(*) as record_count FROM aqi_historical GROUP BY city ORDER BY city;")
results = cursor.fetchall()
print(f"{'City':<20} | {'Records':>10}")
print("-" * 35)
city_counts = {}
for city, count in results:
    print(f"{city:<20} | {count:>10,}")
    city_counts[city] = count
verification_results['city_counts'] = city_counts
print()

# Query 3: Date range
print("QUERY 3: SELECT MIN(date), MAX(date) FROM aqi_historical;")
print("-" * 80)
cursor.execute("SELECT MIN(date) as earliest_date, MAX(date) as latest_date FROM aqi_historical;")
result = cursor.fetchone()
min_date, max_date = result
date_range_days = (max_date - min_date).days
print(f"Earliest Date: {min_date}")
print(f"Latest Date: {max_date}")
print(f"Date Range: {date_range_days} days ({date_range_days/365:.2f} years)\n")
verification_results['date_range'] = {
    'min': str(min_date),
    'max': str(max_date),
    'days': date_range_days
}

# Query 4: Unique dates per city
print("QUERY 4: SELECT city, COUNT(DISTINCT date) FROM aqi_historical GROUP BY city;")
print("-" * 80)
cursor.execute("SELECT city, COUNT(DISTINCT date) as unique_dates FROM aqi_historical GROUP BY city ORDER BY city;")
results = cursor.fetchall()
print(f"{'City':<20} | {'Unique Dates':>15}")
print("-" * 40)
for city, count in results:
    print(f"{city:<20} | {count:>15,}")
print()

# Query 5: Data quality - null counts
print("QUERY 5: Check for NULL values in critical columns")
print("-" * 80)
cursor.execute("""
SELECT 
    COUNT(*) as total_rows,
    COUNT(aqi) as aqi_non_null,
    COUNT(*) - COUNT(aqi) as aqi_null,
    COUNT(pm2_5) as pm2_5_non_null,
    COUNT(*) - COUNT(pm2_5) as pm2_5_null,
    COUNT(health_impact_score) as health_score_non_null,
    COUNT(*) - COUNT(health_impact_score) as health_score_null
FROM aqi_historical;
""")
result = cursor.fetchone()
print(f"Total Rows: {result[0]:,}")
print(f"AQI - Non-Null: {result[1]:,}, Null: {result[2]:,}")
print(f"PM2.5 - Non-Null: {result[3]:,}, Null: {result[4]:,}")
print(f"Health Impact Score - Non-Null: {result[5]:,}, Null: {result[6]:,}\n")

# Query 6: Duplicates check (should be 0)
print("QUERY 6: Check for duplicate (city, date) combinations")
print("-" * 80)
cursor.execute("""
SELECT city, date, COUNT(*) as occurrence_count
FROM aqi_historical
GROUP BY city, date
HAVING COUNT(*) > 1;
""")
results = cursor.fetchall()
if results:
    print(f"WARNING: Found {len(results)} duplicate combinations")
    for row in results[:10]:
        print(f"  {row[0]} - {row[1]}: {row[2]} occurrences")
else:
    print("No duplicates found (0)")
print()

# Query 7: Target cities verification
print("QUERY 7: Verify target cities (Chennai, Bengaluru, Hyderabad)")
print("-" * 80)
target_cities_list = ['Chennai', 'Bengaluru', 'Hyderabad']
target_verification = {}
for city in target_cities_list:
    cursor.execute("""
    SELECT COUNT(*) as record_count,
           MIN(date) as earliest_date,
           MAX(date) as latest_date,
           AVG(aqi) as avg_aqi
    FROM aqi_historical
    WHERE city = %s;
    """, (city,))
    result = cursor.fetchone()
    record_count, earliest, latest, avg_aqi = result
    status = "[OK]" if record_count > 0 else "[MISSING]"
    print(f"\n{status} {city}")
    print(f"  Records: {record_count:,}")
    print(f"  Date Range: {earliest} to {latest}")
    print(f"  Average AQI: {avg_aqi:.1f}")
    target_verification[city] = {
        'records': record_count,
        'earliest': str(earliest),
        'latest': str(latest),
        'avg_aqi': float(avg_aqi) if avg_aqi else None
    }

print()

# Query 8: AQI statistics
print("QUERY 8: AQI Statistics")
print("-" * 80)
cursor.execute("""
SELECT 
    MIN(aqi) as min_aqi,
    MAX(aqi) as max_aqi,
    AVG(aqi) as avg_aqi,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY aqi) as median_aqi
FROM aqi_historical;
""")
result = cursor.fetchone()
print(f"Min AQI: {result[0]}")
print(f"Max AQI: {result[1]}")
print(f"Average AQI: {result[2]:.2f}")
print(f"Median AQI: {result[3]:.2f}\n")

# Query 9: Pollutant statistics
print("QUERY 9: Pollutant Statistics (for all records)")
print("-" * 80)
cursor.execute("""
SELECT 
    COUNT(pm2_5) as pm2_5_records,
    MIN(pm2_5) as pm2_5_min,
    AVG(pm2_5) as pm2_5_avg,
    MAX(pm2_5) as pm2_5_max,
    COUNT(pm10) as pm10_records,
    AVG(pm10) as pm10_avg,
    COUNT(no2) as no2_records,
    AVG(no2) as no2_avg
FROM aqi_historical;
""")
result = cursor.fetchone()
print(f"PM2.5: {result[0]:,} records | Min: {result[1]:.2f} | Avg: {result[2]:.2f} | Max: {result[3]:.2f}")
print(f"PM10: {result[4]:,} records | Avg: {result[5]:.2f}")
print(f"NO2: {result[6]:,} records | Avg: {result[7]:.2f}\n")

verification_results['target_cities'] = target_verification

# Close connection
cursor.close()
conn.close()

print("="*80)
print("IMPORT COMPLETE")
print("="*80)
print(f"\nSummary:")
print(f"  Total rows in aqi_historical: {total_rows:,}")
print(f"  Target cities: {', '.join(target_cities_list)}")
print(f"  All cities: {', '.join(city_counts.keys())}")
print(f"  Date range: {date_range_days} days ({date_range_days/365:.2f} years)")
print(f"  Duplicates removed during load: {duplicates_removed:,}")

# Save results
with open("import_verification.json", "w") as f:
    json.dump(verification_results, f, indent=2)

print(f"\nDetailed results saved to: import_verification.json")
print("="*80 + "\n")
