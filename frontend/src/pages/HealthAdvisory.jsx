import React, { useState, useEffect } from 'react';
import { forecastAPI } from '../api/client';

function HealthAdvisory() {
  const [profile, setProfile] = useState('general');
  const [risk, setRisk] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    calculateRisk();
  }, [profile]);

  // Listen for global profile changes (saved on Profile page) and update
  useEffect(() => {
    const handler = (e) => {
      if (e?.detail) setProfile(e.detail);
    };
    window.addEventListener('profile_updated', handler);
    return () => window.removeEventListener('profile_updated', handler);
  }, []);

  const calculateRisk = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await forecastAPI.getHealthRisk('Chennai', profile, 24);
      setRisk(data);

      // Dispatch custom event to dynamically shift background animations matching predicted AQI!
      if (data?.forecast_aqi) {
        window.dispatchEvent(new CustomEvent('aqi_update', { detail: data.forecast_aqi }));
      }
    } catch (err) {
      setError('Failed to calculate health risk assessments. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getAQIColor = (val) => {
    if (val == null) return '#94a3b8';
    if (val <= 50) return '#10b981';
    if (val <= 100) return '#f59e0b';
    if (val <= 200) return '#f97316';
    return '#ef4444';
  };

  const getRiskCategoryClass = (category = '') => {
    const cat = category.toLowerCase();
    if (cat === 'poor' || cat === 'very poor' || cat === 'severe') return 'badge-danger';
    if (cat === 'moderately polluted' || cat === 'satisfactory') return 'badge-warning';
    return 'badge-success';
  };

  const getAlertColorStyle = (category = '') => {
    const cat = category.toLowerCase();
    if (cat === 'poor' || cat === 'very poor' || cat === 'severe') {
      return { borderLeftColor: 'var(--danger)', backgroundColor: 'var(--danger-light)' };
    }
    if (cat === 'moderately polluted' || cat === 'satisfactory') {
      return { borderLeftColor: 'var(--warning)', backgroundColor: 'var(--warning-light)' };
    }
    return { borderLeftColor: 'var(--success)', backgroundColor: 'var(--success-light)' };
  };

  return (
    <div className="fade-in-up">
      <h1 style={{ fontSize: '26px', fontWeight: 800, letterSpacing: '-0.5px', marginBottom: '4px' }}>Personal Health Advisory</h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '24px' }}>
        Select your wellness profile to evaluate respiratory and cardiac risks relative to current air pollution forecasts.
      </p>

      {error && (
        <div className="alert alert-error">
          <svg style={{ width: '20px', height: '20px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* HEALTH PROFILE SELECTION CARD */}
      <div className="card animate-fade-in" style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '16px' }}>Select Health Profile</h2>
        <div className="health-profile-selector">
          <button
            className={`health-profile-btn ${profile === 'general' ? 'active' : ''}`}
            onClick={() => setProfile('general')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            <span>General</span>
          </button>

          <button
            className={`health-profile-btn ${profile === 'respiratory' ? 'active' : ''}`}
            onClick={() => setProfile('respiratory')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 9a5 5 0 1110 0v3a5 5 0 01-10 0V9z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 9a5 5 0 1110 0v3a5 5 0 01-10 0V9z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v18" />
            </svg>
            <span>Respiratory</span>
          </button>

          <button
            className={`health-profile-btn ${profile === 'cardiac' ? 'active' : ''}`}
            onClick={() => setProfile('cardiac')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z" />
            </svg>
            <span>Cardiac</span>
          </button>

          <button
            className={`health-profile-btn ${profile === 'children' ? 'active' : ''}`}
            onClick={() => setProfile('children')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="8" r="4" />
              <path d="M6 21v-2a4 4 0 014-4h4a4 4 0 014 4v2" />
              <path d="M8 12h8" />
            </svg>
            <span>Children</span>
          </button>

          <button
            className={`health-profile-btn ${profile === 'elderly' ? 'active' : ''}`}
            onClick={() => setProfile('elderly')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2a3 3 0 100 6 3 3 0 000-6zM19 22V11a5 5 0 00-5-5h-4a5 5 0 00-5 5v11M9 22v-4a2 2 0 014 0v4" />
            </svg>
            <span>Elderly</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading" style={{ minHeight: '30vh' }}>
          <div className="spinner"></div>
          <p>Recalculating advice checklist...</p>
        </div>
      ) : (
        risk && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* ADVISORY DETAIL BOX */}
            <div className="card">
              <div className="card-header" style={{ marginBottom: '16px' }}>
                <h2>Your Customized Recommendations</h2>
              </div>
              
              <div style={{
                padding: '20px',
                borderLeft: '4px solid',
                borderRadius: '12px',
                marginBottom: '20px',
                ...getAlertColorStyle(risk.category)
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
                  <span className={`badge-category ${getRiskCategoryClass(risk.category)}`}>
                    {risk.category || 'Unknown'}
                  </span>
                  <strong style={{ fontSize: '15px', color: 'var(--text-primary)' }}>Air Quality Category Assessment</strong>
                </div>
                
                {/* PREMIUM RISK PROGRESS BAR GAUGE */}
                <div style={{ margin: '14px 0 12px 0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px', fontWeight: 600 }}>
                    <span>Index scale risk value: {risk.forecast_aqi} AQI</span>
                    <span>Max limit: 300+ AQI</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--border)', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div style={{
                      width: `${Math.min(100, (risk.forecast_aqi / 300) * 100)}%`,
                      height: '100%',
                      backgroundColor: getAQIColor(risk.forecast_aqi),
                      borderRadius: '9999px',
                      transition: 'width 600ms cubic-bezier(0.16, 1, 0.3, 1)'
                    }}></div>
                  </div>
                </div>

                <p style={{ margin: 0, fontSize: '14px', lineHeight: '1.6', fontWeight: 500, color: 'var(--text-secondary)' }}>
                  {risk.recommendations && risk.recommendations.join(' ')}
                </p>
              </div>

              {/* DETAILED STATS GRID */}
              <div>
                <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <svg style={{ width: '18px', height: '18px', color: 'var(--primary)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 00-2 2H9m2 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  Clinical Factor Checklist
                </h3>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                  <div style={{ padding: '16px', border: '1px solid var(--border)', borderRadius: '8px', backgroundColor: 'var(--bg-page)' }}>
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>Activity Level</span>
                    <p style={{ margin: '4px 0 0 0', fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)' }}>{risk.outdoor_activity}</p>
                  </div>

                  <div style={{ padding: '16px', border: '1px solid var(--border)', borderRadius: '8px', backgroundColor: 'var(--bg-page)' }}>
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>Protective Gear</span>
                    <p style={{ margin: '4px 0 0 0', fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)' }}>{risk.mask_required ? 'High-filtering mask recommended' : 'Mask not required'}</p>
                  </div>

                  <div style={{ padding: '16px', border: '1px solid var(--border)', borderRadius: '8px', backgroundColor: 'var(--bg-page)' }}>
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>Ventilation Status</span>
                    <p style={{ margin: '4px 0 0 0', fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)' }}>{risk.ventilation}</p>
                  </div>

                  <div style={{ padding: '16px', border: '1px solid var(--border)', borderRadius: '8px', backgroundColor: 'var(--bg-page)' }}>
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>Emergency Alerts</span>
                    <p style={{ margin: '4px 0 0 0', fontWeight: 600, fontSize: '13px', color: risk.emergency_warning !== 'None' ? 'var(--danger)' : 'var(--text-primary)' }}>{risk.emergency_warning}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* METRICS COMPARISON GRID */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
              <div className="card">
                <h3 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '12px' }}>Current station stats</h3>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--border)', fontSize: '13px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Selected Profile</span>
                  <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{risk.profile}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--border)', fontSize: '13px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Current Air Quality</span>
                  <span style={{ fontWeight: 600, color: getAQIColor(risk.current_aqi) }}>{risk.current_aqi} AQI</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--border)', fontSize: '13px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Predicted 24h Air Quality</span>
                  <span style={{ fontWeight: 600, color: getAQIColor(risk.forecast_aqi) }}>{risk.forecast_aqi} AQI</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', fontSize: '13px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Calculation Date</span>
                  <span style={{ fontWeight: 500, color: 'var(--text-muted)' }}>{new Date(risk.timestamp).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '12px' }}>Personalized Protective Guidelines</h3>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.6', margin: 0 }}>
                    VayuGuard calculates health metrics dynamically by comparing particulate concentrations (PM2.5, PM10, ozone) against medical safety thresholds defined in our expert health configuration files.
                  </p>
                </div>
                <div style={{ padding: '12px', borderRadius: '8px', backgroundColor: 'var(--bg-page)', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '10px', marginTop: '12px' }}>
                  <svg style={{ width: '18px', height: '18px', color: 'var(--primary)', minWidth: '18px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    Make sure to update your permanent Health Profile settings in the <strong>User Profile</strong> tab.
                  </span>
                </div>
              </div>
            </div>
          </div>
        )
      )}
    </div>
  );
}

export default HealthAdvisory;
