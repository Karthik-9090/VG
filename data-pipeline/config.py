import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'vayuguard')
DB_USER = os.getenv('DB_USER', 'vayuguard_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'vayuguard_pass')

# Data ingestion configuration
CITIES = ['Chennai', 'Bengaluru', 'Hyderabad']
WAQI_API_URL = 'https://api.waqi.info/feed'
WAQI_API_KEY = os.getenv('WAQI_API_KEY', '')
# Correct Open-Meteo base URL (remove erroneous '-py' subdomain)
OPEN_METEO_API_URL = 'https://api.open-meteo.com/v1'

# Coordinates for cities
CITY_COORDS = {
    'Chennai': {'lat': 13.0827, 'lon': 80.2707},
    'Bengaluru': {'lat': 12.9716, 'lon': 77.5946},
    'Hyderabad': {'lat': 17.3850, 'lon': 78.4867}
}

# Ingestion schedule (in minutes). Default is 5 minutes.
INGEST_INTERVAL_MINUTES = int(os.getenv('INGEST_INTERVAL_MINUTES', 5))
INGESTION_INTERVAL = INGEST_INTERVAL_MINUTES / 60

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # exponential backoff multiplier
