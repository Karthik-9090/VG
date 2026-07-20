"""
Feature engineering utilities for AQI forecasting.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple


def engineer_features(aqi_history: List[int], weather_data: Dict) -> np.ndarray:
    """
    Engineer features for AQI forecasting models.
    
    Features include:
    - Lag features (previous values)
    - Rolling statistics (mean, std)
    - Temporal features (hour, day, month)
    - Weather features (temperature, humidity, wind speed)
    
    Args:
        aqi_history: List of recent AQI values (at least 24 hours)
        weather_data: Dict with temperature, humidity, wind_speed
    
    Returns:
        Feature array suitable for model input
    """
    
    features = []
    
    # Lag features (last 24 hours)
    if len(aqi_history) >= 24:
        features.extend(aqi_history[-24:])
    else:
        # Pad with zeros if insufficient history
        features.extend([0] * (24 - len(aqi_history)) + aqi_history)
    
    # Rolling statistics
    aqi_array = np.array(aqi_history[-24:] if len(aqi_history) >= 24 else aqi_history)
    features.append(np.mean(aqi_array))  # 24h mean
    features.append(np.std(aqi_array))   # 24h std
    
    if len(aqi_history) >= 7*24:
        aqi_7d = np.array(aqi_history[-7*24:])
        features.append(np.mean(aqi_7d))  # 7d mean
        features.append(np.std(aqi_7d))   # 7d std
    else:
        features.extend([0, 0])  # Placeholder
    
    # Weather features
    features.append(weather_data.get('temperature', 0))
    features.append(weather_data.get('humidity', 0))
    features.append(weather_data.get('wind_speed', 0))
    
    # Temporal features (hour, day, month - dummy values for now)
    from datetime import datetime
    now = datetime.now()
    features.append(now.hour)
    features.append(now.day)
    features.append(now.month)
    
    return np.array(features, dtype=np.float32).reshape(1, -1)


def prepare_training_data(aqi_data: List[Dict], horizon: int = 24) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare training data for model fitting.
    
    Args:
        aqi_data: List of dicts with 'aqi', 'temperature', 'humidity', 'wind_speed'
        horizon: Forecast horizon in hours
    
    Returns:
        X (features), y (targets)
    """
    
    X_list = []
    y_list = []
    
    aqi_values = [d['aqi'] for d in aqi_data]
    
    # Create sliding windows
    window_size = 24 + horizon
    for i in range(len(aqi_values) - window_size):
        history = aqi_values[i:i+24]
        target = aqi_values[i+24+horizon-1]  # Target at horizon
        
        weather = aqi_data[i+24] if i+24 < len(aqi_data) else aqi_data[-1]
        weather_dict = {
            'temperature': weather.get('temperature', 20),
            'humidity': weather.get('humidity', 50),
            'wind_speed': weather.get('wind_speed', 5)
        }
        
        features = engineer_features(history, weather_dict)
        X_list.append(features[0])
        y_list.append(target)
    
    return np.array(X_list), np.array(y_list)


def normalize_features(X: np.ndarray, mean: np.ndarray = None, std: np.ndarray = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Normalize features using z-score normalization.
    
    Returns:
        Normalized X, mean, std
    """
    if mean is None:
        mean = np.mean(X, axis=0)
    if std is None:
        std = np.std(X, axis=0)
    
    # Avoid division by zero
    std = np.where(std == 0, 1, std)
    
    X_normalized = (X - mean) / std
    return X_normalized, mean, std


def inverse_normalize(y_norm: np.ndarray, mean: float, std: float) -> np.ndarray:
    """Inverse normalization for target values."""
    return y_norm * std + mean
