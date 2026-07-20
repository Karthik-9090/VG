"""Phase 3: Data Quality Validation"""

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data-pipeline'))

import psycopg2
from dotenv import load_dotenv
from db import DatabaseConnection

load_dotenv()

print("="*80)
print("PHASE 3: DATA QUALITY VALIDATION")
print(f"Timestamp: {datetime.now().isoformat()}")
print("="*80)
print()

try:
    DatabaseConnection.init_pool()
    conn = DatabaseConnection.get_connection()
    cursor = conn.cursor()
    
    # 1. Record Count
    print("[1/8] RECORD COUNT")
    print("-"*80)
    cursor.execute("SELECT COUNT(*) FROM aqi_data;")
    total = cursor.fetchone()[0]
    print(f"Total records: {total}")
    print()
    
    # 2. City Distribution
    print("[2/8] CITY DISTRIBUTION")
    print("-"*80)
    cursor.execute("""
        SELECT city, COUNT(*) as count, ROUND(100.0*COUNT(*)/{}, 1) as pct
        FROM aqi_data
        GROUP BY city
        ORDER BY count DESC;
    """.format(total if total > 0 else 1))
    
    cities = cursor.fetchall()
    for city, count, pct in cities:
        print(f"{city:15} {count:4} records ({pct:5.1f}%)")
    print()
    
    # 3. Missing Values (NULL)
    print("[3/8] MISSING VALUES (NULL)")
    print("-"*80)
    cursor.execute("""
        SELECT
            COUNT(CASE WHEN city IS NULL THEN 1 END) as null_city,
            COUNT(CASE WHEN aqi IS NULL THEN 1 END) as null_aqi,
            COUNT(CASE WHEN pm25 IS NULL THEN 1 END) as null_pm25,
            COUNT(CASE WHEN pm10 IS NULL THEN 1 END) as null_pm10,
            COUNT(CASE WHEN no2 IS NULL THEN 1 END) as null_no2,
            COUNT(CASE WHEN o3 IS NULL THEN 1 END) as null_o3,
            COUNT(CASE WHEN so2 IS NULL THEN 1 END) as null_so2,
            COUNT(CASE WHEN co IS NULL THEN 1 END) as null_co,
            COUNT(CASE WHEN temperature IS NULL THEN 1 END) as null_temp,
            COUNT(CASE WHEN humidity IS NULL THEN 1 END) as null_humidity,
            COUNT(CASE WHEN wind_speed IS NULL THEN 1 END) as null_wind,
            COUNT(CASE WHEN pressure IS NULL THEN 1 END) as null_pressure
        FROM aqi_data;
    """)
    
    nulls = cursor.fetchone()
    fields = ['City', 'AQI', 'PM2.5', 'PM10', 'NO2', 'O3', 'SO2', 'CO', 'Temperature', 'Humidity', 'Wind', 'Pressure']
    
    null_count = 0
    for field, null_val in zip(fields, nulls):
        if null_val > 0:
            print(f"{field:15} {null_val:4} NULL values")
            null_count += 1
    
    if null_count == 0:
        print("No NULL values found in critical fields")
    print()
    
    # 4. Duplicate Records
    print("[4/8] DUPLICATE DETECTION")
    print("-"*80)
    cursor.execute("""
        SELECT
            city,
            recorded_at,
            COUNT(*) as occurrences
        FROM aqi_data
        GROUP BY city, recorded_at
        HAVING COUNT(*) > 1
        ORDER BY occurrences DESC;
    """)
    
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"Found {len(duplicates)} duplicate records:")
        for city, recorded_at, count in duplicates:
            print(f"  {city:15} {recorded_at} - {count} occurrences")
    else:
        print("No duplicate records detected (by city + timestamp)")
    print()
    
    # 5. AQI Value Validation
    print("[5/8] AQI VALUE VALIDATION")
    print("-"*80)
    cursor.execute("""
        SELECT
            MIN(aqi) as min_aqi,
            MAX(aqi) as max_aqi,
            AVG(aqi) as avg_aqi,
            COUNT(CASE WHEN aqi < 0 THEN 1 END) as invalid_negative,
            COUNT(CASE WHEN aqi > 500 THEN 1 END) as invalid_over_500
        FROM aqi_data;
    """)
    
    aqi_stats = cursor.fetchone()
    min_aqi, max_aqi, avg_aqi, neg_count, over_500 = aqi_stats
    
    print(f"AQI Range:        {min_aqi} to {max_aqi}")
    print(f"AQI Average:      {avg_aqi:.1f}")
    print(f"Invalid (< 0):    {neg_count}")
    print(f"Invalid (> 500):  {over_500}")
    
    if neg_count == 0 and over_500 == 0 and 0 <= min_aqi and max_aqi <= 500:
        print("Status: All AQI values valid (0-500 range)")
    else:
        print("Status: INVALID AQI values detected")
    print()
    
    # 6. Weather Value Validation
    print("[6/8] WEATHER VALUE VALIDATION")
    print("-"*80)
    cursor.execute("""
        SELECT
            COUNT(CASE WHEN temperature < -50 OR temperature > 60 THEN 1 END) as invalid_temp,
            COUNT(CASE WHEN humidity < 0 OR humidity > 100 THEN 1 END) as invalid_humidity,
            COUNT(CASE WHEN wind_speed < 0 OR wind_speed > 100 THEN 1 END) as invalid_wind,
            COUNT(CASE WHEN pressure < 900 OR pressure > 1100 THEN 1 END) as invalid_pressure
        FROM aqi_data;
    """)
    
    weather_invalid = cursor.fetchone()
    temp_inv, humid_inv, wind_inv, press_inv = weather_invalid
    
    print(f"Invalid Temperature: {temp_inv}")
    print(f"Invalid Humidity:    {humid_inv}")
    print(f"Invalid Wind Speed:  {wind_inv}")
    print(f"Invalid Pressure:    {press_inv}")
    
    total_invalid = sum(weather_invalid)
    if total_invalid == 0:
        print("Status: All weather values valid")
    else:
        print(f"Status: {total_invalid} invalid weather values")
    print()
    
    # 7. Timestamp Validation
    print("[7/8] TIMESTAMP VALIDATION")
    print("-"*80)
    cursor.execute("""
        SELECT
            MIN(created_at) as earliest,
            MAX(created_at) as latest,
            COUNT(CASE WHEN created_at > NOW() THEN 1 END) as future_dates,
            COUNT(CASE WHEN created_at < NOW() - INTERVAL '30 days' THEN 1 END) as older_30days
        FROM aqi_data;
    """)
    
    ts_stats = cursor.fetchone()
    earliest, latest, future, old = ts_stats
    
    print(f"Earliest:         {earliest}")
    print(f"Latest:           {latest}")
    print(f"Future dates:     {future}")
    print(f"Older than 30d:   {old}")
    print("Status: Timestamps valid" if future == 0 else "Status: Future dates detected (ERROR)")
    print()
    
    # 8. Data Completeness
    print("[8/8] DATA COMPLETENESS")
    print("-"*80)
    cursor.execute("""
        SELECT
            COUNT(*) as total_records,
            COUNT(CASE WHEN aqi IS NOT NULL THEN 1 END) as with_aqi,
            COUNT(CASE WHEN pm25 IS NOT NULL THEN 1 END) as with_pm25,
            COUNT(CASE WHEN temperature IS NOT NULL THEN 1 END) as with_temp
        FROM aqi_data;
    """)
    
    completeness = cursor.fetchone()
    total, aqi_count, pm25_count, temp_count = completeness
    
    aqi_pct = 100 * aqi_count / total if total > 0 else 0
    pm25_pct = 100 * pm25_count / total if total > 0 else 0
    temp_pct = 100 * temp_count / total if total > 0 else 0
    
    print(f"Records with AQI:        {aqi_count}/{total} ({aqi_pct:.1f}%)")
    print(f"Records with PM2.5:      {pm25_count}/{total} ({pm25_pct:.1f}%)")
    print(f"Records with Temp:       {temp_count}/{total} ({temp_pct:.1f}%)")
    
    avg_completeness = (aqi_pct + pm25_pct + temp_pct) / 3
    print(f"Average Completeness:    {avg_completeness:.1f}%")
    print()
    
    cursor.close()
    DatabaseConnection.return_connection(conn)
    
    # Summary
    print("="*80)
    print("PHASE 3 SUMMARY")
    print("="*80)
    print()
    print(f"Total Records:           {total}")
    print(f"Cities:                  {len(cities)}")
    print(f"Null Values:             {null_count}")
    print(f"Duplicate Records:       {len(duplicates)}")
    print(f"Invalid AQI Values:      {neg_count + over_500}")
    print(f"Invalid Weather Values:  {total_invalid}")
    print(f"Future Dates:            {future}")
    print(f"Data Completeness:       {avg_completeness:.1f}%")
    print()
    
    if null_count == 0 and len(duplicates) == 0 and (neg_count + over_500) == 0 and total_invalid == 0 and future == 0:
        print("[PASS] PHASE 3: DATA QUALITY VALIDATION - SUCCESS")
        quality_score = "EXCELLENT"
    elif (neg_count + over_500) > 0 or total_invalid > 0:
        print("[FAIL] PHASE 3: DATA QUALITY VALIDATION - INVALID DATA DETECTED")
        quality_score = "POOR"
    else:
        print("[PASS] PHASE 3: DATA QUALITY VALIDATION - ACCEPTABLE")
        quality_score = "GOOD"
    
    print(f"Quality Score:           {quality_score}")
    print("="*80)

except Exception as e:
    print()
    print("="*80)
    print(f"[FAIL] PHASE 3: DATA QUALITY VALIDATION")
    print(f"Error: {e}")
    print("="*80)
    exit(1)
