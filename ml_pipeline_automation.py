#!/usr/bin/env python
"""
ML Pipeline Automation & Monitoring
Orchestrates all phases of model retraining
Checks data readiness and runs phases sequentially
"""

import psycopg2
import pandas as pd
from datetime import datetime
import subprocess
import sys
import os

# Database configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'vayuguard',
    'user': 'vayuguard_user',
    'password': 'vayuguard_pass'
}

PHASE_1_THRESHOLD = 50  # Minimum records for Phase 1 analysis
PHASE_2_THRESHOLD = 500  # Minimum records to start Phase 2

def connect_db():
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Error: Database connection failed: {e}")
        return None

def get_record_count(conn):
    """Get total records in aqi_data."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM aqi_data")
    count = cur.fetchone()[0]
    cur.close()
    return count

def check_table_exists(conn, table_name):
    """Check if table exists in database."""
    cur = conn.cursor()
    cur.execute(f"""
    SELECT EXISTS(
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = '{table_name}'
    )
    """)
    exists = cur.fetchone()[0]
    cur.close()
    return exists

def run_phase_1():
    """Run Phase 1: Dataset Analysis."""
    print()
    print("=" * 70)
    print("RUNNING PHASE 1: DATASET READINESS ANALYSIS")
    print("=" * 70)
    result = subprocess.run(
        ["python", "phase1_dataset_analysis.py"],
        capture_output=False
    )
    return result.returncode == 0

def run_phase_2():
    """Run Phase 2: Feature Engineering."""
    print()
    print("=" * 70)
    print("RUNNING PHASE 2: FEATURE ENGINEERING")
    print("=" * 70)
    result = subprocess.run(
        ["python", "phase2_feature_engineering.py"],
        capture_output=False
    )
    return result.returncode == 0

def run_phase_3():
    """Run Phase 3: Model Training."""
    print()
    print("=" * 70)
    print("RUNNING PHASE 3: MODEL TRAINING")
    print("=" * 70)
    result = subprocess.run(
        ["python", "phase3_model_training.py"],
        capture_output=False
    )
    return result.returncode == 0

def generate_status_report(record_count, has_engineered, has_models):
    """Generate pipeline status report."""
    report = f"""# ML PIPELINE STATUS REPORT

**Generated:** {datetime.now().isoformat()}

## Pipeline Status Overview

| Component | Status | Details |
|-----------|--------|---------|
| Data Collection | ✅ Active | {record_count} records in aqi_data |
| Phase 1: Analysis | ✅ Complete | DATASET_READINESS_REPORT.md generated |
| Phase 2: Features | {'✅' if has_engineered else '⏳'} {'Complete' if has_engineered else 'Waiting'} | {'Engineered features table created' if has_engineered else 'Waiting for 500+ records'} |
| Phase 3: Training | {'✅' if has_models else '⏳'} {'Complete' if has_models else 'Waiting'} | {'Models trained and saved' if has_models else 'Waiting for Phase 2'} |
| Phase 4: Comparison | {'✅' if has_models else '⏳'} {'Complete' if has_models else 'Pending'} | {'MODEL_COMPARISON_REPORT.md generated' if has_models else 'Waiting for Phase 3'} |
| Phase 5: API Update | {'✅' if has_models else '⏳'} {'Complete' if has_models else 'Pending'} | {'Forecast API using best model' if has_models else 'Waiting for Phase 3'} |

## Data Collection Progress

**Current Records:** {record_count}
**Phase 2 Threshold:** {PHASE_2_THRESHOLD}
**Records Needed:** {max(0, PHASE_2_THRESHOLD - record_count)}
**Progress:** {record_count}/{PHASE_2_THRESHOLD} ({min(100, record_count/PHASE_2_THRESHOLD*100):.1f}%)

## Generated Artifacts

### Reports
- DATASET_READINESS_REPORT.md
{f'- PHASE2_FEATURE_ENGINEERING_REPORT.md' if has_engineered else ''}
{f'- MODEL_COMPARISON_REPORT.md' if has_models else ''}

### Models
{f'''- ml-service/models/baseline_model.pkl
- ml-service/models/random_forest_model.pkl
- ml-service/models/xgboost_model.pkl''' if has_models else '(Not yet trained)'}

## Next Steps

"""
    
    if record_count < PHASE_2_THRESHOLD:
        report += f"""1. **Continue Data Collection**
   - Need {PHASE_2_THRESHOLD - record_count} more records
   - Current collection rate: Check collection logs
   - ETA: Monitor daily

2. **Check Data Quality**
   - Review DATASET_READINESS_REPORT.md
   - Current overall completeness: Check report
   - Ensure weather data is being captured

3. **When 500+ Records Collected:**
   - Run Phase 2: Feature Engineering
   - Run Phase 3: Model Training
   - Generate comparison reports
   - Update API with best model
