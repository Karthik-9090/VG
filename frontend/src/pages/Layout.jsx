import React, { useState } from 'react';
import { Outlet, useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import EnvironmentalBackdrop from '../components/EnvironmentalBackdrop';

function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) => {
    if (path === '/' && location.pathname === '/') return 'active';
    if (path !== '/' && location.pathname.startsWith(path)) return 'active';
    return '';
  };

  return (
    <div className={`app-layout ${collapsed ? 'sidebar-collapsed' : ''}`}>
      {/* SIDEBAR NAVIGATION */}
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-logo">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="url(#logoGrad)" stroke="white" strokeWidth="2" strokeLinejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <defs>
              <linearGradient id="logoGrad" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                <stop stopColor="#60a5fa" />
                <stop offset="1" stopColor="#2563eb" />
              </linearGradient>
            </defs>
          </svg>
          <h1>VayuGuard</h1>
        </div>

        <nav className="sidebar-nav">
          <Link to="/" className={isActive('/')}>
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            {!collapsed && <span>Dashboard</span>}
          </Link>

          <Link to="/forecast" className={isActive('/forecast')}>
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            {!collapsed && <span>Forecast</span>}
          </Link>

          <Link to="/health-advisory" className={isActive('/health-advisory')}>
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            {!collapsed && <span>Health Advisory</span>}
          </Link>

          <Link to="/analytics" className={isActive('/analytics')}>
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10a2 2 0 01-2 2h-2a2 2 0 01-2-2zm9 0V4a2 2 0 00-2-2h-2a2 2 0 00-2 2v15a2 2 0 002 2h2a2 2 0 002-2z" />
            </svg>
            {!collapsed && <span>Analytics</span>}
          </Link>

          <Link to="/alerts" className={isActive('/alerts')}>
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            {!collapsed && <span>Alerts</span>}
          </Link>

          <Link to="/map" className={isActive('/map')}>
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
            {!collapsed && <span>Map</span>}
          </Link>

          {user?.role === 'admin' && (
            <Link to="/admin" className={isActive('/admin')}>
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
              </svg>
              {!collapsed && <span>Admin</span>}
            </Link>
          )}

          <Link to="/profile" className={isActive('/profile')}>
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            {!collapsed && <span>Profile</span>}
          </Link>

          <button
            onClick={handleLogout}
            style={{
              background: 'none',
              border: 'none',
              color: '#f44336',
              cursor: 'pointer',
              padding: '12px 16px',
              width: '100%',
              textAlign: 'left',
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
              fontSize: '14px',
              fontWeight: 500,
              borderRadius: '10px',
              marginTop: 'auto',
              transition: 'background-color 150ms ease'
            }}
            className="sidebar-logout-btn"
          >
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ minWidth: '20px', height: '20px' }}>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            {!collapsed && <span>Logout</span>}
          </button>
        </nav>

        {!collapsed && user && (
          <div className="sidebar-footer">
            <div className="sidebar-profile">
              <div className="sidebar-profile-avatar">
                {user.email ? user.email[0].toUpperCase() : 'U'}
              </div>
              <div className="sidebar-profile-info">
                <span className="sidebar-profile-name">{user.email?.split('@')[0] || 'User'}</span>
                <span className="sidebar-profile-role">{user.role || 'Member'}</span>
              </div>
            </div>
          </div>
        )}
      </aside>

      {/* MAIN CONTENT BLOCK */}
      <div className="main-content" style={{ position: 'relative' }}>
        <EnvironmentalBackdrop leafCount={3} />
        
        {/* TOP NAVIGATION BAR */}
        <header className="top-nav">
          <div className="top-nav-left">
            <button className="sidebar-toggle" onClick={() => setCollapsed(!collapsed)} aria-label="Toggle sidebar">
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ width: '20px', height: '20px' }}>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="top-nav-search">
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ width: '16px', height: '16px', color: '#94a3b8' }}>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input type="text" placeholder="Search parameters..." disabled />
              <span style={{
                fontSize: '9px',
                fontWeight: 700,
                color: 'var(--text-muted)',
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                padding: '2px 6px',
                userSelect: 'none',
                letterSpacing: '0.5px'
              }}>⌘K</span>
            </div>
          </div>

          <div className="top-nav-right">
            <div className="city-badge">
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ width: '14px', height: '14px' }}>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Chennai
            </div>

            <div className="live-indicator">
              <div className="live-pulse"></div>
              Live
            </div>
          </div>
        </header>

        {/* WORKSPACE ELEMENT */}
        <main className="container" style={{ zIndex: 1, position: 'relative' }}>
          <Outlet />
        </main>

        {/* SYSTEM FOOTER */}
        <footer style={{ zIndex: 1, position: 'relative' }}>
          <div className="container">
            <p style={{ margin: 0 }}>&copy; 2026 VayuGuard Air Quality Forecasting System. Fully Verified SaaS Edition.</p>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default Layout;
