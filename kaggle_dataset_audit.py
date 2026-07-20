#!/usr/bin/env python3
"""
Kaggle Dataset Audit: Indian AQI Trends and Health Risk 2019-2024
Complete data inspection and quality assessment
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from pathlib import Path

print("\n" + "="*80)
print("KAGGLE DATASET AUDIT: Indian AQI Trends and Health Risk 2019-2024")
print("="*80)
print(f"Audit Date: {datetime.now().isoformat()}\n")

# Dataset location
DATASET_PATH = "indian_aqi_health_impact_2019_2024.csv"
XLSX_PATH = "Indian Urban Air Quality and Health Impact 2019-2024.xlsx"

audit_results = {
    "timestamp": datetime.now().isoformat(),
    "dataset_name": "Indian AQI Trends and Health Risk 2019-2024",
    "source": "Kaggle",
    "url": "https://www.kaggle.com/datasets/divsmahesh/indian-aqi-trends-and-health-risk-20192024",
    "audit_sections": {}
}

# ============================================================================
# SECTION 1: FILE INSPECTION
# ============================================================================
print("SECTION 1: FILE INSPECTION")
print("-" * 80)

files_found = {
    "CSV": DATASET_PATH if os.path.exists(DATASET_PATH) else "NOT FOUND",
    "XLSX": XLSX_PATH if os.path.exists(XLSX_PATH) else "NOT FOUND",
    "Notebook": "aqi_health_impact_analysis.ipynb" if os.path.exists("aqi_health_impact_analysis.ipynb") else "NOT FOUND"
}

for file_type, status in files_found.items():
    print(f"  {file_type}: {status}")

audit_results["audit_sections"]["files"] = files_found

# Try to load CSV first
try:
    if os.path.exists(DATASET_PATH):
        df = pd.read_csv(DATASET_PATH)
        print(f"\n[OK] CSV file loaded successfully")
        print(f"  File size: {os.path.getsize(DATASET_PATH) / 1024:.2f} KB")
    else:
        print(f"\n[ERROR] CSV file not found at {DATASET_PATH}")
        print("  Attempting to load XLSX...")
        if os.path.exists(XLSX_PATH):
            df = pd.read_excel(XLSX_PATH, sheet_name=0)
            print(f"[OK] XLSX file loaded successfully")
            print(f"  File size: {os.path.getsize(XLSX_PATH) / 1024:.2f} KB")
        else:
            print(f"[ERROR] XLSX file not found at {XLSX_PATH}")
            print("\nPlease download the dataset from Kaggle:")
            print("https://www.kaggle.com/datasets/divsmahesh/indian-aqi-trends-and-health-risk-20192024")
            exit(1)
except Exception as e:
    print(f"\n[ERROR] Error loading dataset: {str(e)}")
    exit(1)

# ============================================================================
# SECTION 2: DATASET DIMENSIONS
# ============================================================================
print("\n\nSECTION 2: DATASET DIMENSIONS")
print("-" * 80)

row_count = len(df)
col_count = len(df.columns)
memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024

print(f"  Total Rows: {row_count:,}")
print(f"  Total Columns: {col_count}")
print(f"  Memory Usage: {memory_usage:.2f} MB")
print(f"  Shape: {df.shape}")

audit_results["audit_sections"]["dimensions"] = {
    "rows": row_count,
    "columns": col_count,
    "memory_mb": memory_usage,
    "shape": list(df.shape)
}

# ============================================================================
# SECTION 3: SCHEMA INSPECTION
# ============================================================================
print("\n\nSECTION 3: SCHEMA INSPECTION")
print("-" * 80)

print(f"\nColumns ({col_count} total):\n")
schema = []
for i, col in enumerate(df.columns, 1):
    dtype = str(df[col].dtype)
    non_null = df[col].notna().sum()
    null_count = df[col].isna().sum()
    print(f"  {i:2d}. {col:30s} | Type: {dtype:10s} | Non-Null: {non_null:6,} | Null: {null_count:6,}")
    
    schema_entry = {
        "column": col,
        "dtype": dtype,
        "non_null": int(non_null),
        "null": int(null_count),
        "null_percent": round((null_count / row_count * 100), 2)
    }
    schema.append(schema_entry)

audit_results["audit_sections"]["schema"] = schema

# ============================================================================
# SECTION 4: DATA TYPE SUMMARY
# ============================================================================
print("\n\nSECTION 4: DATA TYPE SUMMARY")
print("-" * 80)

dtype_summary = df.dtypes.value_counts()
print("\nData Type Distribution:")
for dtype, count in dtype_summary.items():
    print(f"  {str(dtype):20s}: {count} columns")

audit_results["audit_sections"]["dtype_summary"] = {str(k): int(v) for k, v in dtype_summary.items()}

# ============================================================================
# SECTION 5: CITY INFORMATION
# ============================================================================
print("\n\nSECTION 5: CITY INFORMATION")
print("-" * 80)

# Identify city column
city_columns = [col for col in df.columns if col.lower() in ['city', 'city_name', 'cities']]

if city_columns:
    city_col = city_columns[0]
    unique_cities = df[city_col].unique()
    city_count = len(unique_cities)
    
    print(f"\nCity Column: '{city_col}'")
    print(f"Unique Cities: {city_count}")
    print(f"\nCities in Dataset:")
    
    # Sort and display cities
    cities_sorted = sorted(unique_cities)
    for i, city in enumerate(cities_sorted, 1):
        count = (df[city_col] == city).sum()
        print(f"  {i:2d}. {city:20s} ({count:6,} records)")
    
    # Check for target cities
    target_cities = ["Chennai", "Bengaluru", "Hyderabad"]
    print(f"\nTarget Cities Verification:")
    target_found = {}
    for target in target_cities:
        found = target in unique_cities or any(target.lower() in str(c).lower() for c in unique_cities)
        status = "[YES]" if found else "[NO]"
        print(f"  {target:15s}: {status}")
        target_found[target] = found
        
        # If not exact match, show similar cities
        if not found:
            similar = [c for c in unique_cities if target.lower() in str(c).lower()]
            if similar:
                print(f"    Similar cities: {similar}")
    
    audit_results["audit_sections"]["cities"] = {
        "total_unique": city_count,
        "city_column": city_col,
        "all_cities": cities_sorted,
        "target_cities_found": target_found
    }
else:
    print("WARNING: No city column identified")
    print("Available columns:", df.columns.tolist())
    audit_results["audit_sections"]["cities"] = {"error": "No city column found"}

# ============================================================================
# SECTION 6: DATE RANGE
# ============================================================================
print("\n\nSECTION 6: DATE RANGE")
print("-" * 80)

date_columns = [col for col in df.columns if col.lower() in ['date', 'date_time', 'timestamp', 'time']]

if date_columns:
    date_col = date_columns[0]
    print(f"\nDate Column: '{date_col}'")
    
    # Convert to datetime if needed
    try:
        if df[date_col].dtype != 'datetime64[ns]':
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        date_min = df[date_col].min()
        date_max = df[date_col].max()
        date_null = df[date_col].isna().sum()
        days_span = (date_max - date_min).days
        
        print(f"  Earliest Date: {date_min}")
        print(f"  Latest Date: {date_max}")
        print(f"  Date Span: {days_span} days ({days_span/365:.2f} years)")
        print(f"  Null Dates: {date_null}")
        
        audit_results["audit_sections"]["date_range"] = {
            "date_column": date_col,
            "min_date": str(date_min),
            "max_date": str(date_max),
            "days_span": days_span,
            "years_span": round(days_span / 365, 2),
            "null_dates": int(date_null)
        }
    except Exception as e:
        print(f"  Error parsing dates: {str(e)}")
        audit_results["audit_sections"]["date_range"] = {"error": str(e)}
else:
    print("WARNING: No date column identified")
    audit_results["audit_sections"]["date_range"] = {"error": "No date column found"}

# ============================================================================
# SECTION 7: REQUIRED COLUMNS CHECK
# ============================================================================
print("\n\nSECTION 7: REQUIRED COLUMNS VERIFICATION")
print("-" * 80)

required_pollutants = ["AQI", "PM2.5", "PM10", "NO2", "SO2", "CO"]
column_names_lower = [col.lower() for col in df.columns]

print(f"\nRequired Pollutants Check:")
pollutants_found = {}
for pollutant in required_pollutants:
    # Try exact match first
    found_col = None
    for col in df.columns:
        if col.lower() == pollutant.lower():
            found_col = col
            break
    
    # If not found, try partial match
    if not found_col:
        for col in df.columns:
            if pollutant.lower() in col.lower():
                found_col = col
                break
    
    if found_col:
        non_null = df[found_col].notna().sum()
        null_count = df[found_col].isna().sum()
        null_pct = (null_count / len(df)) * 100
        print(f"  [OK] {pollutant:10s} | Column: '{found_col}' | Null: {null_pct:.2f}%")
        pollutants_found[pollutant] = {
            "column": found_col,
            "found": True,
            "null_percent": round(null_pct, 2)
        }
    else:
        print(f"  [NO] {pollutant:10s} | NOT FOUND")
        pollutants_found[pollutant] = {"found": False}

audit_results["audit_sections"]["required_columns"] = pollutants_found

# ============================================================================
# SECTION 8: MISSING VALUE ANALYSIS
# ============================================================================
print("\n\nSECTION 8: MISSING VALUE ANALYSIS")
print("-" * 80)

print("\nMissing Values by Column:\n")
missing_analysis = []
for col in df.columns:
    null_count = df[col].isna().sum()
    null_pct = (null_count / len(df)) * 100
    
    if null_count > 0:
        print(f"  {col:30s}: {null_count:6,} ({null_pct:6.2f}%)")
        missing_analysis.append({
            "column": col,
            "null_count": int(null_count),
            "null_percent": round(null_pct, 2)
        })

if not missing_analysis:
    print("  [OK] No missing values found!")
else:
    total_missing = sum(m["null_count"] for m in missing_analysis)
    print(f"\n  Total Missing Cells: {total_missing:,} / {len(df) * len(df.columns):,}")

audit_results["audit_sections"]["missing_values"] = missing_analysis

# ============================================================================
# SECTION 9: DUPLICATE ANALYSIS
# ============================================================================
print("\n\nSECTION 9: DUPLICATE ANALYSIS")
print("-" * 80)

total_rows = len(df)
duplicated_rows = df.duplicated().sum()
duplicate_pct = (duplicated_rows / total_rows) * 100

print(f"\n  Total Rows: {total_rows:,}")
print(f"  Duplicate Rows: {duplicated_rows:,} ({duplicate_pct:.2f}%)")

# Check for duplicates in key columns
if date_columns and city_columns:
    date_col = date_columns[0]
    city_col = city_columns[0]
    
    key_duplicates = df.duplicated(subset=[city_col, date_col]).sum()
    key_dup_pct = (key_duplicates / total_rows) * 100
    print(f"  Duplicates (City + Date): {key_duplicates:,} ({key_dup_pct:.2f}%)")

audit_results["audit_sections"]["duplicates"] = {
    "total_duplicates": int(duplicated_rows),
    "duplicate_percent": round(duplicate_pct, 2)
}

# ============================================================================
# SECTION 10: DATA QUALITY METRICS
# ============================================================================
print("\n\nSECTION 10: DATA QUALITY METRICS")
print("-" * 80)

# Calculate quality score
quality_factors = {
    "completeness": 0,
    "uniqueness": 0,
    "date_coverage": 0,
    "required_fields": 0
}

# Completeness: % of non-null cells
total_cells = len(df) * len(df.columns)
non_null_cells = df.count().sum()
completeness = (non_null_cells / total_cells) * 100
quality_factors["completeness"] = completeness

# Uniqueness: inverse of duplicate rate
uniqueness = 100 - duplicate_pct
quality_factors["uniqueness"] = uniqueness

# Date coverage
if date_columns:
    date_col = date_columns[0]
    try:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        date_min = df[date_col].min()
        date_max = df[date_col].max()
        expected_days = (date_max - date_min).days
        actual_records = len(df[df[date_col].notna()])
        date_coverage = (actual_records / (expected_days + 1)) * 100
        date_coverage = min(date_coverage, 100)
        quality_factors["date_coverage"] = date_coverage
    except:
        quality_factors["date_coverage"] = 0
else:
    quality_factors["date_coverage"] = 0

# Required fields: % of required columns found
found_count = sum(1 for p in pollutants_found.values() if p.get("found", False))
required_fields = (found_count / len(required_pollutants)) * 100
quality_factors["required_fields"] = required_fields

# Overall quality score (weighted average)
quality_score = (
    completeness * 0.25 +
    uniqueness * 0.25 +
    date_coverage * 0.25 +
    required_fields * 0.25
)

print("\nQuality Factor Breakdown:")
print(f"  Completeness:      {completeness:6.2f}%  (Non-null cells)")
print(f"  Uniqueness:        {uniqueness:6.2f}%  (1 - duplicates)")
print(f"  Date Coverage:     {date_coverage:6.2f}%  (Records vs date span)")
print(f"  Required Fields:   {required_fields:6.2f}%  (Pollutants found)")
print(f"\n  Overall Quality Score: {quality_score:.2f}%")

# Quality rating
if quality_score >= 90:
    rating = "[EXCELLENT] 5 STARS"
elif quality_score >= 75:
    rating = "[VERY GOOD] 4 STARS"
elif quality_score >= 60:
    rating = "[GOOD] 3 STARS"
elif quality_score >= 45:
    rating = "[FAIR] 2 STARS"
else:
    rating = "[POOR] 1 STAR"

print(f"  Quality Rating: {rating}")

audit_results["audit_sections"]["quality_score"] = {
    "overall": round(quality_score, 2),
    "rating": rating,
    "factors": {k: round(v, 2) for k, v in quality_factors.items()}
}

# ============================================================================
# SECTION 11: SAMPLE DATA
# ============================================================================
print("\n\nSECTION 11: SAMPLE DATA")
print("-" * 80)

print("\nFirst 5 Rows:\n")
print(df.head(5).to_string())

print("\n\nData Types:\n")
print(df.dtypes)

# ============================================================================
# SECTION 12: SUITABILITY FOR VAYUGUARD
# ============================================================================
print("\n\nSECTION 12: SUITABILITY FOR VAYUGUARD")
print("-" * 80)

suitability = {
    "target_cities_present": all(target_found.values()) if target_found else False,
    "all_pollutants_present": all(p.get("found", False) for p in pollutants_found.values()),
    "date_range_sufficient": audit_results["audit_sections"].get("date_range", {}).get("days_span", 0) >= 365,
    "data_quality_sufficient": quality_score >= 75,
    "record_count_sufficient": row_count >= 1000
}

print("\nSuitability Checklist:")
print(f"  [YES] Target Cities Present:     {suitability['target_cities_present']}")
print(f"  [YES] All Pollutants Present:    {suitability['all_pollutants_present']}")
print(f"  [YES] Date Range Sufficient:     {suitability['date_range_sufficient']}")
print(f"  [YES] Data Quality >= 75%:       {suitability['data_quality_sufficient']}")
print(f"  [YES] Record Count >= 1000:      {suitability['record_count_sufficient']}")

overall_suitable = all(suitability.values())
status_str = "[YES]" if overall_suitable else "[NO]"
print(f"\n  OVERALL SUITABLE FOR VAYUGUARD: {status_str}")

audit_results["audit_sections"]["vayuguard_suitability"] = {
    "suitable": overall_suitable,
    "checklist": suitability
}

# ============================================================================
# SECTION 13: EXPECTED TRAINING DATA
# ============================================================================
print("\n\nSECTION 13: EXPECTED TRAINING DATA")
print("-" * 80)

if city_columns and date_columns:
    city_col = city_columns[0]
    date_col = date_columns[0]
    
    # Calculate records per city
    if city_col in df.columns:
        records_per_city = df[city_col].value_counts()
        
        print(f"\nRecords Per City:")
        for city, count in records_per_city.head(10).items():
            print(f"  {city:20s}: {count:6,} records")
        
        print(f"\nTarget Cities Training Data:")
        training_data = {}
        total_training = 0
        for target in ["Chennai", "Bengaluru", "Hyderabad"]:
            # Try exact match and variations
            city_data = df[df[city_col].str.contains(target, case=False, na=False)] if target in unique_cities else pd.DataFrame()
            if city_data.empty:
                for city in unique_cities:
                    if target.lower() in str(city).lower():
                        city_data = df[df[city_col] == city]
                        break
            
            count = len(city_data)
            training_data[target] = count
            total_training += count
            print(f"  {target:15s}: {count:6,} records")
        
        print(f"\n  Total Training Records (All 3 Cities): {total_training:,}")
        print(f"  Average Per City: {total_training/3:.0f}")
        if training_data:
            print(f"  Minimum City Records: {min(training_data.values()):,}")
        
        audit_results["audit_sections"]["training_data"] = {
            "total_records": total_training,
            "per_city": training_data,
            "average_per_city": round(total_training / 3, 0)
        }

# ============================================================================
# SECTION 14: PREPROCESSING REQUIREMENTS
# ============================================================================
print("\n\nSECTION 14: PREPROCESSING REQUIREMENTS")
print("-" * 80)

preprocessing_needed = []

# Check for missing values
if missing_analysis:
    preprocessing_needed.append("Handle missing values (imputation or removal)")

# Check for duplicates
if duplicated_rows > 0:
    preprocessing_needed.append("Remove duplicate rows")

# Check for date parsing
if date_columns:
    preprocessing_needed.append("Parse and standardize date column")

# Check column normalization
preprocessing_needed.append("Standardize column names (lowercase, remove spaces)")

# Check for outliers
preprocessing_needed.append("Detect and handle outliers in pollutant values")

# Check data type conversions
if col_count > 0:
    object_cols = len(df.select_dtypes(include=['object']).columns)
    if object_cols > 0:
        preprocessing_needed.append(f"Convert {object_cols} object columns to appropriate types")

preprocessing_needed.append("Create city-specific datasets for Chennai, Bengaluru, Hyderabad")
preprocessing_needed.append("Normalize/scale pollutant values for ML models")

print("\nPreprocessing Steps Required:\n")
for i, step in enumerate(preprocessing_needed, 1):
    print(f"  {i}. {step}")

audit_results["audit_sections"]["preprocessing"] = preprocessing_needed

# ============================================================================
# FINAL REPORT
# ============================================================================
print("\n\n" + "="*80)
print("AUDIT COMPLETE")
print("="*80)

print(f"\nQuality Score: {quality_score:.2f}% ({rating})")
suitable_str = "[YES]" if overall_suitable else "[NO]"
print(f"Suitable for VayuGuard: {suitable_str}")
print(f"Expected Training Records: {audit_results['audit_sections'].get('training_data', {}).get('total_records', 'Unknown'):,}")

# Save results - convert bools for JSON
def convert_for_json(obj):
    if isinstance(obj, dict):
        return {k: convert_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_for_json(item) for item in obj]
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, (np.integer, np.floating)):
        return int(obj) if isinstance(obj, np.integer) else float(obj)
    else:
        return obj

audit_results["final_recommendation"] = {
    "proceed_with_integration": bool(overall_suitable),
    "quality_score": round(quality_score, 2),
    "expected_training_records": audit_results["audit_sections"].get("training_data", {}).get("total_records", 0),
    "preprocessing_effort": "Medium" if len(preprocessing_needed) > 3 else "Low",
    "summary": "Dataset is suitable for VayuGuard ML model training with standard preprocessing" if overall_suitable else "Dataset requires significant review before use"
}

audit_results = convert_for_json(audit_results)

# Save JSON results
with open("kaggle_audit_results.json", "w") as f:
    json.dump(audit_results, f, indent=2)

print(f"\nDetailed results saved to: kaggle_audit_results.json")
print("="*80 + "\n")