"""
    else:
        report += f"""1. **Proceed with Feature Engineering**
   - Data threshold reached: {record_count} records
   - Ready to create engineered features
   - Expected duration: <1 minute

2. **Model Training**
   - After Phase 2 completes
   - Will train 3 models (Baseline, RF, XGBoost)
   - Compare performance metrics
   - Expected duration: 1-2 minutes

3. **API Integration**
   - Deploy best performing model
   - Update `/forecast` endpoint
   - Test endpoint validation
   - Expected duration: <1 minute

"""
    
    report += f"""## Recommendation

**Current Status:** {'🟢 Ready for Phase 2' if record_count >= PHASE_2_THRESHOLD else '🟡 Collecting data'}

### Action Items
1. Monitor data collection progress
2. Review DATASET_READINESS_REPORT.md for quality metrics
3. When records reach {PHASE_2_THRESHOLD}:
   - Execute `python ml_pipeline_automation.py --run-all`
   - Or run phases individually as needed

---

**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return report

def main():
    """Main automation routine."""
    print("=" * 70)
    print("ML PIPELINE AUTOMATION & MONITORING")
    print("=" * 70)
    print()
    
    # Connect to database
    print("📡 Checking database connection...")
    conn = connect_db()
    if not conn:
        print("❌ Cannot connect to database")
        sys.exit(1)
    
    # Get data status
    record_count = get_record_count(conn)
    has_engineered = check_table_exists(conn, 'engineered_features')
    has_models = os.path.exists('ml-service/models/baseline_model.pkl')
    
    print(f"📊 Database Status:")
    print(f"  - Records: {record_count}")
    print(f"  - Engineered Features Table: {'✅ Yes' if has_engineered else '❌ No'}")
    print(f"  - Trained Models: {'✅ Yes' if has_models else '❌ No'}")
    print()
    
    # Phase 1: Always run (daily analysis)
    if record_count > 0:
        print("Running Phase 1: Dataset Analysis...")
        if run_phase_1():
            print("✅ Phase 1 Complete")
        else:
            print("❌ Phase 1 Failed")
            sys.exit(1)
    
    # Phase 2: Run if threshold met
    if record_count >= PHASE_2_THRESHOLD and not has_engineered:
        print()
        print("✅ Phase 2 Threshold Met - Running Feature Engineering...")
        if run_phase_2():
            print("✅ Phase 2 Complete")
            has_engineered = True
        else:
            print("❌ Phase 2 Failed")
    
    # Phase 3: Run if Phase 2 complete
    if has_engineered and not has_models:
        print()
        print("✅ Phase 2 Complete - Running Model Training...")
        if run_phase_3():
            print("✅ Phase 3 Complete")
            has_models = True
        else:
            print("❌ Phase 3 Failed")
    
    # Generate status report
    print()
    print("📝 Generating pipeline status report...")
    conn.close()
    
    status_report = generate_status_report(record_count, has_engineered, has_models)
    
    report_path = "ML_PIPELINE_STATUS.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(status_report)
    
    print(f"✅ Status report saved to {report_path}")
    print()
    print("=" * 70)
    print("PIPELINE AUTOMATION COMPLETE")
    print("=" * 70)
    print()
    
    # Display summary
    print("CURRENT STATUS:")
    print(f"  Records:           {record_count}/{PHASE_2_THRESHOLD}")
    if record_count >= PHASE_2_THRESHOLD:
        print(f"  Phase 1:           ✅ Complete")
        print(f"  Phase 2:           {'✅ Complete' if has_engineered else '⏳ Pending'}")
        print(f"  Phase 3:           {'✅ Complete' if has_models else '⏳ Pending'}")
        print(f"  Phase 4:           {'✅ Complete' if has_models else '⏳ Pending'}")
        print(f"  Phase 5:           {'✅ Complete' if has_models else '⏳ Pending'}")
    else:
        print(f"  Phase 1:           ✅ Complete")
        print(f"  Phase 2:           ⏳ Waiting ({PHASE_2_THRESHOLD - record_count} more records needed)")
    
    print()
    print("NEXT STEPS:")
    if record_count < PHASE_2_THRESHOLD:
        print(f"  1. Continue collecting data ({record_count}/{PHASE_2_THRESHOLD})")
        print("  2. Review DATASET_READINESS_REPORT.md")
        print("  3. When threshold reached, run this script again")
    elif not has_engineered:
        print("  1. Feature engineering threshold met")
        print("  2. Re-run this script to start Phase 2")
    elif not has_models:
        print("  1. Feature engineering complete")
        print("  2. Re-run this script to start Phase 3 (model training)")
    else:
        print("  1. All phases complete!")
        print("  2. Next: Update forecast API with best model")
        print("  3. See MODEL_COMPARISON_REPORT.md for recommendations")

if __name__ == '__main__':
    main()
