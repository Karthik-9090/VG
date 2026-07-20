import React, { useState, useEffect } from 'react';

function EnvironmentalBackdrop({ initialAqi = 45 }) {
  const [aqi, setAqi] = useState(initialAqi);

  useEffect(() => {
    const handleUpdate = (e) => {
      const val = Number(e?.detail);
      if (Number.isFinite(val)) {
        setAqi(val);
      }
    };
    window.addEventListener('aqi_update', handleUpdate);
    return () => window.removeEventListener('aqi_update', handleUpdate);
  }, []);

  // Determine state parameters based on current AQI value
  const getContextualSettings = (val) => {
    if (val <= 50) {
      return {
        category: 'good',
        colorBlob1: 'rgba(16, 185, 129, 0.06)', // Emerald
        colorBlob2: 'rgba(6, 182, 212, 0.06)',   // Cyan
        windDuration1: '24s',
        windDuration2: '18s',
        leafCount: 3,
        hazeOpacity: 0.02
      };
    }
    if (val <= 100) {
      return {
        category: 'satisfactory',
        colorBlob1: 'rgba(245, 158, 11, 0.05)',  // Amber
        colorBlob2: 'rgba(6, 182, 212, 0.06)',   // Cyan
        windDuration1: '18s',
        windDuration2: '14s',
        leafCount: 3,
        hazeOpacity: 0.03
      };
    }
    if (val <= 200) {
      return {
        category: 'moderate',
        colorBlob1: 'rgba(249, 115, 22, 0.06)',  // Orange
        colorBlob2: 'rgba(239, 68, 68, 0.05)',   // Red
        windDuration1: '14s',
        windDuration2: '10s',
        leafCount: 2,
        hazeOpacity: 0.06
      };
    }
    if (val <= 300) {
      return {
        category: 'poor',
        colorBlob1: 'rgba(239, 68, 68, 0.08)',   // Red
        colorBlob2: 'rgba(220, 38, 38, 0.06)',   // Crimson
        windDuration1: '10s',
        windDuration2: '8s',
        leafCount: 1,
        hazeOpacity: 0.12
      };
    }
    return {
      category: 'severe',
      colorBlob1: 'rgba(127, 29, 29, 0.12)',   // Dark Red
      colorBlob2: 'rgba(120, 53, 4, 0.08)',    // Dark Amber
      windDuration1: '8s',
      windDuration2: '6s',
      leafCount: 0,
      hazeOpacity: 0.2
    };
  };

  const settings = getContextualSettings(aqi);

  const LeafIcon = ({ color = '#10b981', strokeColor = '#047857' }) => (
    <svg viewBox="0 0 24 24" width="100%" height="100%" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2 22C2 13.72 8.72 7 17 7H22V12C22 20.28 15.28 27 7 27H2" fill={color} />
      <path d="M2 22L17 7" stroke={strokeColor} strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );

  return (
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      overflow: 'hidden',
      pointerEvents: 'none',
      zIndex: 0,
      transition: 'background-color var(--transition-slow)'
    }}>
      {/* 1. DYNAMIC HAZE LAYER FILTER */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        backgroundColor: 'rgba(120, 113, 108, 1)',
        opacity: settings.hazeOpacity,
        transition: 'opacity var(--transition-slow)',
        zIndex: 1
      }}></div>

      {/* 2. AMBIENT GLOW BLOBS */}
      <div className="ambient-glow-blob" style={{
        top: '10%',
        left: '5%',
        width: '350px',
        height: '350px',
        backgroundColor: settings.colorBlob1,
        transition: 'background-color var(--transition-slow)'
      }}></div>
      
      <div className="ambient-glow-blob" style={{
        bottom: '15%',
        right: '10%',
        width: '420px',
        height: '420px',
        backgroundColor: settings.colorBlob2,
        animationDelay: '-5s',
        animationDuration: '22s',
        transition: 'background-color var(--transition-slow)'
      }}></div>

      {/* 3. DYNAMIC WIND LINES */}
      <svg width="100%" height="100%" style={{ position: 'absolute', top: 0, left: 0, zIndex: 0, opacity: 0.4 }}>
        <path d="M -100 180 Q 250 280 600 150 T 1300 220 T 2000 180" fill="none" stroke="url(#windGrad)" strokeWidth="2.5" className="wind-path" style={{ animationDuration: settings.windDuration1 }} />
        <path d="M -100 500 Q 350 400 800 500 T 1700 440" fill="none" stroke="url(#windGrad)" strokeWidth="1.5" className="wind-path" style={{ animationDelay: '-4s', animationDuration: settings.windDuration2 }} />
        <defs>
          <linearGradient id="windGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#2563eb" stopOpacity="0" />
            <stop offset="50%" stopColor={aqi > 200 ? '#ef4444' : aqi > 100 ? '#f59e0b' : '#06b6d4'} stopOpacity="0.35" />
            <stop offset="100%" stopColor="#2563eb" stopOpacity="0" />
          </linearGradient>
        </defs>
      </svg>

      {/* 4. CONTEXTUAL LEAF ELEMENTS */}
      {settings.leafCount >= 1 && (
        <div className="drifting-leaf leaf-path-1" style={{ width: '20px', height: '20px' }}>
          <LeafIcon color={aqi > 100 ? '#eab308' : '#10b981'} strokeColor={aqi > 100 ? '#a16207' : '#047857'} />
        </div>
      )}
      {settings.leafCount >= 2 && (
        <div className="drifting-leaf leaf-path-2" style={{ width: '26px', height: '26px', animationDelay: '-6s' }}>
          <LeafIcon color={aqi > 100 ? '#f59e0b' : '#34d399'} strokeColor={aqi > 100 ? '#b45309' : '#059669'} />
        </div>
      )}
      {settings.leafCount >= 3 && (
        <div className="drifting-leaf leaf-path-3" style={{ width: '15px', height: '15px', animationDelay: '-12s' }}>
          <LeafIcon color="#059669" strokeColor="#047857" />
        </div>
      )}
    </div>
  );
}

export default EnvironmentalBackdrop;
