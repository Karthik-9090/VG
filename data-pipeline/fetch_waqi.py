"""WAQI (World Air Quality Index) data ingestion module."""

import requests
import json
import config
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import execute_values
import time

class WAQIIngestor:
    """Fetch AQI data from WAQI API and store in PostgreSQL."""
    
    def __init__(self):
        self.api_url = config.WAQI_API_URL
        self.api_key = config.WAQI_API_KEY
        self.cities = config.CITIES
        self.max_retries = 3
        self.retry_backoff = 2

    def fetch_aqi(self, city: str, retries: int = None) -> Optional[Dict]:
        """
        Fetch AQI data for a city from WAQI API.
        
        Args:
            city: City name
            retries: Number of retry attempts
            
        Returns:
            Dictionary with AQI data or None if failed
        """
        if retries is None:
            retries = self.max_retries
            
        retry_count = 0
        backoff = 1

        while retry_count < retries:
            try:
                # WAQI endpoint format: city_name/
                endpoint = f"{self.api_url}/{city}/?token={self.api_key}"
                
                response = requests.get(
                    endpoint,
                    timeout=10
                )
                
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
                        print(f"WAQI API returned status: {data.get('status')} for {city}")
                        return None
                
                elif response.status_code == 429:
                    # Rate limited
                    retry_count += 1
                    if retry_count < retries:
                        backoff *= self.retry_backoff
                        time.sleep(backoff)
                        continue
                    else:
                        print(f"Rate limited for {city} after {retries} retries")
                        return None
                
                else:
                    print(f"WAQI API error {response.status_code} for {city}")
                    return None
                    
            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count < retries:
                    time.sleep(backoff)
                    backoff *= self.retry_backoff
                else:
                    print(f"Timeout for {city} after {retries} retries")
                    return None
                    
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < retries:
                    time.sleep(backoff)
                    backoff *= self.retry_backoff
                else:
                    print(f"Request failed for {city}: {e}")
                    return None

    def ingest_aqi_data(self, db_conn) -> Dict:
        """
        Ingest AQI data for all cities.
        
        Args:
            db_conn: PostgreSQL database connection
            
        Returns:
            Dictionary with ingestion statistics
        """
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
                    print(f"✓ {city}: AQI {aqi_data['aqi']}")
                except Exception as e:
                    print(f"✗ Error inserting AQI for {city}: {e}")
                    results['failed'] += 1
                    results['cities'][city] = f'error: {str(e)}'
            else:
                results['failed'] += 1
                results['cities'][city] = 'no data'
                print(f"✗ {city}: No AQI data")

            results['total_records'] += 1

        return results

    def _insert_aqi(self, db_conn, aqi_data: Dict):
        """
        Insert AQI data into database.
        
        Uses INSERT to add fresh records (prevents duplicates by timestamp).
        """
        cursor = db_conn.cursor()
        
        try:
            # Insert fresh record
            sql = """
            INSERT INTO aqi_data (
                city, aqi, category, pm25, pm10, no2, o3, so2, co, 
                temperature, humidity, wind_speed, pressure, recorded_at, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """
            
            # Determine AQI category based on AQI value
            aqi_val = aqi_data.get('aqi')
            if aqi_val is None:
                aqi_val = 0
            
            if aqi_val <= 50:
                category = 'Good'
            elif aqi_val <= 100:
                category = 'Satisfactory'
            elif aqi_val <= 200:
                category = 'Moderately Polluted'
            elif aqi_val <= 300:
                category = 'Heavily Polluted'
            else:
                category = 'Severely Polluted'
            
            cursor.execute(
                sql,
                (
                    aqi_data.get('city'),
                    aqi_val,
                    category,
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
            
        except Exception as e:
            db_conn.rollback()
            raise e
        finally:
            cursor.close()
