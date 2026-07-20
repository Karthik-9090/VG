import React, { useEffect, useState } from 'react';
import { alertsAPI } from '../api/client';

function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [city, setCity] = useState('Chennai');
  const [threshold, setThreshold] = useState('100');

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const { data } = await alertsAPI.getAlerts();
      setAlerts(data.alerts || []);
    } catch (err) {
      setError('Failed to fetch user warning thresholds. Please check connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAlert = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await alertsAPI.createAlert(city, parseInt(threshold));
      fetchAlerts();
      setCity('Chennai');
      setThreshold('100');
    } catch (err) {
      setError('Failed to configure alert. Please check constraints.');
    }
  };

  const handleDeleteAlert = async (alertId) => {
    setError('');
    try {
      await alertsAPI.deleteAlert(alertId);
      fetchAlerts();
    } catch (err) {
      setError('Failed to remove configured alert.');
    }
  };

  if (loading) {
    return (
      <div className="loading" style={{ minHeight: '60vh' }}>
        <div className="spinner"></div>
        <p>Loading alerts panel...</p>
      </div>
    );
  }

  return (
    <div className="fade-in-up">
      <h1 style={{ fontSize: '26px', fontWeight: 800, letterSpacing: '-0.5px', marginBottom: '4px' }}>Notification & Alerts</h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '24px' }}>
        Configure custom atmospheric threshold limits. Receive notifications when sensor levels exceed target AQI metrics.
      </p>

      {error && (
        <div className="alert alert-error">
          <svg style={{ width: '20px', height: '20px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* CREATE ALERT FORM */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>Configure Threshold Limit</h2>
        <form onSubmit={handleCreateAlert} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', alignItems: 'end' }}>
          <div className="input-group" style={{ marginBottom: 0 }}>
            <label htmlFor="alert-city">Target Station</label>
            <select
              id="alert-city"
              value={city}
              onChange={(e) => setCity(e.target.value)}
            >
              <option>Chennai</option>
              <option>Bengaluru</option>
              <option>Hyderabad</option>
            </select>
          </div>

          <div className="input-group" style={{ marginBottom: 0 }}>
            <label htmlFor="alert-threshold">AQI Threshold Limit</label>
            <input
              type="number"
              id="alert-threshold"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              min="0"
              max="500"
              required
            />
          </div>

          <button type="submit" className="button" style={{ height: '42px' }}>
            <svg style={{ width: '18px', height: '18px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
            </svg>
            Activate Warning
          </button>
        </form>
      </div>

      {/* ACTIVE ALERTS CONTAINER */}
      <div className="card">
        <div className="card-header" style={{ marginBottom: '20px' }}>
          <h2>Active Warnings Configured</h2>
          <span className="badge badge-primary">{alerts.length} Warnings Active</span>
        </div>

        {alerts.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🔔</div>
            <h3>No Active Threshold Warnings</h3>
            <p>Configure a targeted AQI alert above to monitor specific municipal stations.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
            {alerts.map((alert) => (
              <div
                key={alert.id}
                style={{
                  padding: '20px',
                  borderRadius: '12px',
                  border: '1px solid rgba(37, 99, 235, 0.15)',
                  backgroundColor: 'var(--bg-page)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  position: 'relative',
                  overflow: 'hidden'
                }}
              >
                {/* Visual blue top highlight line */}
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '4px', backgroundColor: 'var(--primary)' }}></div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>{alert.city}</h3>
                  <span className="badge badge-success" style={{ padding: '2px 8px', fontSize: '10px' }}>Active</span>
                </div>
                
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  Trigger warning when AQI exceeds <strong>{alert.threshold}</strong>.
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border)', paddingTop: '12px', marginTop: '4px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Created: {new Date(alert.created_at).toLocaleDateString()}</span>
                  <button
                    onClick={() => handleDeleteAlert(alert.id)}
                    className="button button-danger"
                    style={{
                      padding: '4px 10px',
                      fontSize: '11px',
                      borderRadius: '6px',
                      boxShadow: 'none',
                      height: '28px'
                    }}
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Alerts;
