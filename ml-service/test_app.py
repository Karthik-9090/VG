"""Tests for ML service endpoints."""

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_current_aqi_default():
    """Test current AQI with default city."""
    response = client.get('/current-aqi')
    assert response.status_code == 200
    data = response.json()
    assert 'aqi' in data
    assert data['city'] == 'Chennai'
    assert data['category'] in ['Good', 'Satisfactory', 'Moderately Polluted', 'Heavily Polluted', 'Severely Polluted']


def test_current_aqi_different_city():
    """Test current AQI with different city."""
    response = client.get('/current-aqi?city=Bengaluru')
    assert response.status_code == 200
    data = response.json()
    assert data['city'] == 'Bengaluru'
    assert 'aqi' in data


def test_forecast_default():
    """Test forecast with default parameters."""
    response = client.post('/forecast', json={'city': 'Chennai'})
    assert response.status_code == 200
    data = response.json()
    assert data['city'] == 'Chennai'
    assert data['horizon'] == 24
    assert len(data['forecast_values']) == 24
    assert 'model_used' in data


def test_forecast_24h():
    """Test 24-hour forecast."""
    response = client.post('/forecast', json={'city': 'Chennai', 'horizon': 24})
    assert response.status_code == 200
    data = response.json()
    assert len(data['forecast_values']) == 24


def test_forecast_48h():
    """Test 48-hour forecast."""
    response = client.post('/forecast', json={'city': 'Chennai', 'horizon': 48})
    assert response.status_code == 200
    data = response.json()
    assert len(data['forecast_values']) == 48


def test_forecast_72h():
    """Test 72-hour forecast."""
    response = client.post('/forecast', json={'city': 'Chennai', 'horizon': 72})
    assert response.status_code == 200
    data = response.json()
    assert len(data['forecast_values']) == 72


def test_forecast_invalid_horizon():
    """Test forecast with invalid horizon."""
    response = client.post('/forecast', json={'city': 'Chennai', 'horizon': 100})
    assert response.status_code == 422


def test_health_risk_general():
    """Test health risk for general profile."""
    response = client.post('/health-risk', json={'aqi': 50, 'profile': 'general'})
    assert response.status_code == 200
    data = response.json()
    assert data['profile'] == 'general'
    assert data['aqi'] == 50
    assert 'risk_level' in data
    assert 'advisory' in data


def test_health_risk_respiratory():
    """Test health risk for respiratory profile."""
    response = client.post('/health-risk', json={'aqi': 75, 'profile': 'respiratory'})
    assert response.status_code == 200
    data = response.json()
    assert data['profile'] == 'respiratory'
    assert 'precautions' in data


def test_health_risk_cardiac():
    """Test health risk for cardiac profile."""
    response = client.post('/health-risk', json={'aqi': 100, 'profile': 'cardiac'})
    assert response.status_code == 200
    data = response.json()
    assert data['profile'] == 'cardiac'


def test_health_risk_children():
    """Test health risk for children profile."""
    response = client.post('/health-risk', json={'aqi': 50, 'profile': 'children'})
    assert response.status_code == 200
    data = response.json()
    assert data['profile'] == 'children'


def test_health_risk_elderly():
    """Test health risk for elderly profile."""
    response = client.post('/health-risk', json={'aqi': 60, 'profile': 'elderly'})
    assert response.status_code == 200
    data = response.json()
    assert data['profile'] == 'elderly'


def test_health_risk_invalid_profile():
    """Test health risk with invalid profile."""
    response = client.post('/health-risk', json={'aqi': 50, 'profile': 'invalid_profile'})
    assert response.status_code == 422


def test_health_risk_all_profiles():
    """Test health risk for all profiles."""
    response = client.post('/health-risk-all?aqi=50')
    assert response.status_code == 200
    data = response.json()
    assert 'general' in data
    assert 'respiratory' in data
    assert 'cardiac' in data
    assert 'children' in data
    assert 'elderly' in data


def test_metrics_endpoint():
    """Test Prometheus metrics endpoint."""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert 'vayuguard_ml_requests_total' in response.text
