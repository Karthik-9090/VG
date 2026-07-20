# DATASET REPORT

**Generated:** 2026-06-15 22:06:21  
**Dataset File:** final_dataset.csv

---

## DATASET OVERVIEW

### Dimensions

| Metric | Value |
|--------|-------|
| **Total Rows** | 3 |
| **Total Columns** | 16 |
| **Time Period** | 1 day(s) |

### Date Range

- **Start Date:** 2026-06-15 20:54:41.500201
- **End Date:** 2026-06-15 20:54:41.500201
- **Duration:** 1 day(s)

---

## CITY DISTRIBUTION

| City | Count | Percentage |
|------|-------|------------|
| Bengaluru | 1 | 33.3% |
| Chennai | 1 | 33.3% |
| Hyderabad | 1 | 33.3% |
| **TOTAL** | **3** | **100%** |

---

## MISSING VALUES ANALYSIS

| Column | Missing Count | Missing % | Data Type |
|--------|---------------|-----------|-----------|
| city | 0 | 0.0% | object |
| aqi | 0 | 0.0% | int64 |
| pm25 | 3 | 100.0% | float64 |
| pm10 | 3 | 100.0% | float64 |
| no2 | 3 | 100.0% | float64 |
| o3 | 3 | 100.0% | float64 |
| so2 | 3 | 100.0% | float64 |
| co | 3 | 100.0% | float64 |
| temperature | 3 | 100.0% | float64 |
| humidity | 3 | 100.0% | float64 |
| wind_speed | 3 | 100.0% | float64 |
| pressure | 3 | 100.0% | float64 |
| hour | 0 | 0.0% | int64 |
| day_of_week | 0 | 0.0% | int64 |
| month | 0 | 0.0% | int64 |
| recorded_at | 0 | 0.0% | datetime64[ns] |

### Missing Data Summary

- **Columns with Complete Data:** 6
- **Columns with Any Missing:** 10
- **Total Missing Values:** 30
- **Missing % of Total:** 62.5%

---

## DUPLICATE ANALYSIS

| Metric | Value |
|--------|-------|
| **Duplicate Rows** | 0 |
| **Duplicate % | 0.0% |
| **Unique Cities** | 3 |
| **Unique Timestamps** | 1 |

---

## DATA SUMMARY STATISTICS

### AQI Column

| Statistic | Value |
|-----------|-------|
| Count | 3 |
| Mean | 81.67 |
| Median | 82.00 |
| Min | 68 |
| Max | 95 |
| Std Dev | 13.50 |

### Temporal Features

| Feature | Unique Values | Range |
|---------|---------------|-------|
| **Hour** | 1 | 20-20 |
| **Day of Week** | 1 | 0-0 |
| **Month** | 1 | 6-6 |

---

## SAMPLE DATA

### First 3 Rows

```
        city  aqi  pm25  pm10  no2  o3  so2  co  temperature  humidity  wind_speed  pressure  hour  day_of_week  month                recorded_at
0  Bengaluru   82   NaN   NaN  NaN NaN  NaN NaN          NaN       NaN         NaN       NaN    20            0      6 2026-06-15 20:54:41.500201
1    Chennai   68   NaN   NaN  NaN NaN  NaN NaN          NaN       NaN         NaN       NaN    20            0      6 2026-06-15 20:54:41.500201
2  Hyderabad   95   NaN   NaN  NaN NaN  NaN NaN          NaN       NaN         NaN       NaN    20            0      6 2026-06-15 20:54:41.500201
```

### Last 3 Rows

```
        city  aqi  pm25  pm10  no2  o3  so2  co  temperature  humidity  wind_speed  pressure  hour  day_of_week  month                recorded_at
0  Bengaluru   82   NaN   NaN  NaN NaN  NaN NaN          NaN       NaN         NaN       NaN    20            0      6 2026-06-15 20:54:41.500201
1    Chennai   68   NaN   NaN  NaN NaN  NaN NaN          NaN       NaN         NaN       NaN    20            0      6 2026-06-15 20:54:41.500201
2  Hyderabad   95   NaN   NaN  NaN NaN  NaN NaN          NaN       NaN         NaN       NaN    20            0      6 2026-06-15 20:54:41.500201
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

- **Fully Complete Columns:** 6 / 16
- **Primary Key Present:** YES (city + recorded_at combination)
- **Time Coverage:** 1 day(s)

### Uniqueness

- **Unique Records:** 3
- **Duplicate Records:** 0
- **Duplicate Rate:** 0.00%

### Validity

- **Valid AQI Values:** YES (0-500 scale)
- **Valid Hour Values:** YES (0-23)
- **Valid Day Values:** YES (0-6)
- **Valid Month Values:** YES (1-12)

---

## RECOMMENDATIONS

1. **Data Volume:** Only 3 records available. Recommend accumulating more data for robust ML training.

2. **Missing Pollutants:** Pollutant columns (PM2.5, PM10, NO₂, O₃, SO₂, CO) are 100% missing. Consider:
   - Integrating with WAQI API for additional pollutants
   - Using CPCB data sources
   - Calculating from AQI using lookup tables

3. **Weather Data:** Gaps in weather information. Consider:
   - Open-Meteo integration for completeness
   - Interpolation for missing timestamps
   - Using historical weather averages

4. **Temporal Coverage:** Limited to 1 day(s). For meaningful ML forecasting:
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

Generated on: 2026-06-15 22:06:21
