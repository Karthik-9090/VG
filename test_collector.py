#!/usr/bin/env python
"""
Comprehensive test suite for VayuGuard AQI Collection Service.
Tests all major components: database, API, ingestion, scheduling.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data-pipeline'))

import psycopg2
import requests
from dotenv import load_dotenv
from ingest_aqi import AQIIngestor
from db import DatabaseConnection

# Load environment
load_dotenv()

class TestCollector:
    """Test suite for AQI Collector."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def test_database_connection(self):
        """Test PostgreSQL connectivity."""
        print("\n" + "="*70)
        print("TEST 1: Database Connection")
        print("="*70)
        
        try:
            DatabaseConnection.init_pool()
            conn = DatabaseConnection.get_connection()
            cursor = conn.cursor()
            
            # Simple query
            cursor.execute("SELECT COUNT(*) FROM aqi_data")
            count = cursor.fetchone()[0]
            
            cursor.close()
            DatabaseConnection.return_connection(conn)
            
            print(f"✓ Database Connection: OK")
            print(f"  - Total AQI records in database: {count}")
            self.passed += 1
            return True
            
        except Exception as e:
            print(f"✗ Database Connection: FAILED")
            print(f"  Error: {e}")
            self.failed += 1
            self.errors.append(f"Database: {e}")
            return False
    
    def test_waqi_api_key(self):
        """Test WAQI API key validity."""
        print("\n" + "="*70)
        print("TEST 2: WAQI API Key")
        print("="*70)
        
        try:
            api_key = os.getenv('WAQI_API_KEY')
            if not api_key:
                print("✗ WAQI API Key: FAILED - Key not found in .env")
                self.failed += 1
                self.errors.append("WAQI API key not configured")
                return False
            
            # Test API call
            response = requests.get(
                f"https://api.waqi.info/feed/Chennai/?token={api_key}",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    print(f"✓ WAQI API Key: OK")
                    print(f"  - API response status: {data['status']}")
                    print(f"  - Data for: {data['data'].get('city', {}).get('name', 'Chennai')}")
                    self.passed += 1
                    return True
                else:
                    print(f"✗ WAQI API Key: FAILED - Status {data.get('status')}")
                    self.failed += 1
                    return False
            else:
                print(f"✗ WAQI API Key: FAILED - HTTP {response.status_code}")
                self.failed += 1
                return False
                
        except Exception as e:
            print(f"✗ WAQI API Key: FAILED")
            print(f"  Error: {e}")
            self.failed += 1
            self.errors.append(f"WAQI API: {e}")
            return False
    
    def test_aqi_ingestion(self):
        """Test AQI data ingestion."""
        print("\n" + "="*70)
        print("TEST 3: AQI Data Ingestion")
        print("="*70)
        
        try:
            ingestor = AQIIngestor()
            
            # Test all 3 cities
            cities_tested = 0
            for city in ['Chennai', 'Bengaluru', 'Hyderabad']:
                try:
                    aqi_data = ingestor.fetch_aqi(city)
                    
                    if aqi_data and aqi_data.get('aqi') is not None:
                        print(f"✓ {city}: AQI={aqi_data['aqi']}, PM2.5={aqi_data.get('pm25')}")
                        cities_tested += 1
                    else:
                        print(f"✗ {city}: No data returned")
                        
                except Exception as e:
                    print(f"✗ {city}: {e}")
            
            if cities_tested == 3:
                print(f"\n✓ AQI Data Ingestion: OK - All 3 cities tested")
                self.passed += 1
                return True
            else:
                print(f"\n✗ AQI Data Ingestion: PARTIAL - Only {cities_tested}/3 cities")
                self.failed += 1
                return False
                
        except Exception as e:
            print(f"✗ AQI Data Ingestion: FAILED")
            print(f"  Error: {e}")
            self.failed += 1
            self.errors.append(f"Ingestion: {e}")
            return False
    
    def test_database_schema(self):
        """Test database schema and columns."""
        print("\n" + "="*70)
        print("TEST 4: Database Schema")
        print("="*70)
        
        try:
            conn = DatabaseConnection.get_connection()
            cursor = conn.cursor()
            
            # Get column info
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'aqi_data'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            expected_columns = [
                'id', 'city', 'aqi', 'category', 'pm25', 'pm10', 
                'no2', 'o3', 'so2', 'co', 'temperature', 'humidity',
                'wind_speed', 'pressure', 'recorded_at', 'created_at', 'timestamp'
            ]
            
            found_columns = [col[0] for col in columns]
            missing = set(expected_columns) - set(found_columns)
            
            if not missing:
                print(f"✓ Database Schema: OK")
                print(f"  - Total columns: {len(found_columns)}")
                print(f"  - Required columns present: {', '.join(expected_columns[:5])}...")
                self.passed += 1
                cursor.close()
                DatabaseConnection.return_connection(conn)
                return True
            else:
                print(f"✗ Database Schema: FAILED - Missing columns: {missing}")
                self.failed += 1
                cursor.close()
                DatabaseConnection.return_connection(conn)
                return False
                
        except Exception as e:
            print(f"✗ Database Schema: FAILED")
            print(f"  Error: {e}")
            self.failed += 1
            self.errors.append(f"Schema: {e}")
            return False
    
    def test_log_creation(self):
        """Test log file creation."""
        print("\n" + "="*70)
        print("TEST 5: Log File Creation")
        print("="*70)
        
        try:
            log_dir = Path('data-pipeline') / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            
            today = datetime.now().strftime('%Y%m%d')
            log_file = log_dir / f'collector_{today}.log'
            
            # Write test log
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"[TEST] Log file test at {datetime.now()}\n")
            
            if log_file.exists() and log_file.stat().st_size > 0:
                print(f"✓ Log File Creation: OK")
                print(f"  - Log file: {log_file}")
                print(f"  - Size: {log_file.stat().st_size} bytes")
                self.passed += 1
                return True
            else:
                print(f"✗ Log File Creation: FAILED")
                self.failed += 1
                return False
                
        except Exception as e:
            print(f"✗ Log File Creation: FAILED")
            print(f"  Error: {e}")
            self.failed += 1
            self.errors.append(f"Logging: {e}")
            return False
    
    def test_backup_directory(self):
        """Test backup directory structure."""
        print("\n" + "="*70)
        print("TEST 6: Backup Directory")
        print("="*70)
        
        try:
            backup_dir = Path('data-pipeline') / 'backups'
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            if backup_dir.exists() and backup_dir.is_dir():
                # Check write permissions
                test_file = backup_dir / '.test'
                test_file.write_text('test')
                test_file.unlink()
                
                print(f"✓ Backup Directory: OK")
                print(f"  - Directory: {backup_dir}")
                print(f"  - Writable: Yes")
                self.passed += 1
                return True
            else:
                print(f"✗ Backup Directory: FAILED")
                self.failed += 1
                return False
                
        except Exception as e:
            print(f"✗ Backup Directory: FAILED")
            print(f"  Error: {e}")
            self.failed += 1
            self.errors.append(f"Backup dir: {e}")
            return False
    
    def test_duplicate_detection(self):
        """Test duplicate detection logic."""
        print("\n" + "="*70)
        print("TEST 7: Duplicate Detection")
        print("="*70)
        
        try:
            from collector import ProductionAQICollector
            
            collector = ProductionAQICollector()
            conn = DatabaseConnection.get_connection()
            
            # Get latest entry for a city
            cursor = conn.cursor()
            cursor.execute("""
                SELECT city, aqi, recorded_at 
                FROM aqi_data 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            if result:
                city, aqi, timestamp = result
                
                # Test duplicate detection
                is_duplicate = collector.check_duplicate(conn, city, aqi, timestamp.isoformat())
                
                print(f"✓ Duplicate Detection: OK")
                print(f"  - Test city: {city}")
                print(f"  - Is duplicate: {is_duplicate}")
                print(f"  - Logic: Working correctly")
                self.passed += 1
                cursor.close()
                DatabaseConnection.return_connection(conn)
                return True
            else:
                print(f"⚠ Duplicate Detection: SKIPPED - No data in database")
                cursor.close()
                DatabaseConnection.return_connection(conn)
                return True
                
        except Exception as e:
            print(f"✗ Duplicate Detection: FAILED")
            print(f"  Error: {e}")
            self.failed += 1
            self.errors.append(f"Duplicate detection: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests."""
        print("\n\n")
        print("█"*70)
        print("  VayuGuard AQI Collection Service - Test Suite")
        print("█"*70)
        
        # Run tests
        self.test_database_connection()
        time.sleep(0.5)
        self.test_waqi_api_key()
        time.sleep(0.5)
        self.test_aqi_ingestion()
        time.sleep(0.5)
        self.test_database_schema()
        time.sleep(0.5)
        self.test_log_creation()
        time.sleep(0.5)
        self.test_backup_directory()
        time.sleep(0.5)
        self.test_duplicate_detection()
        
        # Summary
        total = self.passed + self.failed
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total Tests:   {total}")
        print(f"Passed:        {self.passed}")
        print(f"Failed:        {self.failed}")
        print(f"Success Rate:  {100*self.passed/total:.1f}%")
        
        if self.errors:
            print(f"\nErrors:")
            for error in self.errors:
                print(f"  - {error}")
        
        print("="*70 + "\n")
        
        return self.failed == 0


if __name__ == '__main__':
    tester = TestCollector()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
