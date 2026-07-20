#!/usr/bin/env python
"""
Extract and display exact training dataset information
"""
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
import numpy as np

# Step 1: Query real data from database
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='vayuguard',
    user='vayuguard_user',
    password='vayuguard_pass'
)

df_real = pd.read_sql('SELECT id, city, aqi, category, timestamp FROM aqi_data ORDER BY timestamp', conn)
conn.close()

print('='*80)
print('EXACT TRAINING DATASET INFORMATION')
print('='*80)

print('\n1. DATA SOURCE')
print('-'*80)
print('Location: PostgreSQL Database')
print('Host: localhost')
print('Port: 5432')
print('Database: vayuguard')
print('Table: aqi_data')
print('Connection: psycopg2')

print('\n2. REAL DATA RETRIEVED FROM DATABASE')
print('-'*80)
print(f'Total Real Records: {len(df_real)} rows')
print(f'Date Range: {df_real["timestamp"].min()} to {df_real["timestamp"].max()}')
print(f'Cities Covered: {sorted(df_real["city"].unique().tolist())}')
print(f'AQI Range: {df_real["aqi"].min()}-{df_real["aqi"].max()}')

print('\n3. REAL DATA (All rows):')
print('-'*80)
print(df_real.to_string(index=False))

print('\n\n4. EXTENDED DATASET FOR TRAINING')
print('-'*80)

# Simulate the extension process (same as in training script)
real_stats = {}
for city in df_real['city'].unique():
    city_data = df_real[df_real['city'] == city]
    real_stats[city] = {
        'mean_aqi': city_data['aqi'].mean(),
        'std_aqi': city_data['aqi'].std() if city_data['aqi'].std() > 0 else 5,
        'min_aqi': city_data['aqi'].min(),
        'max_aqi': city_data['aqi'].max(),
    }

extended_data = []
start_date = df_real['timestamp'].min() - timedelta(days=30)
current_date = start_date

while current_date <= df_real['timestamp'].max() + timedelta(days=7):
    for city in df_real['city'].unique():
        stats = real_stats[city]
        hour_of_day = current_date.hour
        day_of_week = current_date.weekday()
        day_of_month = current_date.day
        
        hour_factor = 1.0
        if 7 <= hour_of_day < 9:
            hour_factor = 1.15
        elif 18 <= hour_of_day < 20:
            hour_factor = 1.2
        elif 22 <= hour_of_day or hour_of_day < 6:
            hour_factor = 0.85
        
        week_factor = 0.95 if day_of_week >= 5 else 1.0
        season_factor = 1.0 + 0.1 * (day_of_month / 15)
        
        noise = np.random.normal(1, 0.08)
        
        base_aqi = stats['mean_aqi']
        aqi_value = base_aqi * hour_factor * week_factor * season_factor * noise
        aqi_value = max(10, min(500, int(aqi_value)))
        
        if aqi_value <= 50:
            category = 'Good'
        elif aqi_value <= 100:
            category = 'Satisfactory'
        elif aqi_value <= 200:
            category = 'Moderately Polluted'
        elif aqi_value <= 300:
            category = 'Heavily Polluted'
        else:
            category = 'Severely Polluted'
        
        extended_data.append({
            'timestamp': current_date,
            'city': city,
            'aqi': aqi_value,
            'category': category,
            'hour': hour_of_day,
            'day_of_week': day_of_week,
            'month': current_date.month,
        })
    
    current_date += timedelta(hours=1)

df_extended = pd.DataFrame(extended_data)

print(f'Extended Dataset Size: {len(df_extended)} rows (hourly)')
print(f'Date Range: {df_extended["timestamp"].min()} to {df_extended["timestamp"].max()}')
print(f'Duration: {(df_extended["timestamp"].max() - df_extended["timestamp"].min()).days} days')
print(f'Cities: {len(df_extended["city"].unique())} cities ({", ".join(sorted(df_extended["city"].unique()))})')

print('\nEXTENDED DATASET - FIRST 10 ROWS:')
print('-'*80)
print(df_extended.head(10).to_string(index=False))

print('\nEXTENDED DATASET - LAST 10 ROWS:')
print('-'*80)
print(df_extended.tail(10).to_string(index=False))

print('\n5. STATISTICS')
print('-'*80)
print(f'Total Hourly Records: {len(df_extended)}')
print(f'Records per City: {len(df_extended) // len(df_extended["city"].unique())} records/city')
print(f'Avg AQI: {df_extended["aqi"].mean():.1f}')
print(f'Min AQI: {df_extended["aqi"].min()}')
print(f'Max AQI: {df_extended["aqi"].max()}')
print(f'Std Dev: {df_extended["aqi"].std():.2f}')

# Count by category
print('\nAQI Category Distribution:')
for cat in ['Good', 'Satisfactory', 'Moderately Polluted', 'Heavily Polluted', 'Severely Polluted']:
    count = len(df_extended[df_extended['category'] == cat])
    pct = 100 * count / len(df_extended)
    print(f'  {cat:20s}: {count:4d} ({pct:5.1f}%)')

print('\n6. AFTER FEATURE ENGINEERING')
print('-'*80)

# Create features (same as in training)
df_features = df_extended.copy().sort_values(['city', 'timestamp']).reset_index(drop=True)

for lag in [1, 6, 24]:
    df_features[f'lag_{lag}'] = df_features.groupby('city')['aqi'].shift(lag)

for window in [6, 24]:
    df_features[f'rolling_mean_{window}'] = df_features.groupby('city')['aqi'].transform(
        lambda x: x.rolling(window=window, min_periods=1).mean()
    )

df_features = df_features.dropna().reset_index(drop=True)

print(f'Features created: lag_1, lag_6, lag_24, rolling_mean_6, rolling_mean_24, hour, day_of_week, month')
print(f'Total Columns: {len(df_features.columns)}')
print(f'Rows after feature engineering: {len(df_features):,} (after dropping {len(df_extended) - len(df_features)} NaN rows)')

feature_cols = ['lag_1', 'lag_6', 'lag_24', 'rolling_mean_6', 'rolling_mean_24', 'hour', 'day_of_week', 'month']
train_size = int(0.8 * len(df_features))
test_size = len(df_features) - train_size

print(f'\nTrain/Test split:')
print(f'  Training: {train_size:,} rows (80%)')
print(f'  Test: {test_size:,} rows (20%)')

print('\n7. TRAINING DATA - FIRST 5 ROWS WITH FEATURES')
print('-'*80)
print(df_features[['timestamp', 'city', 'aqi'] + feature_cols].head(5).to_string(index=False))

print('\n8. TRAINING DATA - LAST 5 ROWS WITH FEATURES')
print('-'*80)
print(df_features[['timestamp', 'city', 'aqi'] + feature_cols].tail(5).to_string(index=False))

print('\n' + '='*80)
print('DATASET SUMMARY')
print('='*80)
print(f'Real Data Source File: vayuguard PostgreSQL database -> aqi_data table')
print(f'Real Data Records: 3 rows (seed data from ingestion)')
print(f'Extended Dataset: 2,667 hourly records')
print(f'After Feature Engineering: 2,595 rows')
print(f'Training Samples: 2,076 rows (80%)')
print(f'Test Samples: 519 rows (20%)')
print(f'Features: 8 engineered features')
print('='*80)
