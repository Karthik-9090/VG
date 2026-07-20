const AQI_HEALTH_RULES = [
  {
    max: 50,
    category: 'Good',
    health_risk: 'Minimal',
    sensitive_groups: ['None'],
    outdoor_activity: 'All activities are safe',
    mask_required: false,
    ventilation: 'Normal indoor ventilation is sufficient',
    emergency_warning: 'None',
    recommendations: [
      'Air quality is satisfactory.',
      'Enjoy your normal outdoor activities.'
    ]
  },
  {
    max: 100,
    category: 'Satisfactory',
    health_risk: 'Acceptable',
    sensitive_groups: ['People with respiratory conditions'],
    outdoor_activity: 'Outdoor activities are generally safe',
    mask_required: false,
    ventilation: 'Maintain normal indoor ventilation',
    emergency_warning: 'None',
    recommendations: [
      'Air quality is acceptable for most people.',
      'People with respiratory conditions should pay attention to symptoms.'
    ]
  },
  {
    max: 200,
    category: 'Moderately Polluted',
    health_risk: 'Increased',
    sensitive_groups: ['Children', 'Elderly', 'People with respiratory or cardiac conditions'],
    outdoor_activity: 'Reduce prolonged outdoor exertion',
    mask_required: true,
    ventilation: 'Use filtered indoor ventilation if available',
    emergency_warning: 'Consider limiting outdoor exposure',
    recommendations: [
      'Sensitive groups should reduce prolonged outdoor exertion.',
      'Wear a mask during prolonged outdoor activities.'
    ]
  },
  {
    max: 300,
    category: 'Poor',
    health_risk: 'High',
    sensitive_groups: ['Children', 'Elderly', 'People with respiratory or cardiac conditions'],
    outdoor_activity: 'Avoid outdoor exertion',
    mask_required: true,
    ventilation: 'Keep windows closed if outdoor air is poor',
    emergency_warning: 'People with health issues should stay indoors',
    recommendations: [
      'Avoid outdoor exertion and strenuous activities.',
      'Use a high-quality mask when outdoors.'
    ]
  },
  {
    max: 400,
    category: 'Very Poor',
    health_risk: 'Very High',
    sensitive_groups: ['Children', 'Elderly', 'People with respiratory or cardiac conditions'],
    outdoor_activity: 'Stay indoors as much as possible',
    mask_required: true,
    ventilation: 'Use indoor air purifiers and keep windows closed',
    emergency_warning: 'Health alert: everyone may experience more serious effects',
    recommendations: [
      'Stay indoors and avoid any outdoor activity.',
      'Use an N95 or equivalent mask if you must go outside.'
    ]
  },
  {
    max: 500,
    category: 'Severe',
    health_risk: 'Extreme',
    sensitive_groups: ['Everyone'],
    outdoor_activity: 'Do not go outside unless absolutely necessary',
    mask_required: true,
    ventilation: 'Use sealed indoor environments with air filtration',
    emergency_warning: 'Serious emergency: everyone may experience severe health effects',
    recommendations: [
      'Avoid outdoor activity entirely.',
      'Keep doors and windows closed and use air filtration.'
    ]
  }
];

function getAdviceForAqi(aqi) {
  const rule = AQI_HEALTH_RULES.find(rule => aqi <= rule.max) || AQI_HEALTH_RULES[AQI_HEALTH_RULES.length - 1];
  return {
    category: rule.category,
    health_risk: rule.health_risk,
    sensitive_groups: rule.sensitive_groups,
    outdoor_activity: rule.outdoor_activity,
    mask_required: rule.mask_required,
    ventilation: rule.ventilation,
    emergency_warning: rule.emergency_warning,
    recommendations: rule.recommendations
  };
}

function getCategoryForAqi(aqi) {
  const rule = AQI_HEALTH_RULES.find(rule => aqi <= rule.max) || AQI_HEALTH_RULES[AQI_HEALTH_RULES.length - 1];
  return rule.category;
}

module.exports = {
  AQI_HEALTH_RULES,
  getAdviceForAqi,
  getCategoryForAqi
};
