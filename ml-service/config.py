import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'vayuguard')
DB_USER = os.getenv('DB_USER', 'vayuguard_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'vayuguard_pass')

MODEL_BASELINE = os.getenv('MODEL_BASELINE', './models/baseline.pkl')
MODEL_LR = os.getenv('MODEL_LR', './models/lr.pkl')
MODEL_RF = os.getenv('MODEL_RF', './models/rf.pkl')
MODEL_XGBOOST = os.getenv('MODEL_XGBOOST', './models/xgboost.pkl')
MODEL_LSTM = os.getenv('MODEL_LSTM', './models/lstm.h5')

HEALTH_RISK_PROFILES = {
    'general': {
        'thresholds': {'good': 50, 'moderate': 100, 'unhealthy': 150, 'severe': 200},
        'risk_levels': ['None', 'Low', 'Moderate', 'High', 'Severe']
    },
    'respiratory': {
        'thresholds': {'good': 30, 'moderate': 80, 'unhealthy': 120, 'severe': 160},
        'risk_levels': ['None', 'Low', 'Moderate', 'High', 'Severe']
    },
    'cardiac': {
        'thresholds': {'good': 40, 'moderate': 90, 'unhealthy': 140, 'severe': 180},
        'risk_levels': ['None', 'Low', 'Moderate', 'High', 'Severe']
    },
    'children': {
        'thresholds': {'good': 25, 'moderate': 75, 'unhealthy': 115, 'severe': 155},
        'risk_levels': ['None', 'Low', 'Moderate', 'High', 'Severe']
    },
    'elderly': {
        'thresholds': {'good': 35, 'moderate': 85, 'unhealthy': 130, 'severe': 170},
        'risk_levels': ['None', 'Low', 'Moderate', 'High', 'Severe']
    }
}
