#!/usr/bin/env python
"""
ML RETRAINING PROJECT STATUS DASHBOARD
Shows complete status of all phases
Provides guidance on next steps
"""

import psycopg2
import os
from datetime import datetime

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'vayuguard',
    'user': 'vayuguard_user',
    'password': 'vayuguard_pass'
}

def connect_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except:
        return None

def get_database_stats(conn):
    """Get stats from database."""
    if not conn:
        return None
    
    cur = conn.cursor()
    
    # Get record count
    cur.execute("SELECT COUNT(*) FROM aqi_data")
    total_records = cur.fetchone()[0]
    
    # Get cities
    cur.execute("SELECT DISTINCT city FROM aqi_data")
    cities = [row[0] for row in cur.fetchall()]
    
    # Get feature completeness
    cur.execute("""
    SELECT 
        COUNT(CASE WHEN aqi IS NOT NULL THEN 1 END),
        COUNT(CASE WHEN temperature IS NOT NULL THEN 1 END)
    FROM aqi_data
    """)
    aqi_count, temp_count = cur.fetchone()
    
    # Check tables
    cur.execute("""
    SELECT EXISTS(
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'engineered_features'
    )
    """)
    has_engineered = cur.fetchone()[0]
    
    cur.close()
    
    return {
        'total_records': total_records,
        'cities': cities,
        'aqi_completeness': aqi_count,
        'temp_completeness': temp_count,
        'has_engineered': has_engineered
    }

def check_files():
    """Check for generated files and models."""
    files = {
        'phase1_report': os.path.exists('DATASET_READINESS_REPORT.md'),
        'phase2_report': os.path.exists('PHASE2_FEATURE_ENGINEERING_REPORT.md'),
        'model_comparison_report': os.path.exists('MODEL_COMPARISON_REPORT.md'),
        'api_integration_guide': os.path.exists('API_INTEGRATION_GUIDE.md'),
        'baseline_model': os.path.exists('ml-service/models/baseline_model.pkl'),
        'rf_model': os.path.exists('ml-service/models/random_forest_model.pkl'),
        'xgb_model': os.path.exists('ml-service/models/xgboost_model.pkl'),
    }
    return files

