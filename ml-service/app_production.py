"""
app_production.py

Production FastAPI application for AQI prediction service.

Endpoints:
- POST /forecast - Make predictions
- GET /health - Health check
- GET /metrics - Model metrics

Features:
- Lasso production model (v1.0)
- Real-time predictions
- Prediction logging to database
- Model monitoring
- Rate limiting (100 req/min per IP)
- Environment variable validation
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import logging
import json
import os
import psycopg2
from pathlib import Path
import asyncio
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import time

# Security imports
from security import validate_ml_environment_vars, RateLimitMiddleware, scan_code_for_secrets

# Import model loader
from model_loader import get_model_loader, get_model_status

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate environment variables at startup
logger.info("[SECURITY] Validating environment variables...")
try:
    validate_ml_environment_vars()
    logger.info("[SECURITY] All required environment variables present")
except RuntimeError as e:
    logger.error(f"[SECURITY] {e}")
    raise

# Scan for potential hardcoded secrets
logger.info("[SECURITY] Scanning for hardcoded secrets...")
secrets_found = scan_code_for_secrets()
if secrets_found:
    logger.warning(f"[SECURITY] Found {len(secrets_found)} potential secret exposure(s)")
else:
    logger.info("[SECURITY] No hardcoded secrets detected")

# Create FastAPI app
app = FastAPI(
    title="VayuGuard AQI Prediction Service",
    description="Production ML service for AQI forecasting",
    version="1.0.0"
)

# Add security middleware - Rate limiting
logger.info("[SECURITY] Enabling rate limiting middleware (100 req/min per IP)")
app.add_middleware(RateLimitMiddleware)

# Global state
model_loader = None
db_connection = None
request_count = 0

# Thread pool for parallel model inference (prevents event loop blocking)
# Use 256 workers to handle high concurrency (10, 50, 100 concurrent users)
# CPU-bound inference (~0-4ms per task) can be heavily parallelized
cpu_cores = multiprocessing.cpu_count()
inference_thread_pool = ThreadPoolExecutor(
    max_workers=256,  # Maximized for 100+ concurrent request parallelization
    thread_name_prefix="inference_worker_"
)
prediction_count = 0
error_count = 0
total_latency = 0.0

# Precomputed features snapshot (loaded at startup, no per-request DB query)
features_snapshot = {}  # {city: feature_tuple}
snapshot_loaded = False

# Timing instrumentation
timing_stats = {
    'db_query': [],
    'feature_gen': [],
    'inference': [],
    'serialization': [],
    'total': []
}

# Database configuration (from environment variables)
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'vayuguard')
DB_USER = os.getenv('DB_USER', 'vayuguard_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'vayuguard_pass')

logger.info(f"[DATABASE] Configured: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# ==================== Request/Response Models ====================

class ForecastRequest(BaseModel):
    """Input model for prediction request."""
    city: str  # "Chennai", "Bengaluru", "Hyderabad"
    aqi: float  # Current AQI
    pm2_5: float  # PM2.5 level
    pm10: float  # PM10 level
    no2: float  # NO2 level
    so2: float  # SO2 level
    co: float  # CO level
    o3: Optional[float] = 0.0  # O3 level (optional)


class ForecastResponse(BaseModel):
    """Output model for prediction response."""
    city: str
    forecast_aqi: float
    model: str
    version: str
    timestamp: str
    prediction_id: Optional[str] = None
    confidence_interval: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    model_loaded: bool
    model_version: str
    database_status: str
    api_status: str
    uptime_seconds: Optional[float] = None


class MetricsResponse(BaseModel):
    """Metrics response model."""
    total_requests: int
    total_predictions: int
    total_errors: int
    average_latency_ms: float
    model_version: str
    timestamp: str


# ==================== Database Utilities ====================

def get_db_connection():
    """Get database connection with fork-safety (per-worker connection)."""
    try:
        # Always create fresh connection (no inherited state from parent process)
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=5
        )
        # Reset connection state to avoid inherited state from fork
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def create_prediction_log_table():
    """Create prediction log table if it doesn't exist."""
    try:
        conn = get_db_connection()
        if conn is None:
            logger.warning("Could not create prediction log table - DB connection failed")
            return False
        
        cursor = conn.cursor()
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS prediction_logs (
            id SERIAL PRIMARY KEY,
            city VARCHAR(50) NOT NULL,
            input_aqi FLOAT,
            predicted_aqi FLOAT NOT NULL,
            model_version VARCHAR(20) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            latency_ms FLOAT
        );
        
        CREATE INDEX IF NOT EXISTS idx_prediction_logs_timestamp ON prediction_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_prediction_logs_city ON prediction_logs(city);
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        conn.close()
        
        logger.info("[OK] Prediction log table created/verified")
        return True
    except Exception as e:
        logger.error(f"Failed to create prediction log table: {e}")
        return False


