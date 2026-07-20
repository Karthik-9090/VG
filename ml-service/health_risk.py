"""
Health risk scoring module for VayuGuard.
Implements 5 health profiles with 5 risk levels each.
"""

import config
from typing import Dict, List, Optional


def get_risk_level(aqi: int, profile: str) -> Dict[str, any]:
    """
    Calculate health risk level based on AQI and user health profile.
    
    Args:
        aqi: Air Quality Index value (0-500+)
        profile: Health profile type (general, respiratory, cardiac, children, elderly)
    
    Returns:
        Dict with risk_level, advisory, and precautions
    """
    
    if profile not in config.HEALTH_RISK_PROFILES:
        return {
            'error': 'Invalid profile',
            'valid_profiles': list(config.HEALTH_RISK_PROFILES.keys())
        }
    
    profile_config = config.HEALTH_RISK_PROFILES[profile]
    thresholds = profile_config['thresholds']
    risk_levels = profile_config['risk_levels']
    
    # Determine risk level based on thresholds
    if aqi <= thresholds['good']:
        risk_index = 0
    elif aqi <= thresholds['moderate']:
        risk_index = 1
    elif aqi <= thresholds['unhealthy']:
        risk_index = 2
    elif aqi <= thresholds['severe']:
        risk_index = 3
    else:
        risk_index = 4
    
    risk_level = risk_levels[risk_index]
    
    # Generate advisories based on profile and risk level
    advisories = _get_advisories(profile, risk_index)
    precautions = _get_precautions(profile, risk_index)
    
    return {
        'aqi': aqi,
        'profile': profile,
        'risk_level': risk_level,
        'risk_index': risk_index,
        'advisory': advisories['advisory'],
        'detailed_advisory': advisories['detailed'],
        'precautions': precautions,
        'thresholds': thresholds
    }


def _get_advisories(profile: str, risk_index: int) -> Dict[str, str]:
    """Generate advisories based on profile and risk level."""
    
    advisories = {
        'general': [
            'Air quality is good. Enjoy outdoor activities!',
            'Air quality is acceptable. You can engage in outdoor activities normally.',
            'Sensitive groups should avoid prolonged outdoor activity.',
            'Everyone should avoid outdoor activities. Use N95 masks if you must go out.',
            'Do not go outside. Use air purifiers indoors. Seek medical help if needed.'
        ],
        'respiratory': [
            'Air quality is good for your respiratory health. Safe for outdoor activities.',
            'Air quality is acceptable. You may experience minor symptoms. Limit intense outdoor activities.',
            'Your respiratory system is at risk. Consider limiting outdoor activities and use inhalers if prescribed.',
            'Serious respiratory effects likely. Stay indoors and use air purifiers. Have rescue medication available.',
            'Emergency respiratory hazard. Do not go outside. Have emergency contact ready and monitor symptoms closely.'
        ],
        'cardiac': [
            'Air quality poses no cardiac risk. Safe for outdoor activities.',
            'Air quality is acceptable. Minor cardiac stress possible. Monitor your symptoms.',
            'Cardiac stress possible. Limit strenuous activities and avoid intense exercise.',
            'High cardiac risk. Avoid physical exertion and stay indoors if possible.',
            'Emergency cardiac hazard. Stay indoors immediately. Have medical help ready and consult your cardiologist.'
        ],
        'children': [
            'Air quality is safe for children. Normal outdoor play is fine.',
            'Air quality is acceptable. Children can play outdoors with normal precautions.',
            'Children may experience minor symptoms. Reduce outdoor playtime.',
            'Keep children indoors. Air quality is unhealthy for their sensitive lungs.',
            'Emergency: Children must stay indoors. Seek medical attention if any symptoms appear.'
        ],
        'elderly': [
            'Air quality is safe for elderly individuals. Normal outdoor activity is fine.',
            'Air quality is acceptable. Elderly individuals may engage in light outdoor activities.',
            'Elderly individuals should limit outdoor activities and take precautions.',
            'Elderly should remain indoors. High health risk. Limit movement.',
            'Emergency: Elderly must stay indoors. Serious health risk. Have medical help ready.'
        ]
    }
    
    profile_advisories = advisories.get(profile, advisories['general'])
    
    return {
        'advisory': profile_advisories[risk_index],
        'detailed': f"Health risk level for {profile} profile: {['None', 'Low', 'Moderate', 'High', 'Severe'][risk_index]}"
    }


def _get_precautions(profile: str, risk_index: int) -> List[str]:
    """Generate precautions based on profile and risk level."""
    
    precautions_map = {
        0: [],  # None
        1: ['Check local air quality forecasts', 'Consider indoor activities'],
        2: ['Use N95 masks if outdoors', 'Limit strenuous activities', 'Use air purifiers'],
        3: ['Remain indoors', 'Keep windows and doors closed', 'Use HEPA air filters', 'Consult doctor if symptoms develop'],
        4: ['Emergency situation', 'Seek immediate medical attention if symptoms worsen', 'Stay in designated safe areas']
    }
    
    base_precautions = precautions_map.get(risk_index, [])
    
    # Add profile-specific precautions
    if profile == 'respiratory':
        if risk_index >= 2:
            base_precautions.extend(['Use prescribed inhalers', 'Have rescue medication available'])
    elif profile == 'cardiac':
        if risk_index >= 2:
            base_precautions.extend(['Avoid strenuous exercise', 'Take heart medication as prescribed'])
    elif profile == 'children':
        if risk_index >= 1:
            base_precautions.extend(['Supervise outdoor activities', 'Encourage indoor play'])
    elif profile == 'elderly':
        if risk_index >= 1:
            base_precautions.extend(['Take regular rest breaks', 'Have medications nearby'])
    
    return base_precautions


def get_all_profiles_risk(aqi: int) -> Dict[str, Dict]:
    """Get risk levels for all health profiles at given AQI."""
    return {
        profile: get_risk_level(aqi, profile)
        for profile in config.HEALTH_RISK_PROFILES.keys()
    }