def print_dashboard():
    """Print status dashboard."""
    print("\n" + "=" * 80)
    print(" " * 20 + "ML RETRAINING PROJECT STATUS DASHBOARD")
    print("=" * 80)
    
    # Database status
    conn = connect_db()
    stats = get_database_stats(conn) if conn else None
    files = check_files()
    
    if conn:
        conn.close()
    
    print("\n📊 DATA COLLECTION STATUS")
    print("-" * 80)
    
    if stats:
        progress = min(100, stats['total_records'] / 500 * 100)
        bar = "█" * int(progress / 5) + "░" * (20 - int(progress / 5))
        print(f"Records Collected: {stats['total_records']}/500 [{bar}] {progress:.1f}%")
        print(f"Cities: {', '.join(stats['cities']) if stats['cities'] else 'None'}")
        print(f"AQI Data: {stats['aqi_completeness']} records")
        print(f"Weather Data: {stats['temp_completeness']} records")
    else:
        print("❌ Cannot connect to database")
    
    print("\n✅ PHASE 1: DATASET ANALYSIS")
    print("-" * 80)
    status1 = "✅ COMPLETE" if files['phase1_report'] else "❌ NOT RUN"
    print(f"Status: {status1}")
    if files['phase1_report']:
        print("Report: DATASET_READINESS_REPORT.md")
        print("Details: Dataset statistics, completeness analysis, recommendations")
    
    print("\n📈 PHASE 2: FEATURE ENGINEERING")
    print("-" * 80)
    if stats and stats['total_records'] >= 500:
        status2 = "✅ COMPLETE" if files['phase2_report'] else "🔴 BLOCKED - Run automation"
        print(f"Status: {status2}")
        print("Threshold: 500+ records ✅ MET")
        if files['phase2_report']:
            print("Report: PHASE2_FEATURE_ENGINEERING_REPORT.md")
            print("Details: 15 engineered features, lag/rolling/temporal")
    else:
        needed = 500 - (stats['total_records'] if stats else 0)
        print(f"Status: ⏳ BLOCKED - Need {needed} more records")
        print(f"Threshold: {stats['total_records'] if stats else 0}/500 records")
        print(f"Progress: {min(100, (stats['total_records'] if stats else 0) / 500 * 100):.1f}%")
    
    print("\n🤖 PHASE 3: MODEL TRAINING")
    print("-" * 80)
    if files['phase2_report'] or files['baseline_model']:
        models_trained = sum([files['baseline_model'], files['rf_model'], files['xgb_model']])
        status3 = f"✅ COMPLETE ({models_trained}/3 models)" if models_trained > 0 else "⏳ PENDING"
        print(f"Status: {status3}")
        if files['baseline_model']:
            print("  ✅ Baseline model trained")
        if files['rf_model']:
            print("  ✅ Random Forest model trained")
        if files['xgb_model']:
            print("  ✅ XGBoost model trained")
    else:
        print("Status: ⏳ BLOCKED - Complete Phase 2 first")
    
    print("\n📋 PHASE 4: MODEL COMPARISON")
    print("-" * 80)
    status4 = "✅ COMPLETE" if files['model_comparison_report'] else "⏳ PENDING"
    print(f"Status: {status4}")
    if files['model_comparison_report']:
        print("Report: MODEL_COMPARISON_REPORT.md")
        print("Details: Best model selection, feature importance, recommendations")
    
    print("\n🚀 PHASE 5: API INTEGRATION")
    print("-" * 80)
    status5 = "✅ COMPLETE" if files['api_integration_guide'] else "⏳ PENDING"
    print(f"Status: {status5}")
    if files['api_integration_guide']:
        print("Documents Generated:")
        print("  - model_loader.py (integration script)")
        print("  - API_INTEGRATION_GUIDE.md")
        print("  - DEPLOYMENT_INSTRUCTIONS.md")
    
    # Overall status
    print("\n" + "=" * 80)
    print("📊 OVERALL PROJECT STATUS")
    print("=" * 80)
    
    if stats and stats['total_records'] >= 500:
        if files['baseline_model']:
            print("✅ MODELS TRAINED - Ready for deployment")
            print("\nNext Steps:")
            print("  1. Review MODEL_COMPARISON_REPORT.md")
            print("  2. Run phase5_api_integration.py to generate API docs")
            print("  3. Update ml-service/app.py with model_loader")
            print("  4. Deploy and test")
        else:
            print("🟡 THRESHOLD MET - Ready for training")
            print("\nNext Steps:")
            print("  1. Run: python ml_pipeline_automation.py")
            print("  2. This will run Phases 2-3 automatically")
            print("  3. Then run Phase 5 for API integration")
    else:
        needed = 500 - (stats['total_records'] if stats else 0)
        print(f"🟡 COLLECTING DATA - {needed} records needed")
        print("\nNext Steps:")
        print("  1. Monitor data collection progress")
        print("  2. Check DATASET_READINESS_REPORT.md daily")
        print("  3. When records reach 500:")
        print("     python ml_pipeline_automation.py")
    
    print("\n" + "=" * 80)
    print("🔗 USEFUL COMMANDS")
    print("=" * 80)
    print("\nData Analysis:")
    print("  python phase1_dataset_analysis.py      # Analyze data")
    print("  python ml_pipeline_automation.py        # Auto-run all phases")
    
    print("\nManual Phase Execution:")
    print("  python phase2_feature_engineering.py   # Feature engineering")
    print("  python phase3_model_training.py        # Train models")
    print("  python phase5_api_integration.py       # API integration")
    
    print("\nView Reports:")
    print("  DATASET_READINESS_REPORT.md")
    print("  PHASE2_FEATURE_ENGINEERING_REPORT.md")
    print("  MODEL_COMPARISON_REPORT.md")
    print("  API_INTEGRATION_GUIDE.md")
    print("  ML_PIPELINE_STATUS.md")
    
    print("\n" + "=" * 80)
    print(f"Dashboard Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")

if __name__ == '__main__':
    print_dashboard()
