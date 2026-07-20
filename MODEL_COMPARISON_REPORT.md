# MODEL COMPARISON REPORT

**Generated:** 2026-06-16 01:43:44

**Status:** [COMPLETE] Model training and evaluation completed

---

## EXECUTIVE SUMMARY

Three machine learning models have been trained and evaluated on engineered AQI features using a chronological 80/20 train/test split. The **Linear Regression** model achieved the best performance with MAE of 69.0706.

**Data Split:**
- Training records: 4,725
- Test records: 1,182
- Split method: Chronological (preserves time-series integrity)
- Features: 16

---

## 1. DATASET SUMMARY

### Data Characteristics

| Metric | Value |
|--------|-------|
| Total records | 5,907 |
| Training records | 4,725 |
| Test records | 1,182 |
| Train/test ratio | 80/20 |
| Feature count | 16 |
| Target variable | AQI |
| Split method | Chronological (time-series safe) |

### Date Coverage

- **Training period:** 2019-01-25 00:00:00 to 2021-03-21 00:00:00
- **Test period:** 2021-03-22 00:00:00 to 2024-06-15 00:00:00
- **Total span:** 1968 days

---

## 2. MODELS TRAINED

### 2.1 Linear Regression (Baseline)

**Purpose:** Establish baseline performance for comparison

**Configuration:**
- Model type: OLS Linear Regression
- Parameters: Default scikit-learn
- Training approach: Closed-form solution

**Performance:**
- MAE: 69.0706
- RMSE: 83.0724
- MAPE: 0.6830
- R2: 0.2458
- Training time: 0.11s

### 2.2 Random Forest Regressor

**Purpose:** Capture non-linear relationships and feature interactions

**Configuration:**
- Model type: Ensemble (100 trees)
- Max depth: 15
- Random state: 42
- N jobs: -1 (parallel)

**Performance:**
- MAE: 71.6559
- RMSE: 86.0642
- MAPE: 0.7094
- R2: 0.1905
- Training time: 1.24s

### 2.3 XGBoost Regressor

**Purpose:** Gradient boosting with optimized loss minimization

**Configuration:**
- Model type: Gradient Boosting (100 trees)
- Max depth: 5
- Learning rate: 0.1
- Random state: 42

**Performance:**
- MAE: 71.3153
- RMSE: 85.9827
- MAPE: 0.6981
- R2: 0.1920
- Training time: 1.50s

---

## 3. EVALUATION METRICS COMPARISON

### Metric Definitions

| Metric | Formula | Interpretation |
|--------|---------|-----------------|
| **MAE** | Mean(abs(y_true - y_pred)) | Average absolute error (in AQI points) |
| **RMSE** | sqrt(Mean((y_true - y_pred)^2)) | Penalizes large errors more heavily |
| **MAPE** | Mean(abs((y_true - y_pred) / y_true)) | Percentage error (scale-independent) |
| **R2** | 1 - (SS_res / SS_tot) | Proportion of variance explained (0-1) |

### Performance Comparison Table

| Metric | Linear Regression | Random Forest | XGBoost |
|--------|-------------------|---------------|---------|
| **MAE** | 69.0706 | 71.6559 | 71.3153 |
| **RMSE** | 83.0724 | 86.0642 | 85.9827 |
| **MAPE** | 0.6830 | 0.7094 | 0.6981 |
| **R2** | 0.2458 | 0.1905 | 0.1920 |
| **Training Time (s)** | 0.11 | 1.24 | 1.50 |

---

## 4. FEATURE IMPORTANCE

### Random Forest - Top 10 Features

1. **rolling_mean_6**: 0.2356
2. **lag_3**: 0.0985
3. **rolling_std_6**: 0.0963
4. **lag_1**: 0.0940
5. **rolling_std_12**: 0.0668
6. **lag_24**: 0.0577
7. **rolling_std_24**: 0.0558
8. **lag_12**: 0.0531
9. **lag_6**: 0.0519
10. **rolling_mean_24**: 0.0495


### XGBoost - Top 10 Features

1. **rolling_mean_6**: 0.2753
2. **lag_3**: 0.0909
3. **lag_1**: 0.0752
4. **rolling_std_12**: 0.0644
5. **rolling_std_6**: 0.0576
6. **rolling_std_24**: 0.0566
7. **rolling_mean_24**: 0.0521
8. **rolling_mean_12**: 0.0500
9. **month**: 0.0488
10. **lag_24**: 0.0487


---

## 5. MODEL SELECTION & RECOMMENDATION

### Selection Criteria

Models evaluated using multiple criteria:
1. **Primary:** Lowest MAE (Mean Absolute Error)
2. **Secondary:** Lowest RMSE (handles outliers)
3. **Tertiary:** Lowest MAPE (percentage error)

### Recommended Production Model

**[SELECTED] Linear Regression**

**Justification:**
- Lowest MAE: 69.0706
- RMSE: 83.0724
- MAPE: 0.6830
- R2: 0.2458

---

## 6. EXECUTION SUMMARY

| Step | Status | Result |
|------|--------|--------|
| Data loading | [PASS] | 5,907 records loaded |
| Frequency validation | [PASS] | DAILY data detected |
| Train/test split | [PASS] | Chronological 80/20 |
| Linear Regression | [PASS] | MAE: 69.0706 |
| Random Forest | [PASS] | MAE: 71.6559 |
| XGBoost | [PASS] | MAE: 71.3153 |
| Model selection | [PASS] | Linear Regression selected |
| Serialization | [PASS] | 3 models saved |
| Metrics saved | [PASS] | metrics.json |

---

## FINAL DECISION

**PRODUCTION MODEL:** Linear Regression

**STATUS:** [READY FOR DEPLOYMENT]

---

**Report Generated:** 2026-06-16 01:43:44
