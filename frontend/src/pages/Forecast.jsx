import React, { useState } from 'react';
import { forecastAPI } from '../api/client';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';

function Forecast() {
  const [city, setCity] = useState('Chennai');
  const [horizon, setHorizon] = useState(24);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleForecast = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await forecastAPI.getForecast(city, parseInt(horizon));
      setForecast(data);

      // Dispatch custom event to dynamically shift background animations matching predicted AQI!
      if (data?.forecast_aqi) {
        window.dispatchEvent(new CustomEvent('aqi_update', { detail: data.forecast_aqi }));
      }
    } catch (err) {
      setError('Failed to fetch forecast. Please verify connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const downloadCSV = () => {
    if (!forecast) return;

    const rows = [
      ['Forecast Report', `${forecast.city} (${forecast.horizon} hours)`],
      ['Generated', new Date().toLocaleString()],
      [''],
      ['CURRENT CONDITIONS'],
      ['City', forecast.city],
      ['Current AQI', forecast.current_aqi],
      ['Forecast End AQI', forecast.forecast_aqi],
      ['Category', forecast.category],
      ['Confidence', forecast.confidence],
      [''],
      ['CURRENT POLLUTANTS'],
      ...Object.entries(forecast.current_pollutants || {}).map(([key, value]) => 
        [key.replace('_', '.').toUpperCase(), value]
      ),
      [''],
      ['HEALTH RECOMMENDATIONS'],
      ['Health Risk', forecast.health_risk],
      ['Mask Required', forecast.mask_required ? 'Yes' : 'No'],
      ['Outdoor Activity', forecast.outdoor_activity],
      ['Ventilation', forecast.ventilation],
      ['Emergency Warning', forecast.emergency_warning],
      ...((forecast.recommendations || []).length > 0 ? [[''], ['RECOMMENDATIONS'], ...forecast.recommendations.map((rec, idx) => [`Recommendation ${idx + 1}`, rec])] : []),
      [''],
      ['### Hourly Forecast'],
      ['Hour', 'Timestamp', 'AQI', 'Category']
    ];

    if (forecast.forecast_timeseries && forecast.forecast_timeseries.length > 0) {
      forecast.forecast_timeseries.forEach(point => {
        rows.push([
          `Hour ${point.hour}`,
          new Date(point.timestamp).toLocaleString(),
          point.aqi,
          point.category
        ]);
      });
    }

    const csvContent = rows.map(row => 
      row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
    ).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `forecast_${forecast.city}_${forecast.horizon}h_${new Date().getTime()}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getAQIColor = (val) => {
    if (val == null) return '#94a3b8';
    if (val <= 50) return '#10b981'; // Good
    if (val <= 100) return '#f59e0b'; // Satisfactory
    if (val <= 200) return '#f97316'; // Moderate
    return '#ef4444'; // Danger
  };

  const getAQIColorClass = (val) => {
    if (val == null) return 'badge-info';
    if (val <= 50) return 'badge-success';
    if (val <= 100) return 'badge-warning';
    if (val <= 200) return 'badge-warning';
    return 'badge-danger';
  };

  const chartData = forecast?.forecast_timeseries?.map(point => ({
    timeLabel: `Hour ${point.hour}`,
    AQI: point.aqi,
    Category: point.category
  })) || [];

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{
          backgroundColor: 'white',
          padding: '12px',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          boxShadow: 'var(--shadow-md)'
        }}>
          <p style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '4px' }}>
            {data.timeLabel}
          </p>
          <p style={{ fontSize: '18px', fontWeight: 800, color: getAQIColor(data.AQI), margin: 0 }}>
            AQI: {data.AQI}
          </p>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
            Category: {data.Category}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="fade-in-up">
      <h1 style={{ fontSize: '26px', fontWeight: 800, letterSpacing: '-0.5px', marginBottom: '4px' }}>AI Predictive Forecasting</h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '24px' }}>
        Configure geographical stations and time intervals to retrieve multi-hour particulate matter predictions.
      </p>

      {error && (
        <div className="alert alert-error">
          <svg style={{ width: '20px', height: '20px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* PARAMETERS CONTROL BOX */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '16px' }}>Configure Forecast Model</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
          <div className="input-group">
            <label htmlFor="city">City</label>
            <select id="city" value={city} onChange={(e) => setCity(e.target.value)}>
              <option>Chennai</option>
              <option>Bengaluru</option>
              <option>Hyderabad</option>
            </select>
          </div>

          <div className="input-group">
            <label htmlFor="horizon">Horizon (hours)</label>
            <select id="horizon" value={horizon} onChange={(e) => setHorizon(e.target.value)}>
              <option value="24">24 Hours (Next Day)</option>
              <option value="48">48 Hours (2 Days)</option>
              <option value="72">72 Hours (3 Days)</option>
            </select>
          </div>
        </div>

        <button onClick={handleForecast} className="button" disabled={loading} style={{ marginTop: '8px', minWidth: '160px', height: '40px', borderRadius: '8px' }}>
          {loading ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></span>
              Analyzing...
            </span>
          ) : 'Generate Forecast'}
        </button>
      </div>

      {forecast && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* HEADER SUMMARY CARD */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
              <div>
                <h2 style={{ fontSize: '20px', fontWeight: 800, margin: 0 }}>Forecast Assessment for {forecast.city}</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '13px', margin: '4px 0 0 0' }}>
                  Horizon target: <strong>{forecast.horizon || horizon} Hours</strong> | Inference model: <strong>{forecast.model}</strong>
                </p>
              </div>
              <button
                onClick={downloadCSV}
                className="button button-success"
                style={{ height: '38px', padding: '0 16px', fontSize: '13px', borderRadius: '8px' }}
              >
                <svg style={{ width: '15px', height: '15px', marginRight: '6px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Export CSV Report
              </button>
            </div>

            {/* KEY GLANCE STATS GRID */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginTop: '24px' }}>
              <div style={{ padding: '16px', backgroundColor: 'var(--bg-page)', border: '1px solid var(--border)', borderRadius: '12px', borderLeft: `4px solid ${getAQIColor(forecast.current_aqi)}` }}>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Current AQI</span>
                <h3 style={{ fontSize: '28px', fontWeight: 800, color: getAQIColor(forecast.current_aqi), margin: '4px 0' }}>{forecast.current_aqi}</h3>
                <span className={`badge ${getAQIColorClass(forecast.current_aqi)}`}>{forecast.category}</span>
              </div>

              <div style={{ padding: '16px', backgroundColor: 'var(--bg-page)', border: '1px solid var(--border)', borderRadius: '12px', borderLeft: `4px solid ${getAQIColor(forecast.forecast_aqi)}` }}>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Predicted End AQI</span>
                <h3 style={{ fontSize: '28px', fontWeight: 800, color: getAQIColor(forecast.forecast_aqi), margin: '4px 0' }}>{forecast.forecast_aqi}</h3>
                <span className={`badge ${getAQIColorClass(forecast.forecast_aqi)}`}>Model Prediction</span>
              </div>

              <div style={{ padding: '16px', backgroundColor: 'var(--bg-page)', border: '1px solid var(--border)', borderRadius: '12px', borderLeft: '4px solid var(--primary)' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Confidence Score</span>
                <h3 style={{ fontSize: '28px', fontWeight: 800, color: 'var(--primary)', margin: '4px 0' }}>{(forecast.confidence * 100).toFixed(0)}%</h3>
                <span className="badge badge-info">Inference Precision</span>
              </div>
            </div>
          </div>

          {/* DYNAMIC CHART VISUALIZATION */}
          <div className="card">
            <div className="card-header" style={{ marginBottom: '20px' }}>
              <h2>
                <svg style={{ width: '18px', height: '18px', color: 'var(--primary)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 12l3-3 3 3 4-4M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                Predicted AQI Trend Timeline
              </h2>
            </div>
            
            <div style={{ width: '100%', height: '320px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorAqi" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={getAQIColor(forecast.forecast_aqi)} stopOpacity={0.35}/>
                      <stop offset="95%" stopColor={getAQIColor(forecast.forecast_aqi)} stopOpacity={0.01}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                  <XAxis dataKey="timeLabel" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                  <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="AQI" stroke={getAQIColor(forecast.forecast_aqi)} strokeWidth={3} fillOpacity={1} fill="url(#colorAqi)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* TWO COLUMN GRID FOR RECOMMENDATIONS & POLLUTANTS */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
            {/* Pollutants Table */}
            <div className="card">
              <div className="card-header" style={{ marginBottom: '16px' }}>
                <h2>Pollutants Summary</h2>
              </div>
              <div className="table-container" style={{ border: 'none', margin: 0 }}>
                <table style={{ boxShadow: 'none' }}>
                  <thead>
                    <tr>
                      <th style={{ paddingLeft: '8px' }}>Compound</th>
                      <th style={{ textAlign: 'right', paddingRight: '8px' }}>Metric Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(forecast.current_pollutants || {}).map(([key, value]) => (
                      <tr key={key}>
                        <td style={{ paddingLeft: '8px', textTransform: 'uppercase', fontWeight: 600, fontSize: '13px' }}>
                          {key.replace('_', '.')}
                        </td>
                        <td style={{ textAlign: 'right', paddingRight: '8px', fontWeight: 500 }}>
                          {value} {key.includes('pm') ? 'µg/m³' : key.includes('co') ? 'ppm' : 'ppb'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Recommendations List */}
            <div className="card">
              <div className="card-header" style={{ marginBottom: '16px' }}>
                <h2>AI Recommendations</h2>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ padding: '12px', borderLeft: '4px solid var(--warning)', backgroundColor: 'var(--warning-light)', borderRadius: '8px' }}>
                  <strong style={{ display: 'block', fontSize: '13px', color: '#92400e', marginBottom: '2px' }}>Personal Health Assessment</strong>
                  <span style={{ fontSize: '13px', color: '#b45309' }}>{forecast.health_risk}</span>
                </div>
                
                <ul style={{ paddingLeft: '20px', color: 'var(--text-secondary)', fontSize: '13px', lineHeight: '1.7' }}>
                  {forecast.recommendations && forecast.recommendations.map((rec, idx) => (
                    <li key={idx} style={{ marginBottom: '8px' }}>{rec}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* DETAILED TABLE OF TIMELINE DATA */}
          <div className="card">
            <div className="card-header" style={{ marginBottom: '16px' }}>
              <h2>Hourly Time Series Data</h2>
            </div>
            
            <div className="table-container" style={{ margin: 0 }}>
              <table>
                <thead>
                  <tr>
                    <th>Target Hour</th>
                    <th>Prediction Timestamp</th>
                    <th style={{ textAlign: 'center' }}>Predicted AQI</th>
                    <th>Assessment Category</th>
                  </tr>
                </thead>
                <tbody>
                  {forecast.forecast_timeseries && forecast.forecast_timeseries.map((point, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600 }}>+{point.hour}h</td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                        {new Date(point.timestamp).toLocaleString()}
                      </td>
                      <td style={{ textAlign: 'center', fontWeight: 700, color: getAQIColor(point.aqi) }}>
                        {point.aqi}
                      </td>
                      <td>
                        <span className={`badge ${getAQIColorClass(point.aqi)}`} style={{ padding: '2px 10px', fontSize: '11px' }}>
                          {point.category}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Forecast;
