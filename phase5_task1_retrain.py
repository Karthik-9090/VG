#!/usr/bin/env python3
"""
PHASE 5 - TASK 1: PRODUCTION MODEL RETRAINING
==============================================
Retrain Lasso Regression on ALL 5,907 records (production dataset).

Output:
- models/production_lasso.pkl
- production_metrics.json
"""

import psycopg2
import pandas as pd
import numpy as np
import json
import pickle
import os
import warnings
from datetime import datetime
from sklearn.linear_model import Lasso
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error, r2_score

warnings.filterwarnings('ignore')

# Configuration
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "vayuguard"
DB_USER = "postgres"
DB_PASSWORD = ""

print("=" * 90)
print("PHASE 5 - TASK 1: PRODUCTION MODEL RETRAINING")
print("=" * 90)
print(f"[TIMESTAMP] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Step 1: Connect to PostgreSQL
print("STEP 1: Connecting to PostgreSQL...")
try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()
    print("[OK] Connected to PostgreSQL")
except Exception as e:
    print(f"[ERROR] Connection failed: {e}")
    exit(1)

# Step 2: Load all engineered features
print()
print("STEP 2: Loading all engineered features...")
try:
    query = """
    SELECT date, city, aqi, pm2_5, pm10, no2, so2, co, o3,
           lag_1, lag_3, lag_6, lag_12, lag_24,
           rolling_mean_6, rolling_mean_12, rolling_mean_24,
           rolling_std_6, rolling_std_12, rolling_std_24,
           hour, day_of_week, month, quarter, day_of_month
    FROM engineered_features
    ORDER BY city, date
    """
    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    
    # Create temporal features that were in Phase 4 analysis
    df['year'] = df['date'].dt.year
    df['week_of_year'] = df['date'].dt.isocalendar().week
    
    def get_season(month):
        if month in [12, 1, 2]:
            return 1  # Winter
        elif month in [3, 4, 5]:
            return 2  # Spring
        elif month in [6, 7, 8]:
            return 3  # Summer
        else:
            return 4  # Autumn
    
    df['season'] = df['month'].apply(get_season)
    
    # Days since start (per city)
    df['days_since_start'] = df.groupby('city')['date'].apply(
        lambda x: (x - x.min()).dt.days
    ).reset_index(drop=True)
    
    total_rows = len(df)
    print(f"[OK] Loaded {total_rows:,} records")
    print(f"     Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"     Cities: {', '.join(sorted(df['city'].unique()))}")
    print(f"     Records per city:")
    for city in sorted(df['city'].unique()):
        count = len(df[df['city'] == city])
        print(f"       - {city}: {count:,}")
except Exception as e:
    print(f"[ERROR] Failed to load data: {e}")
    conn.close()
    exit(1)

conn.close()

# Step 3: Prepare features
print()
print("STEP 3: Preparing features...")
try:
    feature_cols = [
        'lag_1', 'lag_3', 'lag_6', 'lag_12', 'lag_24',
        'rolling_mean_6', 'rolling_mean_12', 'rolling_mean_24',
        'rolling_std_6', 'rolling_std_12', 'rolling_std_24',
        'hour', 'day_of_week', 'month', 'quarter', 'day_of_month',
        'year', 'week_of_year', 'season', 'days_since_start',
        'pm2_5', 'pm10', 'no2', 'so2', 'co', 'o3'
    ]
    
    # Add interaction features
    df['lag_1_x_rolling_mean_6'] = df['lag_1'] * df['rolling_mean_6']
    df['lag_3_x_rolling_std_6'] = df['lag_3'] * df['rolling_std_6']
    df['pm25_x_pm10'] = df['pm2_5'] * df['pm10']
    df['no2_x_so2'] = df['no2'] * df['so2']
    
    feature_cols.extend([
        'lag_1_x_rolling_mean_6',
        'lag_3_x_rolling_std_6',
        'pm25_x_pm10',
        'no2_x_so2'
    ])
    
    X = df[feature_cols].values
    y = df['aqi'].values
    
    print(f"[OK] Features prepared")
    print(f"     Total features: {len(feature_cols)}")
    print(f"     Total samples: {len(X):,}")
    print(f"     AQI range: {y.min():.0f} - {y.max():.0f}")
except Exception as e:
    print(f"[ERROR] Feature preparation failed: {e}")
    exit(1)

# Step 4: Train Lasso on ALL data
print()
print("STEP 4: Training Lasso Regression on all data...")
try:
    from time import time
    start = time()
    
    model = Lasso(alpha=0.1, max_iter=5000)
    model.fit(X, y)
    
    training_time = time() - start
    
    print(f"[OK] Training completed in {training_time:.2f}s")
    
    # Get predictions on training data (for metrics)
    y_pred = model.predict(X)
    
    # Calculate metrics
    mae = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    mape = mean_absolute_percentage_error(y, y_pred)
    r2 = r2_score(y, y_pred)
    
    print(f"     Training metrics (on full dataset):")
    print(f"       MAE:  {mae:.4f}")
    print(f"       RMSE: {rmse:.4f}")
    print(f"       MAPE: {mape:.4f}")
    print(f"       R2:   {r2:.4f}")
except Exception as e:
    print(f"[ERROR] Model training failed: {e}")
    exit(1)

# Step 5: Create models directory
print()
print("STEP 5: Saving model...")
try:
    os.makedirs('models', exist_ok=True)
    
    model_path = 'models/production_lasso.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"[OK] Model saved to {model_path}")
except Exception as e:
    print(f"[ERROR] Model save failed: {e}")
    exit(1)

# Step 6: Save production metrics
print()
print("STEP 6: Saving production metrics...")
try:
    metrics_data = {
        "timestamp": datetime.now().isoformat(),
        "phase": 5,
        "task": "production_retraining",
        "model_type": "Lasso Regression",
        "model_version": "v1.0",
        "model_file": "models/production_lasso.pkl",
        "deployment_date": datetime.now().isoformat(),
        "training_config": {
            "alpha": 0.1,
            "max_iter": 5000,
            "total_features": len(feature_cols),
            "feature_count": {
                "base_engineered": 16,
                "temporal": 4,
                "interaction": 4,
                "pollutants": 6
            }
        },
        "training_data": {
            "total_records": int(total_rows),
            "date_range_start": df['date'].min().isoformat(),
            "date_range_end": df['date'].max().isoformat(),
            "cities": sorted(df['city'].unique().tolist()),
            "records_per_city": {city: int(len(df[df['city'] == city])) for city in sorted(df['city'].unique())}
        },
        "training_metrics": {
            "mae": float(mae),
            "rmse": float(rmse),
            "mape": float(mape),
            "r2": float(r2),
            "training_time_seconds": float(training_time)
        },
        "features": feature_cols,
        "model_status": "production_ready",
        "deployment_status": "ready_for_deployment"
    }
    
    with open('production_metrics.json', 'w') as f:
        json.dump(metrics_data, f, indent=2)
    
    print(f"[OK] Saved production_metrics.json")
except Exception as e:
    print(f"[ERROR] Metrics save failed: {e}")
    exit(1)

# Final summary
print()
print("=" * 90)
print("PRODUCTION MODEL RETRAINING: COMPLETE")
print("=" * 90)
print()
print("MODEL SUMMARY:")
print(f"  Model:    Lasso Regression (v1.0)")
print(f"  File:     models/production_lasso.pkl")
print(f"  Training: {total_rows:,} records (2019-01-25 to 2024-06-15)")
print(f"  Features: {len(feature_cols)}")
print()
print("TRAINING METRICS:")
print(f"  MAE:      {mae:.4f} AQI points")
print(f"  RMSE:     {rmse:.4f}")
print(f"  R2:       {r2:.4f}")
print()
print("STATUS: [READY FOR DEPLOYMENT]")
print()
