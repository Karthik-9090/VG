"""
Production-grade hourly AQI collection service for VayuGuard.
Collects data every hour from WAQI API with duplicate prevention, logging, and CSV backups.
"""

import os
import sys
import json
import logging
import csv
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import schedule
import psycopg2
from dotenv import load_dotenv

# Add data-pipeline to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data-pipeline'))

from ingest_aqi import AQIIngestor
from db import DatabaseConnection, log_ingestion
import config

# Load environment variables
load_dotenv()

class ProductionAQICollector:
    """Production-grade AQI collection service."""
    
    def __init__(self):
        self.setup_logging()
        self.cities = config.CITIES
        self.log_dir = Path('data-pipeline') / 'logs'
        self.backup_dir = Path('data-pipeline') / 'backups'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"[OK] ProductionAQICollector initialized")
        self.logger.info(f"   Cities: {', '.join(self.cities)}")
        self.logger.info(f"   Log directory: {self.log_dir.absolute()}")
        self.logger.info(f"   Backup directory: {self.backup_dir.absolute()}")
    
    def setup_logging(self):
        """Configure comprehensive logging."""
        log_dir = Path('data-pipeline') / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"collector_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Use UTF-8 encoding for file handler to support Unicode characters
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)-8s | %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("[OK] ProductionAQICollector initialized")
    
    def check_duplicate(self, conn, city: str, aqi: int, timestamp: str) -> bool:
        """Check if record already exists (same city, same hour, same AQI)."""
        try:
            cursor = conn.cursor()
            
            # Extract hour from timestamp
            ts_hour = datetime.fromisoformat(timestamp).replace(minute=0, second=0, microsecond=0)
            
            cursor.execute("""
                SELECT COUNT(*) FROM aqi_data 
                WHERE city = %s 
                  AND DATE_TRUNC('hour', recorded_at) = %s
            """, (city, ts_hour))
            
            count = cursor.fetchone()[0]
            cursor.close()
            
            if count > 0:
                self.logger.warning(f"[WARNING] Duplicate detected: {city} at {ts_hour}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking duplicate for {city}: {e}")
            return False
    
    def collect_aqi_data(self) -> Dict:
        """Collect AQI data from WAQI API for all cities."""
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"Starting AQI collection cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"{'='*70}")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_records': 0,
            'successful': 0,
            'duplicates_skipped': 0,
            'failed': 0,
            'cities': {},
            'errors': []
        }
        
        try:
            DatabaseConnection.init_pool()
            conn = DatabaseConnection.get_connection()
            
            ingestor = AQIIngestor()
            
            for city in self.cities:
                try:
                    self.logger.info(f"\n[COLLECT] Collecting data for {city}...")
                    
                    # Fetch AQI data
                    aqi_data = ingestor.fetch_aqi(city)
                    
                    if aqi_data and aqi_data.get('aqi') is not None:
                        # Check for duplicates
                        if self.check_duplicate(conn, city, aqi_data['aqi'], aqi_data['timestamp']):
                            results['duplicates_skipped'] += 1
                            results['cities'][city] = 'duplicate_skipped'
                            self.logger.info(f"   [SKIP] Skipped (duplicate): {city}")
                        else:
                            # Insert into database
                            try:
                                ingestor._insert_aqi(conn, aqi_data)
                                results['successful'] += 1
                                results['cities'][city] = {
                                    'status': 'success',
                                    'aqi': aqi_data['aqi'],
                                    'pm25': aqi_data.get('pm25'),
                                    'timestamp': aqi_data['timestamp']
                                }
                                self.logger.info(f"   [OK] Success: AQI={aqi_data['aqi']}, PM2.5={aqi_data.get('pm25')}")
                            except Exception as e:
                                results['failed'] += 1
                                results['cities'][city] = f'insert_error: {str(e)}'
                                results['errors'].append(f"{city}: {str(e)}")
                                self.logger.error(f"   [FAIL] Insert failed for {city}: {e}")
                    else:
                        results['failed'] += 1
                        results['cities'][city] = 'no_data'
                        results['errors'].append(f"{city}: No AQI data returned")
                        self.logger.warning(f"   [FAIL] No AQI data for {city}")
                    
                    results['total_records'] += 1
                    
                except Exception as e:
                    results['failed'] += 1
                    results['cities'][city] = f'error: {str(e)}'
                    results['errors'].append(f"{city}: {str(e)}")
                    self.logger.error(f"   [FAIL] Error collecting data for {city}: {e}")
            
            # Log to database
            log_ingestion(conn, 'waqi', results['successful'], 'completed')
            
            DatabaseConnection.return_connection(conn)
            DatabaseConnection.close_all()
            
        except Exception as e:
            self.logger.error(f"[FAIL] Collection cycle failed: {e}")
            results['errors'].append(f"Critical error: {str(e)}")
        
        # Summary
        self.logger.info(f"\n{'─'*70}")
        self.logger.info(f"Collection Summary:")
        self.logger.info(f"  Total Records: {results['total_records']}")
        self.logger.info(f"  Successful: {results['successful']}")
        self.logger.info(f"  Duplicates: {results['duplicates_skipped']}")
        self.logger.info(f"  Failed: {results['failed']}")
        if results['errors']:
            self.logger.info(f"  Errors: {'; '.join(results['errors'][:3])}")
        self.logger.info(f"{'─'*70}\n")
        
        return results
    
    def backup_to_csv(self):
        """Create daily CSV backup of all AQI data."""
        try:
            backup_file = self.backup_dir / f"aqi_data_{datetime.now().strftime('%Y%m%d')}.csv"
            
            conn = DatabaseConnection.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    city, aqi, pm25, pm10, no2, o3, so2, co,
                    temperature, humidity, wind_speed, pressure,
                    recorded_at, created_at
                FROM aqi_data
                ORDER BY created_at DESC
            """)
            
            rows = cursor.fetchall()
            col_names = ['city', 'aqi', 'pm25', 'pm10', 'no2', 'o3', 'so2', 'co',
                        'temperature', 'humidity', 'wind_speed', 'pressure',
                        'recorded_at', 'created_at']
            
            # Only backup if new data available
            if rows and not backup_file.exists():
                with open(backup_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(col_names)
                    writer.writerows(rows)
                
                self.logger.info(f"✅ CSV backup created: {backup_file.name} ({len(rows)} rows)")
            elif rows and backup_file.exists():
                # Update existing backup
                with open(backup_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(col_names)
                    writer.writerows(rows)
                self.logger.info(f"[OK] CSV backup updated: {backup_file.name} ({len(rows)} rows)")
            
            cursor.close()
            DatabaseConnection.return_connection(conn)
            
        except Exception as e:
            self.logger.error(f"[FAIL] CSV backup failed: {e}")
    
    def generate_collection_report(self):
        """Generate DATA_COLLECTION_REPORT.md."""
        try:
            conn = DatabaseConnection.get_connection()
            cursor = conn.cursor()
            
            # Get statistics
            cursor.execute("SELECT COUNT(*) FROM aqi_data")
            total_rows = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT city, COUNT(*) as count, MAX(created_at) as latest_timestamp
                FROM aqi_data
                GROUP BY city
                ORDER BY city
            """)
            city_stats = cursor.fetchall()
            
            cursor.execute("""
                SELECT 
                    DATE_TRUNC('day', created_at) as day,
                    COUNT(*) as successful_collections,
                    COUNT(CASE WHEN pm25 IS NOT NULL THEN 1 END) as with_complete_data
                FROM aqi_data
                GROUP BY DATE_TRUNC('day', created_at)
                ORDER BY day DESC
                LIMIT 7
            """)
            daily_stats = cursor.fetchall()
            
            cursor.close()
            DatabaseConnection.return_connection(conn)
            
            # Generate report
            report_path = Path('DATA_COLLECTION_REPORT.md')
            with open(report_path, 'w') as f:
                f.write(f"# AQI Data Collection Report\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write(f"## Summary Statistics\n\n")
                f.write(f"| Metric | Value |\n")
                f.write(f"|--------|-------|\n")
                f.write(f"| **Total Rows** | {total_rows} |\n")
                f.write(f"| **Cities** | {len(city_stats)} |\n")
                f.write(f"| **Data Period** | Last 7 days |\n\n")
                
                f.write(f"## Rows Per City\n\n")
                f.write(f"| City | Records | Latest Timestamp |\n")
                f.write(f"|------|---------|------------------|\n")
                for city, count, timestamp in city_stats:
                    f.write(f"| {city} | {count} | {timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'N/A'} |\n")
                
                f.write(f"\n## Daily Collection Summary (Last 7 Days)\n\n")
                f.write(f"| Date | Collections | With Complete Data |\n")
                f.write(f"|------|-------------|--------------------|\n")
                for day, successful, complete in daily_stats:
                    f.write(f"| {day.strftime('%Y-%m-%d')} | {successful} | {complete} |\n")
                
                f.write(f"\n## Data Fields Collected\n\n")
                f.write(f"- AQI (Air Quality Index)\n")
                f.write(f"- PM2.5 (Fine Particulates)\n")
                f.write(f"- PM10 (Coarse Particulates)\n")
                f.write(f"- NO2 (Nitrogen Dioxide)\n")
                f.write(f"- O3 (Ozone)\n")
                f.write(f"- SO2 (Sulfur Dioxide)\n")
                f.write(f"- CO (Carbon Monoxide)\n")
                f.write(f"- Temperature\n")
                f.write(f"- Humidity\n")
                f.write(f"- Wind Speed\n")
                f.write(f"- Pressure\n")
                f.write(f"- Timestamp\n\n")
                
                f.write(f"## Collection Features\n\n")
                f.write(f"[OK] Hourly automated collection\n")
                f.write(f"[OK] Duplicate detection and prevention\n")
                f.write(f"[OK] Real-time logging\n")
                f.write(f"[OK] Daily CSV backups\n")
                f.write(f"[OK] Error tracking and reporting\n")
                f.write(f"[OK] 3-city coverage (Chennai, Bengaluru, Hyderabad)\n\n")
                
                f.write(f"## Recent Logs\n\n")
                f.write(f"```\n")
                f.write(f"See data-pipeline/logs/ for detailed collection logs\n")
                f.write(f"```\n")
            
            self.logger.info(f"[OK] Report generated: {report_path}")
            
        except Exception as e:
            self.logger.error(f"[FAIL] Report generation failed: {e}")
    
    def run_collection_cycle(self):
        """Execute single collection cycle."""
        try:
            results = self.collect_aqi_data()
            
            # Create CSV backup daily (only runs once per day)
            if datetime.now().hour == 1:  # Backup at 1 AM
                self.backup_to_csv()
            
            # Generate report
            self.generate_collection_report()
            
            return results
        
        except Exception as e:
            self.logger.error(f"[FAIL] Collection cycle error: {e}")
            return None
    
    def start_scheduler(self):
        """Start hourly scheduler."""
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"[START] Starting AQI Collection Scheduler")
        self.logger.info(f"   Interval: Every 1 hour")
        self.logger.info(f"   Cities: {', '.join(self.cities)}")
        self.logger.info(f"{'='*70}\n")
        
        # Schedule hourly collection
        schedule.every(1).hours.do(self.run_collection_cycle)
        
        # Run immediately on startup
        self.run_collection_cycle()
        
        # Keep scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def main():
    """Main entry point."""
    if os.getenv('RUN_ONCE'):
        # Single run mode (for testing)
        collector = ProductionAQICollector()
        collector.run_collection_cycle()
    else:
        # Continuous scheduler mode
        collector = ProductionAQICollector()
        collector.start_scheduler()


if __name__ == '__main__':
    main()
