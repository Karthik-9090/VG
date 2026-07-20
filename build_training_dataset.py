#!/usr/bin/env python
"""Build training dataset from PostgreSQL aqi_data and weather_data."""

import os
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'vayuguard')
DB_USER = os.getenv('DB_USER', 'vayuguard_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'vayuguard_pass')

OUTPUT_FILE = 'final_dataset.csv'

def connect_to_db():
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except psycopg2.Error as e:
        print(f"ERROR: Cannot connect to database: {e}")
        return None

def fetch_aqi_data(conn):
    """Fetch AQI data from database."""
    query = """
    SELECT 
        id,
        city,
        aqi,
        category,
        timestamp
    FROM aqi_data
    ORDER BY timestamp ASC, city ASC
    """
    
    df = pd.read_sql(query, conn)
    print(f"✅ Fetched {len(df)} AQI records from aqi_data table")
    return df

def fetch_weather_data(conn):
    """Fetch weather data from database."""
    query = """
    SELECT 
        id,
        city,
        temperature,
        humidity,
        wind_speed,
        timestamp
    FROM weather_data
    ORDER BY timestamp ASC, city ASC
    """
    
    df = pd.read_sql(query, conn)
    print(f"✅ Fetched {len(df)} weather records from weather_data table")
    return df

def merge_datasets(aqi_df, weather_df):
    """Merge AQI and weather data."""
    
    # Convert timestamp to datetime
    aqi_df['timestamp'] = pd.to_datetime(aqi_df['timestamp'])
    weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp'])
    
    # Merge on city and timestamp
    merged = pd.merge(
        aqi_df,
        weather_df[['city', 'timestamp', 'temperature', 'humidity', 'wind_speed']],
        on=['city', 'timestamp'],
        how='left'
    )
    
    print(f"✅ Merged datasets: {len(merged)} records")
    return merged

def add_temporal_features(df):
    """Add temporal features."""
    
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['month'] = df['timestamp'].dt.month
    
    print(f"✅ Added temporal features")
    return df

def extract_pollutants(df):
    """Extract pollutant columns from category or use defaults."""
    
    # These columns might not exist in aqi_data table
    # Initialize with NaN for now
    if 'pm25' not in df.columns:
        df['pm25'] = np.nan
    if 'pm10' not in df.columns:
        df['pm10'] = np.nan
    if 'no2' not in df.columns:
        df['no2'] = np.nan
    if 'o3' not in df.columns:
        df['o3'] = np.nan
    if 'so2' not in df.columns:
        df['so2'] = np.nan
    if 'co' not in df.columns:
        df['co'] = np.nan
    if 'pressure' not in df.columns:
        df['pressure'] = np.nan
    
    print(f"✅ Initialized pollutant columns")
    return df

def build_final_dataset():
    """Build final training dataset."""
    
    print("="*80)
    print("BUILDING TRAINING DATASET")
    print("="*80)
    print()
    
    # Connect to database
    print("STEP 1: CONNECTING TO DATABASE")
    print("-"*80)
    conn = connect_to_db()
    if not conn:
        return False
    
    # Fetch data
    print("\nSTEP 2: FETCHING DATA")
    print("-"*80)
    aqi_df = fetch_aqi_data(conn)
    weather_df = fetch_weather_data(conn)
    conn.close()
    
    # Merge datasets
    print("\nSTEP 3: MERGING DATASETS")
    print("-"*80)
    df = merge_datasets(aqi_df, weather_df)
    
    # Add temporal features
    print("\nSTEP 4: ADDING TEMPORAL FEATURES")
    print("-"*80)
    df = add_temporal_features(df)
    
    # Extract pollutant columns
    print("\nSTEP 5: INITIALIZING POLLUTANT COLUMNS")
    print("-"*80)
    df = extract_pollutants(df)
    
    # Rename recorded_at
    print("\nSTEP 6: PREPARING OUTPUT COLUMNS")
    print("-"*80)
    df['recorded_at'] = df['timestamp']
    
    # Select final columns
    final_columns = [
        'city',
        'aqi',
        'pm25',
        'pm10',
        'no2',
        'o3',
        'so2',
        'co',
        'temperature',
        'humidity',
        'wind_speed',
        'pressure',
        'hour',
        'day_of_week',
        'month',
        'recorded_at'
    ]
    
    # Check for missing columns
    missing_cols = [col for col in final_columns if col not in df.columns]
    if missing_cols:
        print(f"⚠️  Missing columns: {missing_cols}")
        print("   These will be added as NaN columns")
        for col in missing_cols:
            df[col] = np.nan
    
    df_final = df[final_columns].copy()
    
    # Remove duplicates (keep first)
    print("\nSTEP 7: REMOVING DUPLICATES")
    print("-"*80)
    duplicates_before = len(df_final)
    df_final = df_final.drop_duplicates(subset=['city', 'recorded_at'], keep='first')
    duplicates_removed = duplicates_before - len(df_final)
    print(f"✅ Removed {duplicates_removed} duplicate records")
    
    # Sort by recorded_at and city
    df_final = df_final.sort_values(['recorded_at', 'city']).reset_index(drop=True)
    
    # Export to CSV
    print("\nSTEP 8: EXPORTING TO CSV")
    print("-"*80)
    try:
        df_final.to_csv(OUTPUT_FILE, index=False)
        print(f"✅ Exported to {OUTPUT_FILE}")
        print(f"   Rows: {len(df_final)}")
        print(f"   Columns: {len(df_final.columns)}")
    except Exception as e:
        print(f"❌ Error writing CSV: {e}")
        return False
    
    # Dataset statistics
    print("\nSTEP 9: DATASET STATISTICS")
    print("-"*80)
    print(f"Total rows: {len(df_final)}")
    print(f"Date range: {df_final['recorded_at'].min()} to {df_final['recorded_at'].max()}")
    print(f"Cities: {df_final['city'].nunique()}")
    print(f"  {df_final['city'].value_counts().to_dict()}")
    print()
    print("Missing values per column:")
    for col in df_final.columns:
        missing_count = df_final[col].isna().sum()
        missing_pct = (missing_count / len(df_final)) * 100
        if missing_count > 0:
            print(f"  {col}: {missing_count} ({missing_pct:.1f}%)")
    
    print()
    print("="*80)
    print("DATASET BUILD COMPLETE")
    print("="*80)
    
    return df_final

if __name__ == '__main__':
    df = build_final_dataset()
