import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Icon } from 'leaflet';
import { forecastAPI } from '../api/client';
import 'leaflet/dist/leaflet.css';

function Map() {
  const [aqiData, setAqiData] = useState({});
  const [loading, setLoading] = useState(true);

  // City coordinates
  const cities = {
    Chennai: { lat: 13.0827, lng: 80.2707 },
    Bengaluru: { lat: 12.9716, lng: 77.5946 },
    Hyderabad: { lat: 17.3850, lng: 78.4867 }
  };

  useEffect(() => {
    fetchAQIData();
  }, []);

  const fetchAQIData = async () => {
    try {
      const cityEntries = Object.keys(cities);
      const results = await Promise.allSettled(
        cityEntries.map(async (city) => {
          const { data } = await forecastAPI.getCurrentAqi(city);
          return { city, data };
        })
      );

      const aqi = {};
      results.forEach((result) => {
        if (result.status === 'fulfilled') {
          aqi[result.value.city] = result.value.data;
        }
      });
      setAqiData(aqi);

      // Dispatch contextual backdrop event for the primary station (Chennai)
      if (aqi.Chennai?.aqi) {
        window.dispatchEvent(new CustomEvent('aqi_update', { detail: aqi.Chennai.aqi }));
      }
    } catch (err) {
      console.error('Failed to fetch AQI data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getAQIColor = (aqi) => {
    if (aqi == null) return '#94a3b8'; // Slate 400
    if (aqi <= 50) return '#10b981'; // Green
    if (aqi <= 100) return '#f59e0b'; // Amber
    if (aqi <= 200) return '#f97316'; // Orange
    if (aqi <= 300) return '#ef4444'; // Red
    return '#7f1d1d'; // Dark Red / Severe
  };

  const createMarkerIcon = (aqi) => {
    const pinColor = getAQIColor(aqi);
    return new Icon({
      iconUrl: `data:image/svg+xml;base64,${btoa(
        `<svg xmlns="http://www.w3.org/2000/svg" width="40" height="50" viewBox="0 0 40 50">
          <circle cx="20" cy="20" r="15" fill="${pinColor}" stroke="white" stroke-width="2"/>
          <polygon points="20,50 10,30 30,30" fill="${pinColor}"/>
          <circle cx="20" cy="20" r="6" fill="white" opacity="0.8"/>
        </svg>`
      )}`,
      iconSize: [40, 50],
      iconAnchor: [20, 50],
      popupAnchor: [0, -50]
    });
  };

  if (loading) {
    return (
      <div className="loading" style={{ minHeight: '60vh' }}>
        <div className="spinner"></div>
        <p>Loading geospatial map telemetries...</p>
      </div>
    );
  }

  return (
    <div className="fade-in-up">
      <h1 style={{ fontSize: '26px', fontWeight: 800, letterSpacing: '-0.5px', marginBottom: '4px' }}>Real-time Air Quality Map</h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '24px' }}>
        Geospatial distribution of atmospheric monitors across the Southern Peninsula tracking realtime AQI markers.
      </p>

      <div className="card" style={{ padding: '16px', position: 'relative', overflow: 'visible' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>Municipal Telemetry Distribution Overlay</span>
          <span className="live-indicator">
            <div className="live-pulse"></div>
            Live Tracking
          </span>
        </div>

        {/* MAP WRAPPER WITH ABSOLUTE OVERLAY LEGEND */}
        <div style={{ position: 'relative', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--border)' }}>
          <MapContainer
            center={[14.5, 78.5]}
            zoom={6}
            style={{ width: '100%', height: '480px', zIndex: 1 }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {Object.entries(cities).map(([city, coords]) => {
              const cityData = aqiData[city];
              const cityAqi = cityData?.aqi ?? '-';
              const cityCategory = cityData?.category ?? '-';
              const cityColor = getAQIColor(cityData?.aqi);

              return (
                <Marker
                  key={city}
                  position={[coords.lat, coords.lng]}
                  icon={createMarkerIcon(cityData?.aqi)}
                >
                  <Popup>
                    <div style={{ fontFamily: 'inherit', fontSize: '13px', minWidth: '150px' }}>
                      <strong style={{ fontSize: '14px', display: 'block', marginBottom: '6px' }}>{city}</strong>
                      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '6px' }}>
                        <div style={{ color: cityColor, fontWeight: 'bold', fontSize: '15px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: cityColor, display: 'inline-block' }}></span>
                          AQI: {cityAqi}
                        </div>
                        <div style={{ color: 'var(--text-secondary)', marginTop: '4px', fontSize: '12px' }}>
                          Status: <strong>{cityCategory}</strong>
                        </div>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              );
            })}
          </MapContainer>

          {/* FLOATING LEGEND GLASS PANEL OVERLAY */}
          <div style={{
            position: 'absolute',
            bottom: '16px',
            right: '16px',
            zIndex: 10,
            backgroundColor: 'rgba(255, 255, 255, 0.85)',
            backdropFilter: 'blur(12px)',
            padding: '14px 18px',
            borderRadius: '10px',
            boxShadow: 'var(--shadow-lg)',
            border: '1px solid rgba(226, 232, 240, 0.8)',
            fontSize: '11px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            pointerEvents: 'auto'
          }}>
            <div style={{ fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '4px', color: 'var(--text-primary)' }}>
              AQI Scale Legend
            </div>
            <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#10b981', width: '12px', height: '12px' }}></span> Good (0 - 50)</div>
            <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#f59e0b', width: '12px', height: '12px' }}></span> Satisfactory (51 - 100)</div>
            <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#f97316', width: '12px', height: '12px' }}></span> Moderate (101 - 200)</div>
            <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#ef4444', width: '12px', height: '12px' }}></span> Poor (201 - 300)</div>
            <div className="legend-item"><span className="legend-color" style={{ backgroundColor: '#7f1d1d', width: '12px', height: '12px' }}></span> Severe (301+)</div>
          </div>
        </div>

        {/* DETAILS LIST AT BOTTOM */}
        <div style={{ marginTop: '24px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          {Object.entries(cities).map(([city, _]) => {
            const cityData = aqiData[city];
            const aqiValue = cityData?.aqi;
            const cardColor = getAQIColor(aqiValue);
            
            return (
              <div
                key={city}
                style={{
                  padding: '16px',
                  backgroundColor: 'var(--bg-page)',
                  borderRadius: '10px',
                  border: '1px solid var(--border)',
                  borderLeft: `4px solid ${cardColor}`,
                  transition: 'all var(--transition-fast)',
                  cursor: 'pointer'
                }}
                onClick={() => {
                  // Allow manual backdrop shifting by clicking on city reference cards!
                  if (aqiValue) {
                    window.dispatchEvent(new CustomEvent('aqi_update', { detail: aqiValue }));
                  }
                }}
                className="map-city-card"
              >
                <div style={{ fontWeight: 700, fontSize: '14px', marginBottom: '4px' }}>{city}</div>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>AQI Index:</span>
                  <span style={{ fontWeight: 'bold', color: cardColor }}>{aqiValue ?? '-'}</span>
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', textTransform: 'capitalize' }}>
                  {cityData?.category || 'No data reported'}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default Map;
