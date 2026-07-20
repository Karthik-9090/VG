import React, { useEffect, useState } from 'react';
import { analyticsAPI } from '../api/client';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts';

function Analytics() {
  const [summary, setSummary] = useState(null);
  const [hotspots, setHotspots] = useState([]);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      const [summaryRes, hotspotsRes, trendsRes] = await Promise.all([
        analyticsAPI.getSummary(),
        analyticsAPI.getHotspots(),
        analyticsAPI.getTrends()
      ]);

      setSummary(summaryRes.data);
      setHotspots(hotspotsRes.data.hotspots || []);
      
      const parsedTrends = transformTrendData(trendsRes.data.trends || {});
      setTrends(parsedTrends);

      // Dispatch custom event to dynamically shift background animations matching avg AQI!
      if (summaryRes.data?.avgAqi) {
        window.dispatchEvent(new CustomEvent('aqi_update', { detail: summaryRes.data.avgAqi }));
      }
    } catch (err) {
      setError('Failed to fetch statistical analytics. Please verify server connection.');
    } finally {
      setLoading(false);
    }
  };

  const transformTrendData = (trendsObj) => {
    const datesMap = {};
    Object.entries(trendsObj).forEach(([city, points]) => {
      points.forEach(pt => {
        const dateObj = new Date(pt.day);
        const dateLabel = dateObj.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
        
        if (!datesMap[dateLabel]) {
          datesMap[dateLabel] = { 
            name: dateLabel,
            _rawDate: dateObj.getTime()
          };
        }
        datesMap[dateLabel][city] = pt.avgAqi;
      });
    });

    return Object.values(datesMap)
      .sort((a, b) => a._rawDate - b._rawDate)
      .map(({ _rawDate, ...rest }) => rest);
  };

  const getAQIColor = (val) => {
    if (val == null) return '#94a3b8';
    if (val <= 50) return '#10b981';
    if (val <= 100) return '#f59e0b';
    if (val <= 200) return '#f97316';
    return '#ef4444';
  };

  if (loading) {
    return (
      <div className="loading" style={{ minHeight: '60vh' }}>
        <div className="spinner"></div>
        <p>Generating executive analytics dashboard...</p>
      </div>
    );
  }

  return (
    <div className="fade-in-up">
      <h1 style={{ fontSize: '26px', fontWeight: 800, letterSpacing: '-0.5px', marginBottom: '4px' }}>Analytics & Intelligence</h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '24px' }}>
        Executive reporting covering average station metrics, active warning thresholds, and multi-city comparative trends.
      </p>

      {error && (
        <div className="alert alert-error">
          <svg style={{ width: '20px', height: '20px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* KPI BLOCKS */}
      {summary && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="grid-3">
            <div className="stat-box info" style={{ borderLeft: '4px solid var(--accent)' }}>
              <span className="stat-box-title">Average Station AQI</span>
              <h3>{Math.round(summary.avgAqi)}</h3>
              <span className="stat-box-desc">Across all monitored cities</span>
            </div>

            <div className="stat-box warning" style={{ borderLeft: '4px solid var(--warning)' }}>
              <span className="stat-box-title">Configured Alerts</span>
              <h3>{summary.alerts}</h3>
              <span className="stat-box-desc">Active threshold warnings</span>
            </div>

            <div className="stat-box primary" style={{ borderLeft: '4px solid var(--primary)' }}>
              <span className="stat-box-title">Locations Monitored</span>
              <h3>{summary.cities.length}</h3>
              <span className="stat-box-desc">Active meteorological stations</span>
            </div>
          </div>

          {/* DUAL CHART ROW */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '24px' }}>
            {/* Trends multi-line chart */}
            <div className="card">
              <div className="card-header" style={{ marginBottom: '20px' }}>
                <h2>7-Day Historical AQI Trends</h2>
              </div>
              <div style={{ width: '100%', height: '300px' }}>
                {trends.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                      <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                      <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                      <Tooltip />
                      <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                      <Line type="monotone" dataKey="Chennai" stroke="var(--primary)" strokeWidth={3} dot={{ r: 3 }} activeDot={{ r: 6 }} />
                      <Line type="monotone" dataKey="Bengaluru" stroke="var(--success)" strokeWidth={3} dot={{ r: 3 }} activeDot={{ r: 6 }} />
                      <Line type="monotone" dataKey="Hyderabad" stroke="var(--warning)" strokeWidth={3} dot={{ r: 3 }} activeDot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-state" style={{ height: '100%' }}>
                    <p>No trend historical datasets logged in the last 7 days</p>
                  </div>
                )}
              </div>
            </div>

            {/* Hotspots Bar chart */}
            <div className="card">
              <div className="card-header" style={{ marginBottom: '20px' }}>
                <h2>Station Pollution Hotspots</h2>
              </div>
              <div style={{ width: '100%', height: '300px' }}>
                {hotspots.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={hotspots} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                      <XAxis dataKey="city" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                      <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                      <Tooltip />
                      <Bar dataKey="aqi" radius={[6, 6, 0, 0]}>
                        {hotspots.map((entry, index) => (
                          <rect
                            key={`cell-${index}`}
                            fill={getAQIColor(entry.aqi)}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-state" style={{ height: '100%' }}>
                    <p>No hotspots logged currently</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* MONITORED LOCATIONS FOOTER CARD */}
          <div className="card">
            <h2 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '12px' }}>Operational Meteorological Stations</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '16px' }}>
              The following cities are actively feeding real-time air quality telemetry via WAQI APIs to our predictive training clusters.
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {summary.cities.map((city, idx) => (
                <span key={idx} className="badge badge-primary" style={{ padding: '6px 14px', fontSize: '12px', borderRadius: '8px' }}>
                  <svg style={{ width: '12px', height: '12px', marginRight: '4px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {city} Status Active
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Analytics;
