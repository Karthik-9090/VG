#!/usr/bin/env python
"""
PHASE 1: Dataset Readiness Analysis
ML-Service Data Quality Assessment
Generates DATASET_READINESS_REPORT.md
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import numpy as np
from datetime import datetime
import sys

# Database configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'vayuguard',
    'user': 'vayuguard_user',
    'password': 'vayuguard_pass'
}

def connect_db():
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

def fetch_data(conn):
    """Fetch all AQI data from database."""
    query = """
    SELECT 
        id, city, aqi, category, 
        pm25, pm10, no2, o3, so2, co,
        temperature, humidity, wind_speed, pressure,
        recorded_at, created_at
    FROM aqi_data
    ORDER BY recorded_at ASC
    """
    df = pd.read_sql_query(query, conn)
    return df

def analyze_dataset(df):
    """Comprehensive dataset analysis."""
    analysis = {}
    
    # Basic statistics
    analysis['total_rows'] = len(df)
    analysis['date_range_start'] = df['recorded_at'].min().isoformat() if len(df) > 0 else None
    analysis['date_range_end'] = df['recorded_at'].max().isoformat() if len(df) > 0 else None
    analysis['unique_cities'] = df['city'].nunique() if len(df) > 0 else 0
    analysis['cities'] = sorted(df['city'].unique().tolist()) if len(df) > 0 else []
    
    # Per-city statistics
    analysis['rows_per_city'] = df['city'].value_counts().to_dict() if len(df) > 0 else {}
    
    # Feature completeness
    analysis['feature_completeness'] = {}
    feature_cols = ['aqi', 'pm25', 'pm10', 'no2', 'o3', 'so2', 'co', 
                    'temperature', 'humidity', 'wind_speed', 'pressure']
    for col in feature_cols:
        if col in df.columns:
            non_null = df[col].notna().sum()
            pct = (non_null / len(df) * 100) if len(df) > 0 else 0
            analysis['feature_completeness'][col] = {
                'non_null': int(non_null),
                'null': int(df[col].isna().sum()),
                'completeness_pct': round(pct, 2)
            }
    
    # Overall completeness
    overall_null = df[feature_cols].isna().sum().sum()
    total_cells = len(df) * len(feature_cols)
    analysis['overall_completeness_pct'] = round((1 - overall_null/total_cells)*100, 2) if total_cells > 0 else 0
    
    # Duplicates
    analysis['duplicate_rows'] = int(df.duplicated().sum())
    analysis['duplicate_by_city_timestamp'] = int(df.duplicated(subset=['city', 'recorded_at']).sum())
    
    # Missing value counts
    analysis['missing_values_by_column'] = df[feature_cols].isna().sum().to_dict()
    
    # AQI statistics
    if 'aqi' in df.columns:
        aqi_stats = df['aqi'].describe()
        analysis['aqi_statistics'] = {
            'min': float(aqi_stats['min']),
            'max': float(aqi_stats['max']),
            'mean': float(aqi_stats['mean']),
            'median': float(df['aqi'].median()),
            'std': float(aqi_stats['std']),
            'count': int(aqi_stats['count'])
        }
    
    # Temporal distribution
    if len(df) > 0:
        df['day'] = pd.to_datetime(df['recorded_at']).dt.date
        analysis['data_per_day'] = df.groupby('day').size().to_dict()
        analysis['max_records_per_day'] = int(df.groupby('day').size().max())
        analysis['avg_records_per_day'] = round(df.groupby('day').size().mean(), 2)
    
    return analysis

def generate_report(analysis):
    """Generate markdown report."""
    report = f"""# DATASET READINESS REPORT

**Generated:** {datetime.now().isoformat()}

## Executive Summary

✅ **Dataset Status:** Ready for analysis  
📊 **Total Records:** {analysis['total_rows']}  
🏙️ **Cities:** {analysis['unique_cities']}  
📈 **Overall Completeness:** {analysis['overall_completeness_pct']}%  

## 1. Data Volume

| Metric | Value |
|--------|-------|
| Total Rows | {analysis['total_rows']} |
| Unique Cities | {analysis['unique_cities']} |
| Date Range | {analysis['date_range_start']} to {analysis['date_range_end']} |

### Rows Per City

"""
    
    if analysis['rows_per_city']:
        for city, count in sorted(analysis['rows_per_city'].items(), key=lambda x: x[1], reverse=True):
            report += f"- **{city}:** {count} records\n"
    else:
        report += "- No data collected yet\n"
    
    report += f"""

## 2. Data Completeness

**Overall Feature Completeness:** {analysis['overall_completeness_pct']}%

### Per-Feature Completeness

"""
    
    for col, stats in sorted(analysis['feature_completeness'].items()):
        completeness = stats['completeness_pct']
        status = "✅" if completeness >= 95 else "⚠️" if completeness >= 70 else "❌"
        report += f"- {status} **{col}:** {stats['non_null']}/{analysis['total_rows']} ({completeness}%)\n"
    
    report += f"""

## 3. Data Quality

| Issue | Count |
|-------|-------|
| Duplicate Records | {analysis['duplicate_rows']} |
| Duplicate (City+Timestamp) | {analysis['duplicate_by_city_timestamp']} |