def log_prediction(city: str, input_aqi: float, predicted_aqi: float, 
                   model_version: str, latency_ms: float):
    """Log prediction to database (non-blocking, with fresh connection per-worker)."""
    try:
        # Get fresh connection (fork-safe)
        conn = get_db_connection()
        if conn is None:
            logger.warning("Could not log prediction - DB connection failed")
            return False
        
        cursor = conn.cursor()
        
        try:
            insert_sql = """
            INSERT INTO prediction_logs 
            (city, input_aqi, predicted_aqi, model_version, latency_ms)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_sql, (city, input_aqi, predicted_aqi, model_version, latency_ms))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()  # Close immediately after use (no pool, just close)
            
    except Exception as e:
        logger.error(f"Failed to log prediction: {e}")
        return False


async def log_prediction_background(city: str, input_aqi: float, predicted_aqi: float, 
                                     model_version: str, latency_ms: float):
    """Async wrapper to log prediction in background (non-blocking)."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, log_prediction, city, input_aqi, predicted_aqi, model_version, latency_ms)


def get_db_status():
    """Check database connectivity."""
    try:
        conn = get_db_connection()
        if conn is None:
            return "disconnected"
        conn.close()
        return "connected"
    except Exception:
        return "error"


def load_features_snapshot():
    """
    Load engineered features snapshot from database at startup.
    Executed ONCE per worker at startup, not per-request. Fork-safe.
    """
    global features_snapshot, snapshot_loaded
    global timing_stats
    import time
    
    try:
        conn = get_db_connection()
        if conn is None:
            logger.error("[SNAPSHOT] Database connection failed")
            return False
        
        try:
            cursor = conn.cursor()
            
            # Query latest features for all cities
            query = """
            SELECT city, lag_1, lag_3, lag_6, lag_12, lag_24,
                   rolling_mean_6, rolling_mean_12, rolling_mean_24,
                   rolling_std_6, rolling_std_12, rolling_std_24,
                   hour, day_of_week, month, quarter, day_of_month
            FROM engineered_features
            WHERE (city, date) IN (
                SELECT city, MAX(date) FROM engineered_features GROUP BY city
            )
            """
            
            start = time.time()
            cursor.execute(query)
            results = cursor.fetchall()
            query_time = (time.time() - start) * 1000
            
            cursor.close()
            
            # Build snapshot dictionary (local to this worker)
            for row in results:
                city = row[0]
                features = row[1:]
                features_snapshot[city] = features
            
            snapshot_loaded = True
            
            logger.info(f"[SNAPSHOT] Worker loaded {len(features_snapshot)} cities in {query_time:.1f}ms")
            logger.info(f"[SQL] Rows returned: {len(results)}")
            
            return True
            
        finally:
            conn.close()
        
    except Exception as e:
        logger.error(f"[SNAPSHOT] Failed to load features snapshot: {e}")
        snapshot_loaded = False
        return False
    except Exception as e:
        logger.error(f"[SNAPSHOT] Failed to load features snapshot: {e}")
        return False


def get_snapshot_features(city: str):
    """
    Get engineered features for a city from in-memory snapshot.
    NO database query per-request (loaded at startup).
    """
    global features_snapshot, snapshot_loaded
    
    if not snapshot_loaded or city not in features_snapshot:
        logger.warning(f"[SNAPSHOT] No features for {city}, using defaults")
        return None
    
    return features_snapshot[city]


