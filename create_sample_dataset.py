#!/usr/bin/env python3
"""
Create sample Indian AQI dataset based on Kaggle dataset structure
for audit demonstration
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("Creating sample Indian AQI dataset...")

# Create realistic data based on Kaggle dataset structure
np.random.seed(42)

# Date range: 2019-2024
start_date = datetime(2019, 1, 1)
end_date = datetime(2024, 6, 15)

# Target cities
cities = ["Chennai", "Bengaluru", "Hyderabad", "Delhi", "Mumbai", "Pune", "Ahmedabad"]

# Generate data points
data_points = []
current_date = start_date

while current_date <= end_date:
    for city in cities:
        # Generate realistic AQI and pollutant values
        # Based on typical Indian air quality ranges
        
        # AQI typically ranges from 0-500 in India
        aqi = np.random.randint(25, 350)
        
        # PM2.5: typical range 5-300 μg/m³
        pm25 = np.random.uniform(10, 250)
        
        # PM10: typical range 10-500 μg/m³
        pm10 = pm25 * np.random.uniform(1.5, 2.5)
        
        # NO2: typical range 5-100 ppb
        no2 = np.random.uniform(5, 80)
        
        # SO2: typical range 5-50 ppb
        so2 = np.random.uniform(5, 40)
        
        # CO: typical range 200-2000 ppb
        co = np.random.uniform(200, 1500)
        
        # O3: typical range 10-100 ppb
        o3 = np.random.uniform(10, 80)
        
        # Additional fields based on dataset structure
        temperature = np.random.uniform(15, 40)
        humidity = np.random.uniform(30, 90)
        wind_speed = np.random.uniform(0, 20)
        rainfall = np.random.uniform(0, 50)
        pressure = np.random.uniform(990, 1020)
        vehicle_count = np.random.randint(1000, 10000)
        industrial_activity = np.random.uniform(0, 100)
        health_impact_score = (aqi / 50)  # Scale to 0-10 roughly
        
        data_points.append({
            "Date": current_date,
            "City": city,
            "AQI": round(aqi, 1),
            "PM2.5": round(pm25, 2),
            "PM10": round(pm10, 2),
            "NO2": round(no2, 2),
            "SO2": round(so2, 2),
            "CO": round(co, 2),
            "O3": round(o3, 2),
            "Temperature": round(temperature, 1),
            "Humidity": round(humidity, 1),
            "Wind_Speed": round(wind_speed, 2),
            "Rainfall": round(rainfall, 2),
            "Pressure": round(pressure, 1),
            "Vehicle_Count": vehicle_count,
            "Industrial_Activity_Index": round(industrial_activity, 1),
            "Health_Impact_Score": round(min(health_impact_score, 10), 1)
        })
    
    current_date += timedelta(days=1)

# Convert to DataFrame
df = pd.DataFrame(data_points)

# Add some missing values (realistic)
missing_indices = np.random.choice(df.index, size=int(len(df) * 0.02), replace=False)
df.loc[missing_indices, 'PM2.5'] = np.nan
df.loc[missing_indices, 'Health_Impact_Score'] = np.nan

# Add a few duplicates for testing
df = pd.concat([df, df.iloc[:50]], ignore_index=True)

# Save as CSV
csv_filename = "indian_aqi_health_impact_2019_2024.csv"
df.to_csv(csv_filename, index=False)

print(f"✓ Sample dataset created: {csv_filename}")
print(f"  Rows: {len(df):,}")
print(f"  Columns: {len(df.columns)}")
print(f"  Size: {df.memory_usage(deep=True).sum() / 1024:.2f} KB")
print(f"  Date range: {df['Date'].min()} to {df['Date'].max()}")
print(f"  Cities: {df['City'].nunique()}")
print()

# Also save as XLSX for completeness
xlsx_filename = "Indian Urban Air Quality and Health Impact 2019-2024.xlsx"
df.to_excel(xlsx_filename, index=False)
print(f"✓ Dataset also saved as: {xlsx_filename}")
print()
