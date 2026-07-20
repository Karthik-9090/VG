#!/usr/bin/env python3
"""
VayuGuard v2.0 Deployment Automation
One-command setup and launch for production
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

class VayuGuardDeployment:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.start_time = datetime.now()
        self.steps_completed = []
        self.errors = []
    
    def log(self, message, level='INFO'):
        """Print formatted log message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        if level == 'INFO':
            print(f"ℹ️  [{timestamp}] {message}")
        elif level == 'SUCCESS':
            print(f"✅ [{timestamp}] {message}")
        elif level == 'ERROR':
            print(f"❌ [{timestamp}] {message}")
        elif level == 'WARN':
            print(f"⚠️  [{timestamp}] {message}")
    
    def run_command(self, cmd, cwd=None, name="Command"):
        """Run shell command and capture output"""
        try:
            self.log(f"Running: {name}")
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(cwd or self.project_root),
                capture_output=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.log(f"{name} completed", level='SUCCESS')
                self.steps_completed.append(name)
                return True
            else:
                error_msg = result.stderr.decode()
                self.log(f"{name} failed: {error_msg}", level='ERROR')
                self.errors.append(f"{name}: {error_msg}")
                return False
        
        except subprocess.TimeoutExpired:
            self.log(f"{name} timeout (>5 min)", level='ERROR')
            self.errors.append(f"{name}: Timeout")
            return False
        except Exception as e:
            self.log(f"{name} error: {e}", level='ERROR')
            self.errors.append(f"{name}: {e}")
            return False
    
    def install_dependencies(self):
        """Install all Python dependencies"""
        self.log("\n" + "="*60)
        self.log("STEP 1: Installing Dependencies")
        self.log("="*60)
        
        # ML Service
        self.run_command(
            f'"{sys.executable}" -m pip install -q -r requirements.txt',
            cwd=self.project_root / "ml-service",
            name="ML Service dependencies"
        )
        
        # Data Pipeline
        self.run_command(
            f'"{sys.executable}" -m pip install -q -r requirements.txt',
            cwd=self.project_root / "data-pipeline",
            name="Data Pipeline dependencies"
        )
        
        # Scheduler dependencies (requests, schedule)
        self.run_command(
            f'"{sys.executable}" -m pip install -q schedule requests',
            name="Scheduler dependencies"
        )
    
    def create_directories(self):
        """Create necessary directories"""
        self.log("\n" + "="*60)
        self.log("STEP 2: Creating Directories")
        self.log("="*60)
        
        directories = [
            self.project_root / "ml-service" / "models",
            self.project_root / "data" / "backups",
            self.project_root / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.log(f"Created/verified: {directory}")
        
        self.steps_completed.append("Create directories")
    
    def train_models(self):
        """Train initial ML models"""
        self.log("\n" + "="*60)
        self.log("STEP 3: Training ML Models")
        self.log("="*60)
        
        self.run_command(
            f'"{sys.executable}" train.py',
            cwd=self.project_root / "ml-service",
            name="Model training"
        )
        
        # Verify models were created
        models_dir = self.project_root / "ml-service" / "models"
        model_files = list(models_dir.glob("*.pkl"))
        
        if model_files:
            self.log(f"✅ Created {len(model_files)} model files", level='SUCCESS')
        else:
            self.log("⚠️  No model files found", level='WARN')
    
    def fetch_real_data(self):
        """Fetch initial real data from OpenAQ"""
        self.log("\n" + "="*60)
        self.log("STEP 4: Fetching Real Data")
        self.log("="*60)
        
        self.run_command(
            f'"{sys.executable}" openaq_fetcher.py',
            cwd=self.project_root / "data-pipeline",
            name="Real data ingestion"
        )
        
        # Verify CSV was created
        csv_file = self.project_root / "data" / "openaq_current.csv"
        if csv_file.exists():
            size_kb = csv_file.stat().st_size / 1024
            self.log(f"✅ Data file created ({size_kb:.1f} KB)", level='SUCCESS')
        else:
            self.log("⚠️  Data file not found", level='WARN')
    
    def verify_services(self):
        """Verify all services are configured"""
        self.log("\n" + "="*60)
        self.log("STEP 5: Verifying Services")
        self.log("="*60)
        
        services = {
            'Frontend': self.project_root / "frontend" / "package.json",
            'Backend': self.project_root / "backend" / "package.json",
            'ML Service': self.project_root / "ml-service" / "app-mock.py",
            'Database': self.project_root / "infra" / "schema.sql"
        }
        
        for service, path in services.items():
            if path.exists():
                self.log(f"✅ {service}: Found", level='SUCCESS')
            else:
                self.log(f"❌ {service}: Missing ({path})", level='ERROR')
    
    def generate_config(self):
        """Generate deployment configuration"""
        self.log("\n" + "="*60)
        self.log("STEP 6: Generating Configuration")
        self.log("="*60)
        
        config = {
            "deployment_date": datetime.now().isoformat(),
            "version": "2.0.0",
            "services": {
                "frontend": {
                    "port": 3000,
                    "status": "ready"
                },
                "backend": {
                    "port": 8000,
                    "database": "PostgreSQL",
                    "status": "ready"
                },
                "ml_service": {
                    "port": 8001,
                    "models": "Random Forest",
                    "data_source": "OpenAQ",
                    "status": "ready"
                },
                "scheduler": {
                    "data_ingestion": "Every 6 hours",
                    "model_retraining": "Every 24 hours",
                    "status": "ready"
                }
            },
            "data_pipeline": {
                "source": "OpenAQ API",
                "update_frequency": "6 hours",
                "cities": ["Chennai", "Bengaluru", "Hyderabad", "Mumbai", "Delhi"]
            }
        }
        
        config_file = self.project_root / "deployment-config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.log(f"✅ Configuration saved to {config_file.name}", level='SUCCESS')
    
    def generate_summary(self):
        """Generate deployment summary"""
        self.log("\n" + "="*60)
        self.log("DEPLOYMENT SUMMARY")
        self.log("="*60)
        
        duration = (datetime.now() - self.start_time).total_seconds()
        
        self.log(f"\n✅ Completed Steps ({len(self.steps_completed)}):")
        for i, step in enumerate(self.steps_completed, 1):
            print(f"  {i}. {step}")
        
        if self.errors:
            self.log(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        self.log(f"\n⏱️  Total time: {duration:.1f} seconds")
        
        self.log("\n🚀 NEXT STEPS:")
        print("  1. Start services:")
        print("     cd backend && npm start")
        print("     cd frontend && npm run dev")
        print("     cd ml-service && python app-mock.py")
        print("")
        print("  2. Start scheduler:")
        print("     python scheduler.py")
        print("")
        print("  3. Access the application:")
        print("     http://localhost:3000")
        print("")
        print("  4. Monitor the system:")
        print("     tail -f scheduler.log")
        
        self.log("\n📖 Documentation:")
        print("  - REAL_DATA_SETUP.md: Configuration guide")
        print("  - PRODUCTION_READINESS_ASSESSMENT.md: Deployment checklist")
        print("  - IMPLEMENTATION.md: Architecture details")
        
        self.log("\n" + "="*60)
    
    def deploy(self, steps=None):
        """Run full deployment"""
        default_steps = [
            'install_dependencies',
            'create_directories',
            'train_models',
            'fetch_real_data',
            'verify_services',
            'generate_config'
        ]
        
        steps = steps or default_steps
        
        self.log("\n🚀 VayuGuard v2.0 Deployment Automation")
        self.log("="*60)
        
        for step in steps:
            if hasattr(self, step):
                try:
                    getattr(self, step)()
                except Exception as e:
                    self.log(f"Step {step} error: {e}", level='ERROR')
                    self.errors.append(f"{step}: {e}")
        
        self.generate_summary()
        
        # Exit with appropriate code
        return 0 if not self.errors else 1

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='VayuGuard Deployment')
    parser.add_argument('--step', type=str, help='Run specific step')
    parser.add_argument('--skip-models', action='store_true', help='Skip model training')
    parser.add_argument('--skip-data', action='store_true', help='Skip data fetch')
    args = parser.parse_args()
    
    deployment = VayuGuardDeployment()
    
    if args.step:
        # Run single step
        if hasattr(deployment, args.step):
            getattr(deployment, args.step)()
            deployment.generate_summary()
        else:
            print(f"Unknown step: {args.step}")
            return 1
    else:
        # Run full deployment
        steps = [
            'install_dependencies',
            'create_directories',
            'train_models' if not args.skip_models else None,
            'fetch_real_data' if not args.skip_data else None,
            'verify_services',
            'generate_config'
        ]
        
        steps = [s for s in steps if s]  # Remove None values
        return deployment.deploy(steps)
