from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import numpy as np
from typing import List, Dict, Optional
import config
import health_risk
import utils

app = FastAPI(title="VayuGuard ML Service", version="1.0.0")

# Prometheus metrics
request_count = Counter('vayuguard_ml_requests_total', 'Total ML service requests', ['endpoint'])
forecast_duration = Histogram('vayuguard_forecast_duration_seconds', 'Forecast generation duration')


class CurrentAQIRequest(BaseModel):
    city: str = 'Chennai'


class CurrentAQIResponse(BaseModel):
    city: str
    aqi: int
    category: str
    timestamp: str


class ForecastRequest(BaseModel):
    city: str = 'Chennai'
    horizon: int = Field(default=24, ge=1, le=72)


class ForecastResponse(BaseModel):
    city: str
    horizon: int
    forecast_values: List[int]
    model_used: str
    confidence: float


class HealthRiskRequest(BaseModel):
    aqi: int = Field(ge=0)
    profile: str = 'general'


class HealthRiskResponse(BaseModel):
    aqi: int
    profile: str
    risk_level: str
    risk_index: int
    advisory: str
    precautions: List[str]


@app.get('/health')
def health_check():
    """Health check endpoint."""
    request_count.labels(endpoint='health').inc()
    return {'status': 'ok', 'service': 'ml-service'}


@app.get('/current-aqi', response_model=CurrentAQIResponse)
def get_current_aqi(city: str = 'Chennai'):
    """Get current AQI for a city."""
    request_count.labels(endpoint='current-aqi').inc()
    
    # Simulate AQI reading (in production, would fetch from database/API)
    aqi_values = {
        'Chennai': 65,
        'Bengaluru': 58,
        'Hyderabad': 72
    }
    
    aqi = aqi_values.get(city, 60)
    
    # Categorize AQI
    if aqi <= 50:
        category = 'Good'
    elif aqi <= 100:
        category = 'Satisfactory'
    elif aqi <= 150:
        category = 'Moderately Polluted'
    elif aqi <= 200:
        category = 'Heavily Polluted'
    else:
        category = 'Severely Polluted'
    
    from datetime import datetime
    return CurrentAQIResponse(
        city=city,
        aqi=aqi,
        category=category,
        timestamp=datetime.now().isoformat()
    )


@app.post('/forecast', response_model=ForecastResponse)
def generate_forecast(request: ForecastRequest):
    """Generate AQI forecast for specified horizon."""
    request_count.labels(endpoint='forecast').inc()
    
    with forecast_duration.time():
        city = request.city
        horizon = request.horizon
        
        # Validate horizon
        if horizon < 1 or horizon > 72:
            raise HTTPException(status_code=422, detail='Horizon must be between 1 and 72 hours')
        
        # Simulate forecast generation
        # In production, would use trained models
        base_aqi = {
            'Chennai': 65,
            'Bengaluru': 58,
            'Hyderabad': 72
        }.get(city, 60)
        
        # Generate forecast values with slight variation
        np.random.seed(42)
        forecast_values = []
        current_aqi = base_aqi
        for h in range(horizon):
            # Add seasonal and random variation
            change = np.random.normal(0, 5)
            # Add slight trend
            trend = -0.5 if h % 12 < 6 else 0.5
            current_aqi = max(0, current_aqi + change + trend)
            forecast_values.append(int(current_aqi))
        
        return ForecastResponse(
            city=city,
            horizon=horizon,
            forecast_values=forecast_values,
            model_used='ensemble',
            confidence=0.87
        )


@app.post('/health-risk', response_model=HealthRiskResponse)
def calculate_health_risk(request: HealthRiskRequest):
    """Calculate health risk for given AQI and profile."""
    request_count.labels(endpoint='health-risk').inc()
    
    aqi = request.aqi
    profile = request.profile
    
    # Validate profile
    valid_profiles = list(config.HEALTH_RISK_PROFILES.keys())
    if profile not in valid_profiles:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid profile. Valid profiles: {valid_profiles}"
        )
    
    result = health_risk.get_risk_level(aqi, profile)
    
    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return HealthRiskResponse(
        aqi=result['aqi'],
        profile=result['profile'],
        risk_level=result['risk_level'],
        risk_index=result['risk_index'],
        advisory=result['advisory'],
        precautions=result['precautions']
    )


@app.post('/health-risk-all')
def calculate_all_health_risks(aqi: int):
    """Calculate health risk for all profiles at given AQI."""
    request_count.labels(endpoint='health-risk-all').inc()
    
    result = health_risk.get_all_profiles_risk(aqi)
    return result


@app.get('/metrics')
def metrics_endpoint():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8001)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8001)
