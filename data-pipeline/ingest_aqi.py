"""AQI data ingestion module using WAQI API."""

import requests
import json
import config
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import execute_values
import time

class AQIIngestor:
    """Fetch AQI data from WAQI API."""
    
    def __init__(self):
        self.api_url = config.WAQI_API_URL
        self.api_key = config.WAQI_API_KEY
        self.cities = config.CITIES
        self.max_retries = getattr(config, 'MAX_RETRIES', 3)
        self.retry_backoff = getattr(config, 'RETRY_BACKOFF', 2)

    def fetch_aqi(self, city: str, retries: int = None) -> Optional[Dict]:
        """Fetch AQI data for a city from WAQI API."""
        if retries is None:
            retries = self.max_retries
            
        retry_count = 0
        backoff = 1

        while retry_count < retries:
            try:
                endpoint = f"{self.api_url}/{city}/?token={self.api_key}"
                response = requests.get(endpoint, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('status') == 'ok':
                        result = data.get('data', {})
                        
                        return {
                            'city': city,
                            'aqi': result.get('aqi'),
                            'pm25': result.get('iaqi', {}).get('pm25', {}).get('v'),
                            'pm10': result.get('iaqi', {}).get('pm10', {}).get('v'),
                            'no2': result.get('iaqi', {}).get('no2', {}).get('v'),
                            'o3': result.get('iaqi', {}).get('o3', {}).get('v'),
                            'so2': result.get('iaqi', {}).get('so2', {}).get('v'),
                            'co': result.get('iaqi', {}).get('co', {}).get('v'),
                            'temperature': result.get('iaqi', {}).get('t', {}).get('v'),
                            'humidity': result.get('iaqi', {}).get('h', {}).get('v'),
                            'wind_speed': result.get('iaqi', {}).get('w', {}).get('v'),
                            'pressure': result.get('iaqi', {}).get('p', {}).get('v'),
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    else:
                        return None
                
                elif response.status_code == 429:
                    # Rate limited
                    retry_count += 1
                    if retry_count < retries:
                        backoff *= self.retry_backoff
                        time.sleep(backoff)
                        continue
                    else:
                        return None
                
                else:
                    return None
                    
            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count < retries:
                    time.sleep(backoff)
                    backoff *= self.retry_backoff
                else:
                    return None
                    
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < retries:
                    time.sleep(backoff)
                    backoff *= self.retry_backoff
                else:
                    return None

    def ingest_aqi_data(self, db_conn) -> Dict:
        """Ingest AQI data for all cities."""
        results = {
            'total_records': 0,
            'successful': 0,
            'failed': 0,
            'cities': {}
        }

        for city in self.cities:
            aqi_data = self.fetch_aqi(city)
            if aqi_data and aqi_data.get('aqi') is not None:
                try:
                    self._insert_aqi(db_conn, aqi_data)
                    results['successful'] += 1
                    results['cities'][city] = 'success'
                except Exception as e:
                    print(f"Error inserting AQI for {city}: {e}")
                    results['failed'] += 1
                    results['cities'][city] = f'error: {str(e)}'
            else:
                results['failed'] += 1
                results['cities'][city] = 'no data'

            results['total_records'] += 1

        return results

    def _insert_aqi(self, db_conn, aqi_data: Dict):
        """Insert AQI data into database with all WAQI fields."""
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                '''
                INSERT INTO aqi_data (
                    city, aqi, category, pm25, pm10, no2, o3, so2, co,
                    temperature, humidity, wind_speed, pressure,
                    recorded_at, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ''',
                (
                    aqi_data['city'],
                    int(aqi_data['aqi']) if aqi_data.get('aqi') else 0,
                    self._categorize_aqi(int(aqi_data['aqi']) if aqi_data.get('aqi') else 0),
                    aqi_data.get('pm25'),
                    aqi_data.get('pm10'),
                    aqi_data.get('no2'),
                    aqi_data.get('o3'),
                    aqi_data.get('so2'),
                    aqi_data.get('co'),
                    aqi_data.get('temperature'),
                    aqi_data.get('humidity'),
                    aqi_data.get('wind_speed'),
                    aqi_data.get('pressure'),
                    aqi_data.get('timestamp')
                )
            )
            db_conn.commit()
        except psycopg2.Error as e:
            db_conn.rollback()
            raise e

    @staticmethod
    def _categorize_aqi(aqi: int) -> str:
        """Categorize AQI value."""
        if aqi <= 50:
            return 'Good'
        elif aqi <= 100:
            return 'Satisfactory'
        elif aqi <= 150:
            return 'Moderately Polluted'
        elif aqi <= 200:
            return 'Heavily Polluted'
        else:
            return 'Severely Polluted'