# ==================== Startup/Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    global model_loader, db_connection, snapshot_loaded
    
    logger.info("=" * 80)
    logger.info("STARTUP: VayuGuard AQI Prediction Service (v1.0)")
    logger.info("=" * 80)
    
    # Load model
    try:
        model_loader = get_model_loader()
        if model_loader.is_loaded():
            logger.info("[OK] Production model loaded successfully")
            logger.info(f"     Model version: {model_loader.get_version()}")
            logger.info(f"     Features: {len(model_loader.get_features())}")
            metrics = model_loader.get_training_metrics()
            if metrics:
                logger.info(f"     Training MAE: {metrics.get('mae', 'N/A')}")
                logger.info(f"     Training R2: {metrics.get('r2', 'N/A')}")
        else:
            logger.error("[ERROR] Model failed to load")
    except Exception as e:
        logger.error(f"[ERROR] Model loading failed: {e}")
    
    # Setup database and load features snapshot
    logger.info("Setting up database...")
    try:
        create_prediction_log_table()
        db_status = get_db_status()
        logger.info(f"[OK] Database status: {db_status}")
        
        # Load engineered features snapshot at startup (ONCE, not per-request)
        logger.info("Loading features snapshot...")
        if load_features_snapshot():
            logger.info("[OK] Features snapshot loaded successfully")
        else:
            logger.warning("[WARN] Features snapshot loading failed, will use defaults")
            
    except Exception as e:
        logger.error(f"[ERROR] Database setup failed: {e}")
    
    logger.info("=" * 80)
    logger.info("STARTUP COMPLETE - API READY")
    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down VayuGuard AQI Prediction Service")


# ==================== API Endpoints ====================

