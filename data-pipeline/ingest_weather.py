"""Weather data ingestion module."""

import requests
import config
from datetime import datetime
from typing import Dict, Optional
import psycopg2

class WeatherIngestor:
    def __init__(self):
        self.api_url = config.OPEN_METEO_API_URL
        self.cities = config.CITIES
        self.coords = config.CITY_COORDS

    def fetch_weather(self, city: str, retries: int = config.MAX_RETRIES) -> Optional[Dict]:
        """Fetch weather data for a city."""
        if city not in self.coords:
            return None

        retry_count = 0
        backoff = 1
        coord = self.coords[city]

        while retry_count < retries:
            try:
                response = requests.get(
                    f"{self.api_url}/forecast",
                    params={
                        'latitude': coord['lat'],
                        'longitude': coord['lon'],
                        'current_weather': True,
                        'hourly': 'relativehumidity_2m',
                        'timezone': 'auto'
                    },
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

                if 'current_weather' in data:
                    current = data['current_weather']
                    humidity = 0
                    if 'hourly' in data and 'relativehumidity_2m' in data['hourly']:
                        times = data['hourly'].get('time', [])
                        humidities = data['hourly'].get('relativehumidity_2m', [])
                        if current.get('time') in times:
                            idx = times.index(current['time'])
                            humidity = humidities[idx] if idx < len(humidities) else 0

                    return {
                        'city': city,
                        'temperature': current.get('temperature', 0),
                        'humidity': humidity,
                        'wind_speed': current.get('windspeed', 0),
                        'timestamp': current.get('time')
                    }
                return None
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < retries:
                    import time
                    backoff *= config.RETRY_BACKOFF
                    time.sleep(backoff)
                else:
                    print(f"Failed to fetch weather for {city} after {retries} retries: {e}")
                    return None

    def ingest_weather_data(self, db_conn) -> Dict:
        """Ingest weather data for all cities."""
        results = {
            'total_records': 0,
            'successful': 0,
            'failed': 0,
            'cities': {}
        }

        for city in self.cities:
            weather_data = self.fetch_weather(city)
            if weather_data:
                try:
                    self._insert_weather(db_conn, weather_data)
                    results['successful'] += 1
                    results['cities'][city] = 'success'
                except Exception as e:
                    print(f"Error inserting weather for {city}: {e}")
                    results['failed'] += 1
                    results['cities'][city] = f'error: {str(e)}'
            else:
                results['failed'] += 1
                results['cities'][city] = 'no data'

            results['total_records'] += 1

        return results

    def _insert_weather(self, db_conn, weather_data: Dict):
        """Insert weather data into database."""
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                '''
                INSERT INTO weather_data (city, temperature, humidity, wind_speed, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                ''',
                (
                    weather_data['city'],
                    weather_data.get('temperature', 0),
                    weather_data.get('humidity', 0),
                    weather_data.get('wind_speed', 0),
                    weather_data.get('timestamp', datetime.utcnow().isoformat())
                )
            )
            db_conn.commit()
        except psycopg2.Error as e:
            db_conn.rollback()
            raise e