## 4. Feature Statistics

### AQI Distribution

"""
    
    if 'aqi_statistics' in analysis:
        aqi = analysis['aqi_statistics']
        report += f"""| Statistic | Value |
|-----------|-------|
| Count | {int(aqi['count'])} |
| Mean | {aqi['mean']:.2f} |
| Median | {aqi['median']:.2f} |
| Std Dev | {aqi['std']:.2f} |
| Min | {aqi['min']:.2f} |
| Max | {aqi['max']:.2f} |
"""
    
    report += f"""

## 5. Temporal Distribution

| Metric | Value |
|--------|-------|
| Max Records/Day | {analysis.get('max_records_per_day', 'N/A')} |
| Avg Records/Day | {analysis.get('avg_records_per_day', 'N/A')} |

## 6. Readiness Assessment

"""
    
    # Readiness decision
    if analysis['total_rows'] < 50:
        readiness = "🔴 **NOT READY** - Insufficient data (< 50 records)"
        phase2_status = "❌ Cannot proceed to Phase 2 (need 500+ rows)"
    elif analysis['total_rows'] < 500:
        readiness = "🟡 **COLLECTING** - Initial collection phase"
        phase2_status = f"⏳ Proceed to Phase 2 when rows exceed 500 (currently {analysis['total_rows']})"
    else:
        readiness = "🟢 **READY** - Sufficient data for feature engineering"
        phase2_status = "✅ Ready to proceed to Phase 2"
    
    report += f"""### Overall Readiness
{readiness}

### Phase 2 Feature Engineering
{phase2_status}

## 7. Recommendations

"""
    
    if analysis['total_rows'] < 100:
        report += "- 🔴 Increase data collection frequency\n"
        report += "- 🔴 Monitor WAQI API response rates\n"
        report += "- 🔴 Verify database ingestion pipeline\n"
    
    if analysis['overall_completeness_pct'] < 80:
        report += "- ⚠️ Address missing values in data collection\n"
        incomplete_features = [f for f, s in analysis['feature_completeness'].items() 
                               if s['completeness_pct'] < 80]
        if incomplete_features:
            report += f"- ⚠️ Focus on completing: {', '.join(incomplete_features)}\n"
    
    if analysis['duplicate_rows'] > 0:
        report += f"- 🟡 Investigate {analysis['duplicate_rows']} duplicate records\n"
    
    if analysis['total_rows'] >= 500:
        report += "- ✅ Ready for feature engineering pipeline\n"
        report += "- ✅ Proceed to Phase 2: Create lag/rolling features\n"
        report += "- ✅ Schedule model training for Phase 3\n"
    
    report += f"""

## 8. Next Steps

1. **Phase 2 (Feature Engineering):**
   - Status: {phase2_status}
   - When available: Create lag features (1, 3, 6, 12, 24)
   - When available: Create rolling statistics (6, 12, 24 hour windows)
   - When available: Add temporal features (hour, day_of_week, month)

2. **Phase 3 (Model Training):**
   - When Phase 2 complete: Train baseline model
   - When Phase 2 complete: Train Random Forest model
   - When Phase 2 complete: Train XGBoost model

3. **Phase 4 (Model Comparison):**
   - When Phase 3 complete: Generate MODEL_COMPARISON_REPORT.md

4. **Phase 5 (API Integration):**
   - When Phase 4 complete: Update forecast API with best model

---

**Report Status:** Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return report

def main():
    """Main execution."""
    print("=" * 70)
    print("PHASE 1: DATASET READINESS ANALYSIS")
    print("=" * 70)
    print()
    
    # Connect to database
    print("📡 Connecting to PostgreSQL...")
    conn = connect_db()
    
    # Fetch data
    print("📊 Fetching data from aqi_data table...")
    df = fetch_data(conn)
    conn.close()
    
    print(f"✅ Loaded {len(df)} records")
    print()
    
    # Analyze
    print("🔍 Analyzing dataset...")
    analysis = analyze_dataset(df)
    
    # Display summary
    print()
    print("=" * 70)
    print("DATASET SUMMARY")
    print("=" * 70)
    print(f"Total Rows:              {analysis['total_rows']}")
    print(f"Unique Cities:           {analysis['unique_cities']}")
    print(f"Overall Completeness:    {analysis['overall_completeness_pct']}%")
    print(f"Duplicate Records:       {analysis['duplicate_rows']}")
    print(f"Date Range:              {analysis['date_range_start']} to {analysis['date_range_end']}")
    print()
    
    if analysis['rows_per_city']:
        print("Rows Per City:")
        for city, count in sorted(analysis['rows_per_city'].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {city}: {count}")
    print()
    
    # Phase 2 readiness
    if analysis['total_rows'] >= 500:
        print("✅ PHASE 2 READY - Rows >= 500")
    else:
        print(f"⏳ PHASE 2 BLOCKED - Need {500 - analysis['total_rows']} more rows")
    print()
    
    # Generate report
    print("📝 Generating DATASET_READINESS_REPORT.md...")
    report = generate_report(analysis)
    
    # Save report
    report_path = "DATASET_READINESS_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Report saved to {report_path}")
    print()
    print("=" * 70)
    print("PHASE 1 COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    main()
