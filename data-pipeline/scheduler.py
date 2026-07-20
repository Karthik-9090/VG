"""Data pipeline scheduler for VayuGuard."""

import time
import os
import config
from ingest_aqi import AQIIngestor
from ingest_weather import WeatherIngestor
from db import DatabaseConnection, log_ingestion
from datetime import datetime
import schedule

def run_ingestion():
    """Run complete data ingestion pipeline."""
    print(f"[{datetime.now()}] Starting data ingestion pipeline...")
    
    conn = None
    try:
        # Initialize connection pool
        DatabaseConnection.init_pool()
        conn = DatabaseConnection.get_connection()
        
        # Ingest AQI data
        print("Ingesting AQI data...")
        aqi_ingestor = AQIIngestor()
        aqi_results = aqi_ingestor.ingest_aqi_data(conn)
        print(f"AQI ingestion results: {aqi_results}")
        log_ingestion(conn, 'waqi', aqi_results['successful'], 'completed')
        
        # Ingest weather data
        print("Ingesting weather data...")
        weather_ingestor = WeatherIngestor()
        weather_results = weather_ingestor.ingest_weather_data(conn)
        print(f"Weather ingestion results: {weather_results}")
        log_ingestion(conn, 'open_meteo', weather_results['successful'], 'completed')
        
        print(f"[{datetime.now()}] Data ingestion pipeline completed successfully")
        
    except Exception as e:
        print(f"[{datetime.now()}] Error during data ingestion: {e}")
        if conn:
            log_ingestion(conn, 'pipeline', 0, 'error', str(e))
    finally:
        if conn:
            DatabaseConnection.return_connection(conn)
        DatabaseConnection.close_all()

def schedule_ingestions():
    """Schedule recurring data ingestions."""
    # Schedule ingestion based on configured interval in hours
    schedule.every(config.INGESTION_INTERVAL).hours.do(run_ingestion)
    
    print(
        f"Data pipeline scheduler started. Ingestion interval: {config.INGESTION_INTERVAL} hours "
        f"({config.INGEST_INTERVAL_MINUTES} minutes)"
    )
    
    # Run pending jobs indefinitely
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def main():
    """Main entry point."""
    if os.getenv('RUN_ONCE'):
        # Single run mode for CI
        print('Data pipeline running in single-shot mode...')
        run_ingestion()
        print('Data pipeline run complete')
    else:
        # Continuous scheduler mode
        schedule_ingestions()

if __name__ == '__main__':
    main()