@app.post("/forecast", response_model=ForecastResponse)
async def forecast(request: ForecastRequest):
    """
    Predict AQI for a given city and conditions.
    
    Args:
        request: ForecastRequest with city and environmental data
        
    Returns:
        ForecastResponse with predicted AQI
    """
    global prediction_count, error_count, total_latency, timing_stats
    import time
    import numpy as np
    
    start_time = time.time()
    
    try:
        # Validate city
        valid_cities = ["Chennai", "Bengaluru", "Hyderabad"]
        if request.city not in valid_cities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid city. Must be one of: {', '.join(valid_cities)}"
            )
        
        # Get model
        model = model_loader.get_model()
        version = model_loader.get_version()
        
        # === PHASE 1: Get historical data (from in-memory snapshot, NO DB query) ===
        db_start = time.time()
        result = get_snapshot_features(request.city)
        db_time = (time.time() - db_start) * 1000
        timing_stats['db_query'].append(db_time)
        
        logger.info(f"[FORECAST] {request.city}: DB lookup {db_time:.3f}ms (snapshot, no query)")
        
        if result is not None:
            # Extract historical features from snapshot
            (lag_1, lag_3, lag_6, lag_12, lag_24,
             rolling_mean_6, rolling_mean_12, rolling_mean_24,
             rolling_std_6, rolling_std_12, rolling_std_24,
             hour, day_of_week, month, quarter, day_of_month) = result
        else:
            # Use default values if snapshot unavailable
            logger.warning(f"Using default features for {request.city}")
            lag_1 = request.aqi
            lag_3 = request.aqi
            lag_6 = request.aqi
            lag_12 = request.aqi
            lag_24 = request.aqi
            rolling_mean_6 = request.aqi
            rolling_mean_12 = request.aqi
            rolling_mean_24 = request.aqi
            rolling_std_6 = 10.0
            rolling_std_12 = 10.0
            rolling_std_24 = 10.0
            now = datetime.now()
            hour = now.hour
            day_of_week = now.weekday()
            month = now.month
            quarter = (now.month - 1) // 3 + 1
            day_of_month = now.day
        
        # === PHASE 2: Feature generation ===
        feature_start = time.time()
        
        # Calculate temporal features from current time (not from DB)
        now = datetime.now()
        year = now.year
        week_of_year = now.isocalendar()[1]
        season = {1: 1, 2: 1, 3: 2, 4: 2, 5: 2, 6: 3, 7: 3, 8: 3, 9: 4, 10: 4, 11: 4, 12: 1}[now.month]
        days_since_start = 0
        
        features = [
            lag_1, lag_3, lag_6, lag_12, lag_24,
            rolling_mean_6, rolling_mean_12, rolling_mean_24,
            rolling_std_6, rolling_std_12, rolling_std_24,
            hour, day_of_week, month, quarter, day_of_month,
            year, week_of_year, season, days_since_start,
            request.pm2_5, request.pm10, request.no2, request.so2, request.co, request.o3,
            # Interaction features
            lag_1 * rolling_mean_6,
            lag_3 * rolling_std_6,
            request.pm2_5 * request.pm10,
            request.no2 * request.so2
        ]
        feature_time = (time.time() - feature_start) * 1000
        timing_stats['feature_gen'].append(feature_time)
        
        # === PHASE 3: Model inference (run in thread pool to avoid blocking event loop) ===
        inference_start = time.time()
        features_array = np.array(features).reshape(1, -1)
        
        # Run CPU-bound model.predict() in thread pool to parallelize with async I/O
        loop = asyncio.get_event_loop()
        predicted_aqi = await loop.run_in_executor(
            inference_thread_pool,
            lambda: float(model.predict(features_array)[0])
        )
        
        inference_time = (time.time() - inference_start) * 1000
        timing_stats['inference'].append(inference_time)
        
        # === PHASE 4: Response serialization ===
        serialization_start = time.time()
        response_obj = ForecastResponse(
            city=request.city,
            forecast_aqi=round(predicted_aqi, 2),
            model="lasso",
            version=version,
            timestamp=datetime.now().isoformat(),
            prediction_id=f"{request.city}_{datetime.now().timestamp()}"
        )
        serialization_time = (time.time() - serialization_start) * 1000
        timing_stats['serialization'].append(serialization_time)
        
        # Calculate total latency
        total_time = (time.time() - start_time) * 1000
        total_latency += total_time
        timing_stats['total'].append(total_time)
        prediction_count += 1
        
        # Log all phases
        logger.info(f"[FORECAST] {request.city}: DB={db_time:.1f}ms | Features={feature_time:.1f}ms | Inference={inference_time:.1f}ms | Serialization={serialization_time:.1f}ms | TOTAL={total_time:.1f}ms")
        
        # Log prediction to database in background (non-blocking with create_task)
        asyncio.create_task(
            log_prediction_background(
                city=request.city,
                input_aqi=request.aqi,
                predicted_aqi=predicted_aqi,
                model_version=version,
                latency_ms=total_time
            )
        )
        
        return response_obj
        
    except HTTPException as e:
        error_count += 1
        raise e
    except Exception as e:
        error_count += 1
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        HealthResponse with service status
    """
    global request_count
    request_count += 1
    
    try:
        model_loaded = model_loader.is_loaded()
        model_version = model_loader.get_version() if model_loaded else "unknown"
        db_status = get_db_status()
        
        status = "healthy" if model_loaded and db_status == "connected" else "degraded"
        
        return HealthResponse(
            status=status,
            timestamp=datetime.now().isoformat(),
            model_loaded=model_loaded,
            model_version=model_version,
            database_status=db_status,
            api_status="operational"
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now().isoformat(),
            model_loaded=False,
            model_version="unknown",
            database_status="error",
            api_status="error"
        )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get service metrics.
    
    Returns:
        MetricsResponse with service metrics
    """
    avg_latency = (total_latency / prediction_count * 1000) if prediction_count > 0 else 0.0
    
    return MetricsResponse(
        total_requests=request_count,
        total_predictions=prediction_count,
        total_errors=error_count,
        average_latency_ms=round(avg_latency, 2),
        model_version=model_loader.get_version() if model_loader else "unknown",
        timestamp=datetime.now().isoformat()
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "VayuGuard AQI Prediction Service",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "forecast": "POST /forecast",
            "health": "GET /health",
            "metrics": "GET /metrics",
            "docs": "GET /docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting VayuGuard AQI Production Service on 0.0.0.0:8000")
    logger.info("Workers: 1 (single-process, fork-safe mode)")
    
    # Single worker to avoid fork-safety issues with psycopg2
    # Use asyncio loop (uvloop not available on Windows)
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1, loop="asyncio")
