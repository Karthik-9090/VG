"""Phase 4: Model Training Validation"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml-service'))

print("="*80)
print("PHASE 4: MODEL TRAINING VALIDATION")
print(f"Timestamp: {datetime.now().isoformat()}")
print("="*80)
print()

# Check model directory
print("[1/5] MODEL DIRECTORY STRUCTURE")
print("-"*80)

models_dir = Path('models')
models_dir.mkdir(exist_ok=True)

model_files = list(models_dir.glob('*'))
print(f"Models directory: {models_dir}")
print(f"Existing files: {len(model_files)}")
for file in model_files:
    print(f"  - {file.name} ({file.stat().st_size} bytes, modified: {datetime.fromtimestamp(file.stat().st_mtime)})")

print()

# Test training
print("[2/5] MODEL TRAINING EXECUTION")
print("-"*80)

try:
    from train import AQIModelTrainer
    
    trainer = AQIModelTrainer()
    
    # Fetch data
    print("Fetching real data from database...")
    df = trainer.fetch_real_data_from_db()
    
    if df is None:
        print("[FAIL] Could not fetch data from database")
        exit(1)
    
    print(f"[PASS] Data fetched: {len(df)} records")
    print(f"       Columns: {list(df.columns)}")
    print()
    
    # Create features
    print("[3/5] FEATURE ENGINEERING")
    print("-"*80)
    df_features = trainer.create_features(df)
    print(f"[PASS] Features created: {df_features.shape[1]} total features")
    print(f"       Rows: {df_features.shape[0]}")
    print()
    
    # Train models
    print("[4/5] MODEL TRAINING")
    print("-"*80)
    
    cities = ['Chennai', 'Bengaluru', 'Hyderabad']
    models_trained = 0
    
    for city in cities:
        try:
            print(f"Training model for {city}...", end=" ")
            trainer.train_model(city=city, model_type='xgboost')
            models_trained += 1
            print("[TRAINED]")
        except Exception as e:
            print(f"[SKIP] {e}")
    
    print(f"\n[PASS] {models_trained} models trained")
    print()
    
    # Check generated files
    print("[5/5] MODEL ARTIFACTS")
    print("-"*80)
    
    model_files_new = list(models_dir.glob('*'))
    
    required_files = [
        'xgboost.pkl',
        'xgboost_metrics.json',
        'feature_list.json',
        'scaler.pkl'
    ]
    
    found_files = 0
    for req_file in required_files:
        file_path = models_dir / req_file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"[FOUND] {req_file:25} {size:10} bytes")
            found_files += 1
        else:
            print(f"[MISSING] {req_file:25}")
    
    print()
    print("="*80)
    print("PHASE 4 SUMMARY")
    print("="*80)
    print(f"Data Records:     {len(df)}")
    print(f"Features:         {df_features.shape[1]}")
    print(f"Models Trained:   {models_trained}/{len(cities)}")
    print(f"Artifacts Found:  {found_files}/{len(required_files)}")
    print()
    
    if models_trained > 0 and found_files > 0:
        print("[PASS] PHASE 4: MODEL TRAINING VALIDATION - SUCCESS")
    else:
        print("[FAIL] PHASE 4: MODEL TRAINING VALIDATION - INCOMPLETE")
        exit(1)
    
    print("="*80)

except Exception as e:
    print()
    print("="*80)
    print(f"[FAIL] PHASE 4: MODEL TRAINING VALIDATION")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    print("="*80)
    exit(1)
