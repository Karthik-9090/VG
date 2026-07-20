#!/usr/bin/env python3
"""
Production FastAPI Application for VayuGuard AQI Predictions
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import pickle
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
import numpy as np
import logging

# ==================== LOGGING ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "vayuguard"
DB_USER = "postgres"
DB_PASSWORD = ""

WORKSPACE_ROOT = str(Path(__file__).parent.parent)
MODEL_PATH = os.path.join(WORKSPACE_ROOT, "models", "production_lasso.pkl")
METADATA_PATH = os.path.join(WORKSPACE_ROOT, "production_metrics.json")

# ==================== MODELS ====================
class ForecastRequest(BaseModel):
    city: str
    aqi: float
    pm2_5: float
    pm10: float
    no2: float
    so2: float
    co: float
    o3: Optional[float] = 0.0

class ForecastResponse(BaseModel):
    city: str
    forecast_aqi: float
    model: str
    version: str
    timestamp: str
    prediction_id: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str
    database_status: str

# ==================== GLOBAL STATE ====================
app = FastAPI(title="VayuGuard AQI Service", version="1.0.0")

model = None
metadata = None
model_loaded = False

requests_count = 0
predictions_count = 0
errors_count = 0

# ==================== UTILITIES ====================
def load_model():
    """Load production model."""
    global model, metadata, model_loaded
    try:
        logger.info(f"Loading model from {MODEL_PATH}")
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        
        with open(METADATA_PATH, 'r') as f:
            metadata = json.load(f)
        
        model_loaded = True
        logger.info("[OK] Model loaded successfully")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Failed to load model: {e}")
        model_loaded = False
        return False

def get_db_connection():
    """Get database connection."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, database=DB_NAME,
            user=DB_USER, password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def create_logs_table():
    """Create prediction logs table."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_logs (
                id SERIAL PRIMARY KEY,
                city VARCHAR(50),
                input_aqi FLOAT,
                predicted_aqi FLOAT,
                model_version VARCHAR(20),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                latency_ms FLOAT
            )
        """)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Failed to create logs table: {e}")
        return False

def log_prediction(city, input_aqi, predicted_aqi, version, latency_ms):
    """Log prediction to database."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO prediction_logs (city, input_aqi, predicted_aqi, model_version, latency_ms)
            VALUES (%s, %s, %s, %s, %s)
        """, (city, input_aqi, predicted_aqi, version, latency_ms))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Failed to log prediction: {e}")
        return False

def get_db_status():
    """Check database connectivity."""
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            return "connected"
        return "disconnected"
    except:
        return "error"

# ==================== STARTUP ====================
@app.on_event("startup")
async def startup():
    """Initialize on startup."""
    logger.info("=" * 80)
    logger.info("STARTUP: VayuGuard AQI Service v1.0")
    logger.info("=" * 80)
    
    # Load model
    load_model()
    
    # Setup database
    create_logs_table()
    
    logger.info("Startup complete")

# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint."""
    global requests_count
    requests_count += 1
    return {
        "service": "VayuGuard AQI Prediction",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    global requests_count
    requests_count += 1
    
    return HealthResponse(
        status="healthy" if model_loaded else "unhealthy",
        model_loaded=model_loaded,
        model_version=metadata.get("model_version", "unknown") if metadata else "unknown",
        database_status=get_db_status()
    )

@app.post("/forecast", response_model=ForecastResponse)
async def forecast(request: ForecastRequest):
    """Predict AQI."""
    global requests_count, predictions_count, errors_count
    requests_count += 1
    
    start = time.time()
    
    try:
        # Validate city
        valid_cities = ["Chennai", "Bengaluru", "Hyderabad"]
        if request.city not in valid_cities:
            raise HTTPException(status_code=400, detail="Invalid city")
        
        if not model_loaded:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        # Get historical data
        try:
            conn = get_db_connection()
            if not conn:
                raise Exception("DB connection failed")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT lag_1, lag_3, lag_6, lag_12, lag_24,
                       rolling_mean_6, rolling_mean_12, rolling_mean_24,
                       rolling_std_6, rolling_std_12, rolling_std_24,
                       hour, day_of_week, month, quarter, day_of_month,
                       year, week_of_year, season, days_since_start
                FROM engineered_features
                WHERE city = %s
                ORDER BY date DESC LIMIT 1
            """, (request.city,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                (lag_1, lag_3, lag_6, lag_12, lag_24,
                 rolling_mean_6, rolling_mean_12, rolling_mean_24,
                 rolling_std_6, rolling_std_12, rolling_std_24,
                 hour, day_of_week, month, quarter, day_of_month,
                 year, week_of_year, season, days_since_start) = result
            else:
                # Use defaults if no historical data
                lag_1 = lag_3 = lag_6 = lag_12 = lag_24 = request.aqi
                rolling_mean_6 = rolling_mean_12 = rolling_mean_24 = request.aqi
                rolling_std_6 = rolling_std_12 = rolling_std_24 = 10.0
                now = datetime.now()
                hour = now.hour
                day_of_week = now.weekday()
                month = now.month
                quarter = (now.month - 1) // 3 + 1
                day_of_month = now.day
                year = now.year
                week_of_year = now.isocalendar()[1]
                season = [1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 1][month - 1]
                days_since_start = 0
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            # Use defaults
            lag_1 = lag_3 = lag_6 = lag_12 = lag_24 = request.aqi
            rolling_mean_6 = rolling_mean_12 = rolling_mean_24 = request.aqi
            rolling_std_6 = rolling_std_12 = rolling_std_24 = 10.0
            now = datetime.now()
            hour = now.hour
            day_of_week = now.weekday()
            month = now.month
            quarter = (now.month - 1) // 3 + 1
            day_of_month = now.day
            year = now.year
            week_of_year = now.isocalendar()[1]
            season = [1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 1][month - 1]
            days_since_start = 0
        
        # Create feature vector (30 features)
        features = [
            lag_1, lag_3, lag_6, lag_12, lag_24,
            rolling_mean_6, rolling_mean_12, rolling_mean_24,
            rolling_std_6, rolling_std_12, rolling_std_24,
            hour, day_of_week, month, quarter, day_of_month,
            year, week_of_year, season, days_since_start,
            request.pm2_5, request.pm10, request.no2, request.so2, request.co, request.o3,
            lag_1 * rolling_mean_6,
            lag_3 * rolling_std_6,
            request.pm2_5 * request.pm10,
            request.no2 * request.so2
        ]
        
        # Predict
        features_array = np.array(features).reshape(1, -1)
        predicted_aqi = float(model.predict(features_array)[0])
        
        latency_ms = (time.time() - start) * 1000
        predictions_count += 1
        
        # Log prediction
        log_prediction(request.city, request.aqi, predicted_aqi, 
                      metadata.get("model_version", "v1.0") if metadata else "v1.0", latency_ms)
        
        logger.info(f"[OK] Prediction: {request.city} -> {predicted_aqi:.2f} ({latency_ms:.1f}ms)")
        
        return ForecastResponse(
            city=request.city,
            forecast_aqi=round(predicted_aqi, 2),
            model="lasso",
            version=metadata.get("model_version", "v1.0") if metadata else "v1.0",
            timestamp=datetime.now().isoformat(),
            prediction_id=f"{request.city}_{datetime.now().timestamp()}"
        )
    
    except HTTPException:
        errors_count += 1
        raise
    except Exception as e:
        errors_count += 1
        logger.error(f"[ERROR] Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
