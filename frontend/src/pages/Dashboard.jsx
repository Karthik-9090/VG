import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { forecastAPI } from '../api/client';

function Dashboard() {
  const [aqi, setAqi] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sseActive, setSseActive] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    let es;
    let reconnectTimeout = null;
    const token = localStorage.getItem('token');

    const startSse = () => {
      if (!token) return fetchAQI();
      const sseUrl = `/api/sse/aqi?token=${encodeURIComponent(token)}`;
      try {
        es = new EventSource(sseUrl);
        es.onopen = () => {
          console.info('SSE open');
          setLoading(false);
          setSseActive(true);
        };
        es.onmessage = (e) => {
          try {
            const payload = JSON.parse(e.data);
            setAqi(payload.data);
            setSseActive(true);
            setLastUpdated(new Date().toLocaleTimeString());
            
            // Dispatch custom event for contextual backdrop animations
            if (payload.data?.aqi) {
              window.dispatchEvent(new CustomEvent('aqi_update', { detail: payload.data.aqi }));
            }
          } catch (err) {
            console.error('Failed to parse SSE message', err);
          }
        };
        es.onerror = (err) => {
          console.warn('SSE error', err);
          setSseActive(false);
          try { es.close(); } catch (e) {}
          if (reconnectTimeout) clearTimeout(reconnectTimeout);
          let attempts = (window.__sseReconnectAttempts || 0) + 1;
          window.__sseReconnectAttempts = attempts;
          const wait = Math.min(30000, 1000 * Math.pow(2, Math.min(attempts, 5)));
          reconnectTimeout = setTimeout(() => startSse(), wait);
        };
      } catch (err) {
        console.warn('SSE not available, falling back to fetch', err);
        setSseActive(false);
        fetchAQI();
      }
    };

    startSse();

    return () => {
      if (es) try { es.close(); } catch (e) {}
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  const fetchAQI = async () => {
    try {
      const { data } = await forecastAPI.getCurrentAqi('Chennai');
      setAqi(data);
      setLastUpdated(new Date().toLocaleTimeString());
      
      // Dispatch custom event for contextual backdrop animations
      if (data?.aqi) {
        window.dispatchEvent(new CustomEvent('aqi_update', { detail: data.aqi }));
      }
    } catch (err) {
      setError('Failed to fetch real-time AQI data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getAQIColorClass = (val) => {
    if (val == null) return 'badge-info';
    if (val <= 50) return 'badge-success';
    if (val <= 100) return 'badge-warning';
    if (val <= 200) return 'badge-warning'; // moderately polluted
    return 'badge-danger';
  };

  const getAQICircleStyle = (val) => {
    if (val == null) return { borderColor: '#e2e8f0', color: '#64748b' };
    if (val <= 50) return { borderColor: '#10b981', color: '#10b981', backgroundColor: '#f0fdf4' };
    if (val <= 100) return { borderColor: '#f59e0b', color: '#b45309', backgroundColor: '#fffbeb' };
    if (val <= 200) return { borderColor: '#f97316', color: '#c2410c', backgroundColor: '#fff7ed' };
    return { borderColor: '#ef4444', color: '#ef4444', backgroundColor: '#fef2f2' };
  };

  if (loading) {
    return (
      <div className="loading" style={{ minHeight: '60vh' }}>
        <div className="spinner"></div>
        <p>Loading real-time environmental data...</p>
      </div>
    );
  }

  return (
    <div className="fade-in-up">
      {/* WOW-FACTOR HERO SECTION */}
      <div className="card premium-glow" style={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        color: 'white',
        border: 'none',
        padding: '40px 32px',
        marginBottom: '28px',
        borderRadius: '20px',
        boxShadow: 'var(--shadow-xl)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Soft atmospheric gradient blob inside the card */}
        <div style={{
          position: 'absolute',
          top: '-20%',
          right: '-10%',
          width: '300px',
          height: '300px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(6,182,212,0.15) 0%, rgba(37,99,235,0) 70%)',
          pointerEvents: 'none'
        }}></div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '24px', zIndex: 1, position: 'relative' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
              <span className="badge" style={{ backgroundColor: 'rgba(37, 99, 235, 0.25)', border: 'none', color: '#93c5fd', fontSize: '11px' }}>
                🌍 Environmental Intelligence
              </span>
              {sseActive && (
                <span className="live-indicator" style={{ border: 'none', padding: '2px 8px', fontSize: '10px', backgroundColor: 'rgba(16, 185, 129, 0.2)', color: '#34d399' }}>
                  <div className="live-pulse" style={{ backgroundColor: '#10b981' }}></div>
                  SSE Active
                </span>
              )}
            </div>
            
            <h1 style={{ color: 'white', marginBottom: '8px', fontSize: '30px', fontWeight: 800, letterSpacing: '-0.8px' }}>
              Air Quality Dashboard
            </h1>
            <p style={{ color: '#cbd5e1', fontSize: '14px', margin: 0, maxWidth: '640px', lineHeight: '1.6' }}>
              VayuGuard feeds live telemetry metrics through automated regression clusters, evaluating regional atmospheric qualities to dispatch real-time health warnings.
            </p>
            {lastUpdated && (
              <div style={{ marginTop: '12px', fontSize: '11px', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '5px', height: '5px', borderRadius: '50%', backgroundColor: '#94a3b8' }}></span>
                System telemetry synced at: <strong>{lastUpdated}</strong>
              </div>
            )}
          </div>
          
          <div style={{ display: 'flex', gap: '12px' }}>
            <Link to="/forecast" className="button" style={{ height: '42px', boxShadow: '0 4px 14px rgba(37,99,235,0.4)', borderRadius: '8px' }}>
              Predictive Models
            </Link>
          </div>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          <svg style={{ width: '20px', height: '20px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* METRICS CARDS GRID */}
      <div className="grid">
        {/* Live AQI card */}
        <div className="card fade-in-up delay-1" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div className="card-header" style={{ marginBottom: '12px' }}>
            <h2>
              <svg style={{ width: '18px', height: '18px', color: 'var(--primary)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Current AQI Index
            </h2>
            <span className="badge badge-primary" style={{ padding: '2px 8px', fontSize: '10px' }}>Chennai</span>
          </div>

          {aqi ? (
            <div className="aqi-radial-container" style={{ margin: '8px 0' }}>
              <div className="aqi-radial-gauge" style={{
                border: '6px solid',
                transition: 'all 500ms ease',
                ...getAQICircleStyle(aqi.aqi)
              }}>
                <span className="aqi-radial-value">{aqi.aqi}</span>
                <span className="aqi-radial-label" style={{ fontSize: '9px', marginTop: '1px' }}>AQI Index</span>
              </div>
              <div style={{ textAlign: 'center', marginTop: '14px' }}>
                <p style={{ fontWeight: 700, fontSize: '15px', color: 'var(--text-primary)', margin: '0 0 2px 0' }}>
                  {aqi.category}
                </p>
                <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: 0 }}>
                  Live station telemetry
                </p>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <p>No real-time data received yet</p>
            </div>
          )}
        </div>

        {/* AI Health Advisory card */}
        <div className="card fade-in-up delay-2" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div className="card-header" style={{ marginBottom: '12px' }}>
              <h2>
                <svg style={{ width: '18px', height: '18px', color: 'var(--success)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                Health Advisory
              </h2>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '14px', lineHeight: '1.5' }}>
              Retrieve micro-tailored environmental precautions adapted to custom clinical filters like cardiac, pediatric or respiratory issues.
            </p>
            {aqi && (
              <div style={{ padding: '12px', borderRadius: '8px', backgroundColor: 'var(--bg-page)', border: '1px solid var(--border)', fontSize: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span className={`badge ${getAQIColorClass(aqi.aqi)}`} style={{ padding: '2px 8px', fontSize: '9px' }}>
                    Risk Level: {aqi.aqi > 100 ? 'Cautious' : 'Minimal'}
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '11px', color: 'var(--text-secondary)' }}>
                  Outdoor conditions are <strong>{aqi.aqi > 100 ? 'compromised for sensitive groups' : 'healthy for all profiles'}</strong>.
                </p>
              </div>
            )}
          </div>
          <Link to="/health-advisory" className="button button-secondary" style={{ width: '100%', marginTop: '12px', height: '38px', fontSize: '13px', borderRadius: '8px' }}>
            Check Health Score
          </Link>
        </div>

        {/* ML Forecast Summary card */}
        <div className="card fade-in-up delay-3" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div className="card-header" style={{ marginBottom: '12px' }}>
              <h2>
                <svg style={{ width: '18px', height: '18px', color: 'var(--accent)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                Atmospheric Forecast
              </h2>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '14px', lineHeight: '1.5' }}>
              Generate future forecasting curves mapping particulate concentration gradients over 24h, 48h, and 72h cycles.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '11px' }}>
              <div style={{ padding: '8px', borderRadius: '6px', backgroundColor: 'var(--bg-page)', border: '1px solid var(--border)' }}>
                <span style={{ fontWeight: 600, display: 'block', color: 'var(--text-primary)' }}>Lasso Clusters</span>
                <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>Inference active</span>
              </div>
              <div style={{ padding: '8px', borderRadius: '6px', backgroundColor: 'var(--bg-page)', border: '1px solid var(--border)' }}>
                <span style={{ fontWeight: 600, display: 'block', color: 'var(--text-primary)' }}>Confidence index</span>
                <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>92% Precision</span>
              </div>
            </div>
          </div>
          <Link to="/forecast" className="button button-secondary" style={{ width: '100%', marginTop: '12px', height: '38px', fontSize: '13px', borderRadius: '8px' }}>
            Check Predictive Graphs
          </Link>
        </div>
      </div>

      {/* DETAILED POLLUTANTS KPI CARD WITH SPARKLINE INDICATORS */}
      {aqi && (
        <div className="card fade-in-up delay-4" style={{ marginTop: '12px' }}>
          <div className="card-header" style={{ marginBottom: '24px' }}>
            <h2>
              <svg style={{ width: '18px', height: '18px', color: 'var(--primary)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10a2 2 0 01-2 2h-2a2 2 0 01-2-2zm9 0V4a2 2 0 00-2-2h-2a2 2 0 00-2 2v15a2 2 0 002 2h2a2 2 0 002-2z" />
              </svg>
              Atmospheric Pollutant Distribution
            </h2>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Realtime Sensor Telemetry</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
            {/* PM2.5 */}
            <div style={{ padding: '18px', borderRadius: '12px', backgroundColor: '#f8fafc', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>PM2.5</span>
                <h3 style={{ fontSize: '22px', fontWeight: 800, margin: '4px 0' }}>{aqi.pm2_5} <span style={{ fontSize: '11px', fontWeight: 500, color: 'var(--text-muted)' }}>µg/m³</span></h3>
              </div>
              <div style={{ marginTop: '8px' }}>
                <svg viewBox="0 0 100 20" width="100%" height="20" style={{ overflow: 'visible' }}>
                  <path d="M0,10 Q10,12 20,5 T40,15 T60,8 T80,18 T100,6" fill="none" stroke="var(--primary)" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </div>
            </div>

            {/* PM10 */}
            <div style={{ padding: '18px', borderRadius: '12px', backgroundColor: '#f8fafc', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>PM10</span>
                <h3 style={{ fontSize: '22px', fontWeight: 800, margin: '4px 0' }}>{aqi.pm10} <span style={{ fontSize: '11px', fontWeight: 500, color: 'var(--text-muted)' }}>µg/m³</span></h3>
              </div>
              <div style={{ marginTop: '8px' }}>
                <svg viewBox="0 0 100 20" width="100%" height="20" style={{ overflow: 'visible' }}>
                  <path d="M0,8 Q15,4 30,12 T60,4 T80,15 T100,8" fill="none" stroke="var(--success)" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </div>
            </div>

            {/* NO2 */}
            <div style={{ padding: '18px', borderRadius: '12px', backgroundColor: '#f8fafc', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>NO2</span>
                <h3 style={{ fontSize: '22px', fontWeight: 800, margin: '4px 0' }}>{aqi.no2} <span style={{ fontSize: '11px', fontWeight: 500, color: 'var(--text-muted)' }}>ppb</span></h3>
              </div>
              <div style={{ marginTop: '8px' }}>
                <svg viewBox="0 0 100 20" width="100%" height="20" style={{ overflow: 'visible' }}>
                  <path d="M0,15 Q10,5 25,12 T50,4 T75,18 T100,10" fill="none" stroke="var(--warning)" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </div>
            </div>

            {/* SO2 */}
            <div style={{ padding: '18px', borderRadius: '12px', backgroundColor: '#f8fafc', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>SO2</span>
                <h3 style={{ fontSize: '22px', fontWeight: 800, margin: '4px 0' }}>{aqi.so2} <span style={{ fontSize: '11px', fontWeight: 500, color: 'var(--text-muted)' }}>ppb</span></h3>
              </div>
              <div style={{ marginTop: '8px' }}>
                <svg viewBox="0 0 100 20" width="100%" height="20" style={{ overflow: 'visible' }}>
                  <path d="M0,5 Q20,15 40,8 T70,12 T100,4" fill="none" stroke="var(--danger)" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </div>
            </div>

            {/* CO */}
            <div style={{ padding: '18px', borderRadius: '12px', backgroundColor: '#f8fafc', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>CO</span>
                <h3 style={{ fontSize: '22px', fontWeight: 800, margin: '4px 0' }}>{aqi.co} <span style={{ fontSize: '11px', fontWeight: 500, color: 'var(--text-muted)' }}>ppm</span></h3>
              </div>
              <div style={{ marginTop: '8px' }}>
                <svg viewBox="0 0 100 20" width="100%" height="20" style={{ overflow: 'visible' }}>
                  <path d="M0,12 Q10,4 30,14 T60,6 T90,12 T100,5" fill="none" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </div>
            </div>

            {/* O3 */}
            <div style={{ padding: '18px', borderRadius: '12px', backgroundColor: '#f8fafc', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>O3</span>
                <h3 style={{ fontSize: '22px', fontWeight: 800, margin: '4px 0' }}>{aqi.o3} <span style={{ fontSize: '11px', fontWeight: 500, color: 'var(--text-muted)' }}>ppb</span></h3>
              </div>
              <div style={{ marginTop: '8px' }}>
                <svg viewBox="0 0 100 20" width="100%" height="20" style={{ overflow: 'visible' }}>
                  <path d="M0,10 Q20,4 40,15 T70,8 T100,12" fill="none" stroke="var(--info)" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
