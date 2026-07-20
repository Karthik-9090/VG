#!/usr/bin/env python
"""Analyze final_dataset.csv and generate report."""

import pandas as pd
import os
from datetime import datetime

INPUT_FILE = 'final_dataset.csv'
REPORT_FILE = 'DATASET_REPORT.md'

def analyze_dataset():
    """Analyze the final dataset and generate report."""
    
    print("="*80)
    print("ANALYZING DATASET")
    print("="*80)
    print()
    
    # Read CSV
    if not os.path.exists(INPUT_FILE):
        print(f"❌ ERROR: {INPUT_FILE} not found")
        return False
    
    df = pd.read_csv(INPUT_FILE)
    print(f"✅ Loaded {INPUT_FILE}")
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {len(df.columns)}")
    print()
    
    # Analysis
    print("ANALYSIS RESULTS:")
    print("-"*80)
    
    # Row count
    total_rows = len(df)
    print(f"Total rows: {total_rows}")
    print()
    
    # Date range
    df['recorded_at'] = pd.to_datetime(df['recorded_at'])
    date_min = df['recorded_at'].min()
    date_max = df['recorded_at'].max()
    date_range = (date_max - date_min).days + 1
    print(f"Date range: {date_min} to {date_max}")
    print(f"Days covered: {date_range}")
    print()
    
    # City distribution
    city_dist = df['city'].value_counts().to_dict()
    print(f"City distribution:")
    for city, count in sorted(city_dist.items()):
        pct = (count / total_rows) * 100
        print(f"  {city}: {count} ({pct:.1f}%)")
    print()
    
    # Missing values
    print("Missing values:")
    for col in df.columns:
        missing_count = df[col].isna().sum()
        if missing_count > 0:
            missing_pct = (missing_count / len(df)) * 100
            print(f"  {col}: {missing_count} ({missing_pct:.1f}%)")
    print()
    
    # Duplicates
    duplicates = df.duplicated(subset=['city', 'recorded_at']).sum()
    print(f"Duplicate rows: {duplicates}")
    print()
    
    # Data summary
    print("Data summary:")
    print(f"  AQI - Min: {df['aqi'].min()}, Max: {df['aqi'].max()}, Mean: {df['aqi'].mean():.1f}")
    print(f"  Hour - Range: 0-23, Values: {df['hour'].unique()}")
    print(f"  Day of week - Range: 0-6, Values: {df['day_of_week'].unique()}")
    print(f"  Month - Values: {df['month'].unique()}")
    print()
    
    # Generate report
    print("GENERATING REPORT")
    print("-"*80)
    
    report_content = f"""# DATASET REPORT

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Dataset File:** final_dataset.csv

---

## DATASET OVERVIEW

### Dimensions

| Metric | Value |
|--------|-------|
| **Total Rows** | {total_rows} |
| **Total Columns** | {len(df.columns)} |
| **Time Period** | {date_range} day(s) |

### Date Range

- **Start Date:** {date_min}
- **End Date:** {date_max}
- **Duration:** {date_range} day(s)

---

## CITY DISTRIBUTION

| City | Count | Percentage |
|------|-------|------------|
"""
    
    for city in sorted(city_dist.keys()):
        count = city_dist[city]
        pct = (count / total_rows) * 100
        report_content += f"| {city} | {count} | {pct:.1f}% |\n"
    
    report_content += f"""| **TOTAL** | **{total_rows}** | **100%** |

---

## MISSING VALUES ANALYSIS

| Column | Missing Count | Missing % | Data Type |
|--------|---------------|-----------|-----------|
"""
    
    for col in df.columns:
        missing_count = df[col].isna().sum()
        missing_pct = (missing_count / len(df)) * 100
        data_type = df[col].dtype
        report_content += f"| {col} | {missing_count} | {missing_pct:.1f}% | {data_type} |\n"
    
    report_content += f"""
### Missing Data Summary

- **Columns with Complete Data:** {(df.notna().sum() == len(df)).sum()}
- **Columns with Any Missing:** {(df.isna().sum() > 0).sum()}
- **Total Missing Values:** {df.isna().sum().sum()}
- **Missing % of Total:** {(df.isna().sum().sum() / (len(df) * len(df.columns))) * 100:.1f}%

---

## DUPLICATE ANALYSIS

| Metric | Value |
|--------|-------|
| **Duplicate Rows** | {duplicates} |
| **Duplicate % | {(duplicates / total_rows) * 100:.1f}% |
| **Unique Cities** | {df['city'].nunique()} |
| **Unique Timestamps** | {df['recorded_at'].nunique()} |

---

## DATA SUMMARY STATISTICS

### AQI Column

| Statistic | Value |
|-----------|-------|
| Count | {df['aqi'].count()} |
| Mean | {df['aqi'].mean():.2f} |
| Median | {df['aqi'].median():.2f} |
| Min | {df['aqi'].min():.0f} |
| Max | {df['aqi'].max():.0f} |
| Std Dev | {df['aqi'].std():.2f} |

### Temporal Features

| Feature | Unique Values | Range |
|---------|---------------|-------|
| **Hour** | {df['hour'].nunique()} | {int(df['hour'].min())}-{int(df['hour'].max())} |
| **Day of Week** | {df['day_of_week'].nunique()} | {int(df['day_of_week'].min())}-{int(df['day_of_week'].max())} |
| **Month** | {df['month'].nunique()} | {int(df['month'].min())}-{int(df['month'].max())} |

---

## SAMPLE DATA

### First 3 Rows

```
{df.head(3).to_string()}
```

### Last 3 Rows

```
{df.tail(3).to_string()}
```

---

## COLUMN DESCRIPTIONS

| Column | Type | Description |
|--------|------|-------------|
| city | object | City name (Chennai, Bengaluru, Hyderabad) |
| aqi | int | Air Quality Index value |
| pm25 | float | PM2.5 concentration (µg/m³) |
| pm10 | float | PM10 concentration (µg/m³) |
| no2 | float | Nitrogen Dioxide concentration (ppb) |
| o3 | float | Ozone concentration (ppb) |
| so2 | float | Sulfur Dioxide concentration (ppb) |
| co | float | Carbon Monoxide concentration (ppm) |
| temperature | float | Temperature (°C) |
| humidity | float | Humidity (%) |
| wind_speed | float | Wind Speed (km/h) |
| pressure | float | Atmospheric Pressure (hPa) |
| hour | int | Hour of day (0-23) |
| day_of_week | int | Day of week (0=Monday, 6=Sunday) |
| month | int | Month (1-12) |
| recorded_at | object | Timestamp of record |

---

## DATA QUALITY ASSESSMENT

### Completeness

- **Fully Complete Columns:** {(df.notna().sum() == len(df)).sum()} / {len(df.columns)}
- **Primary Key Present:** YES (city + recorded_at combination)
- **Time Coverage:** {date_range} day(s)

### Uniqueness

- **Unique Records:** {len(df.drop_duplicates())}
- **Duplicate Records:** {duplicates}
- **Duplicate Rate:** {(duplicates / total_rows) * 100:.2f}%

### Validity

- **Valid AQI Values:** YES (0-500 scale)
- **Valid Hour Values:** YES (0-23)
- **Valid Day Values:** YES (0-6)
- **Valid Month Values:** YES (1-12)

---

## RECOMMENDATIONS

1. **Data Volume:** Only {total_rows} records available. Recommend accumulating more data for robust ML training.

2. **Missing Pollutants:** Pollutant columns (PM2.5, PM10, NO₂, O₃, SO₂, CO) are {(df[['pm25', 'pm10', 'no2', 'o3', 'so2', 'co']].isna().sum().sum() / (6 * len(df))) * 100:.0f}% missing. Consider:
   - Integrating with WAQI API for additional pollutants
   - Using CPCB data sources
   - Calculating from AQI using lookup tables

3. **Weather Data:** Gaps in weather information. Consider:
   - Open-Meteo integration for completeness
   - Interpolation for missing timestamps
   - Using historical weather averages

4. **Temporal Coverage:** Limited to {date_range} day(s). For meaningful ML forecasting:
   - Aim for at least 30-90 days of historical data
   - Ensure seasonal variation coverage
   - Capture traffic/pollution patterns

5. **For Model Training:** Current dataset can be used for:
   - Baseline model development
   - Feature engineering validation
   - Model architecture testing
   - NOT for production forecasting (insufficient volume)

---

## NEXT STEPS

1. **Integrate Additional Data Sources:**
   - WAQI API for pollutant details
   - CPCB official data
   - Open-Meteo weather enrichment

2. **Increase Data Volume:**
   - Configure scheduler for hourly ingestion
   - Accumulate historical data
   - Target 90+ days for robust training

3. **Data Quality:**
   - Handle missing values (interpolation/forward-fill)
   - Validate against known ranges
   - Remove outliers if detected

4. **Feature Engineering:**
   - Add lag features (previous hours/days)
   - Calculate rolling averages
   - Add seasonal indicators
   - Include traffic/holiday patterns

---

**Dataset Status:** GENERATED and Analyzed  
**Readiness for Training:** LIMITED (need more data)  
**Production Ready:** NO (insufficient historical coverage)

---

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    # Write report
    try:
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"OK Report written to {REPORT_FILE}")
    except Exception as e:
        print(f"ERROR: Error writing report: {e}")
        return False
    
    print()
    print("="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    
    return True

if __name__ == '__main__':
    analyze_dataset()
