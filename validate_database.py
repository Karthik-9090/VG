#!/usr/bin/env python
"""
Phase 2: Database Validation
Comprehensive database schema and data integrity checks
"""

import psycopg2
from psycopg2 import sql
import json
from datetime import datetime

# Connection parameters
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'vayuguard'
DB_USER = 'vayuguard_user'
DB_PASSWORD = 'vayuguard_pass'

def connect_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        return None

def run_validation():
    """Run comprehensive database validation"""
    
    conn = connect_db()
    if not conn:
        return False
    
    cursor = conn.cursor()
    results = {
        'timestamp': datetime.now().isoformat(),
        'database': DB_NAME,
        'host': DB_HOST,
        'validations': {}
    }
    
    try:
        # 1. Count aqi_historical
        print("\n1. Historical Data Count")
        cursor.execute("SELECT COUNT(*) FROM aqi_historical")
        count = cursor.fetchone()[0]
        results['validations']['aqi_historical_count'] = count
        print(f"   aqi_historical: {count} records")
        
        # 2. Count aqi_data
        print("\n2. Live Data Count")
        cursor.execute("SELECT COUNT(*) FROM aqi_data")
        count = cursor.fetchone()[0]
        results['validations']['aqi_data_count'] = count
        print(f"   aqi_data: {count} records")
        
        # 3. aqi_historical by city
        print("\n3. Historical Data Distribution by City")
        cursor.execute("""
        SELECT city, COUNT(*) as count 
        FROM aqi_historical 
        GROUP BY city 
        ORDER BY count DESC
        """)
        city_counts = cursor.fetchall()
        results['validations']['aqi_historical_by_city'] = {}
        for city, count in city_counts:
            print(f"   {city}: {count} records")
            results['validations']['aqi_historical_by_city'][city] = count
        
        # 4. aqi_data by city
        print("\n4. Live Data Distribution by City")
        cursor.execute("""
        SELECT city, COUNT(*) as count 
        FROM aqi_data 
        GROUP BY city 
        ORDER BY count DESC
        """)
        city_counts = cursor.fetchall()
        results['validations']['aqi_data_by_city'] = {}
        if cursor.rowcount > 0:
            for city, count in city_counts:
                print(f"   {city}: {count} records")
                results['validations']['aqi_data_by_city'][city] = count
        else:
            print("   (No live data yet - this is expected)")
        
        # 5. prediction_logs table check
        print("\n5. Prediction Logs Table")
        cursor.execute("""
        SELECT to_regclass('prediction_logs') IS NOT NULL
        """)
        exists = cursor.fetchone()[0]
        print(f"   Table exists: {'YES' if exists else 'NO'}")
        results['validations']['prediction_logs_exists'] = exists
        
        if exists:
            cursor.execute("SELECT COUNT(*) FROM prediction_logs")
            count = cursor.fetchone()[0]
            print(f"   Records in prediction_logs: {count}")
            results['validations']['prediction_logs_count'] = count
        
        # 6. Verify all required tables
        print("\n6. Required Tables Status")
        required_tables = [
            'users', 'health_profiles', 'aqi_data', 'weather_data',
            'forecasts', 'alerts', 'model_metadata', 'aqi_historical',
            'engineered_features', 'prediction_logs'
        ]
        results['validations']['tables'] = {}
        for table in required_tables:
            cursor.execute(f"SELECT to_regclass('{table}') IS NOT NULL")
            exists = cursor.fetchone()[0]
            status = 'PASS' if exists else 'MISSING'
            print(f"   {table}: {status}")
            results['validations']['tables'][table] = 'exists' if exists else 'missing'
        
        # 7. Check indexes on critical tables
        print("\n7. Indexes on Critical Tables")
        cursor.execute("""
        SELECT tablename, indexname 
        FROM pg_indexes 
        WHERE tablename IN ('aqi_historical', 'aqi_data', 'prediction_logs')
        ORDER BY tablename, indexname
        """)
        indexes = cursor.fetchall()
        results['validations']['indexes'] = {}
        for table, index in indexes:
            if table not in results['validations']['indexes']:
                results['validations']['indexes'][table] = []
            print(f"   {table}: {index}")
            results['validations']['indexes'][table].append(index)
        
        # 8. Check constraints
        print("\n8. Constraints on Critical Tables")
        cursor.execute("""
        SELECT table_name, constraint_name, constraint_type
        FROM information_schema.table_constraints
        WHERE table_name IN ('aqi_historical', 'aqi_data', 'users')
        ORDER BY table_name, constraint_name
        """)
        constraints = cursor.fetchall()
        results['validations']['constraints'] = {}
        for table, constraint, ctype in constraints:
            if table not in results['validations']['constraints']:
                results['validations']['constraints'][table] = []
            print(f"   {table}: {constraint} ({ctype})")
            results['validations']['constraints'][table].append(f"{constraint} ({ctype})")
        
        # 9. Data quality checks
        print("\n9. Data Quality Checks")
        
        # Check for NULL values in aqi_historical
        cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM aqi_historical WHERE aqi IS NULL) as null_aqi,
            (SELECT COUNT(*) FROM aqi_historical WHERE city IS NULL) as null_city,
            (SELECT COUNT(*) FROM aqi_historical WHERE date IS NULL) as null_date
        """)
        nulls = cursor.fetchone()
        results['validations']['data_quality'] = {
            'aqi_historical_null_aqi': nulls[0],
            'aqi_historical_null_city': nulls[1],
            'aqi_historical_null_date': nulls[2]
        }
        print(f"   aqi_historical NULL AQI: {nulls[0]}")
        print(f"   aqi_historical NULL city: {nulls[1]}")
        print(f"   aqi_historical NULL date: {nulls[2]}")
        
        # Check date range
        cursor.execute("""
        SELECT 
            MIN(date) as min_date, 
            MAX(date) as max_date,
            (MAX(date) - MIN(date)) as date_range_days
        FROM aqi_historical
        """)
        date_info = cursor.fetchone()
        results['validations']['date_range'] = {
            'min_date': str(date_info[0]),
            'max_date': str(date_info[1]),
            'range_days': int(date_info[2].days) if date_info[2] else 0
        }
        print(f"   Date range: {date_info[0]} to {date_info[1]}")
        print(f"   Duration: {date_info[2].days if date_info[2] else 0} days")
        
        # 10. Engineered features table
        print("\n10. Engineered Features Table")
        cursor.execute("SELECT COUNT(*) FROM engineered_features")
        count = cursor.fetchone()[0]
        print(f"   Records: {count}")
        results['validations']['engineered_features_count'] = count
        
        cursor.execute("""
        SELECT 
            COUNT(DISTINCT city) as distinct_cities,
            COUNT(DISTINCT date) as distinct_dates
        FROM engineered_features
        """)
        row = cursor.fetchone()
        print(f"   Distinct cities: {row[0]}")
        print(f"   Distinct dates: {row[1]}")
        results['validations']['engineered_features_cities'] = row[0]
        results['validations']['engineered_features_dates'] = row[1]
        
        # Final summary
        print("\n" + "="*60)
        print("DATABASE VALIDATION SUMMARY")
        print("="*60)
        
        # Check if all critical requirements met
        all_pass = True
        checks = [
            ('Historical data exists', results['validations']['aqi_historical_count'] > 0),
            ('Live data table exists', results['validations']['aqi_data_exists'] if 'aqi_data_exists' in results['validations'] else True),
            ('Prediction logs table exists', results['validations']['prediction_logs_exists']),
            ('Indexes on aqi_historical', len(results['validations']['indexes'].get('aqi_historical', [])) > 0),
            ('Constraints on aqi_historical', len(results['validations']['constraints'].get('aqi_historical', [])) > 0),
            ('No NULL aqi_historical values', results['validations']['data_quality']['aqi_historical_null_aqi'] == 0),
            ('Engineered features populated', results['validations']['engineered_features_count'] > 0),
        ]
        
        for check_name, check_result in checks:
            status = 'PASS' if check_result else 'FAIL'
            print(f"{check_name}: {status}")
            if not check_result:
                all_pass = False
        
        results['overall_status'] = 'PASS' if all_pass else 'FAIL'
        
    except Exception as e:
        print(f"ERROR during validation: {e}")
        results['overall_status'] = 'ERROR'
        results['error'] = str(e)
    finally:
        cursor.close()
        conn.close()
    
    return results

if __name__ == '__main__':
    results = run_validation()
    print(f"\n\nValidation Status: {results.get('overall_status', 'UNKNOWN')}")
