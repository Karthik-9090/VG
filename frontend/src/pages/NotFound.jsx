import React from 'react';
import { Link } from 'react-router-dom';

function NotFound() {
  return (
    <div style={{
      minHeight: '80vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      textAlign: 'center'
    }}>
      <div className="card" style={{ maxWidth: '480px', width: '100%', padding: '48px 32px' }}>
        <div style={{
          fontSize: '72px',
          fontWeight: 800,
          background: 'linear-gradient(135deg, var(--danger) 0%, var(--primary) 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          lineHeight: 1.1,
          marginBottom: '16px'
        }}>
          404
        </div>
        <h2 style={{ fontSize: '22px', fontWeight: 800, marginBottom: '8px', letterSpacing: '-0.3px' }}>Page Not Found</h2>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '32px' }}>
          The page you're looking for doesn't exist or has been moved to a new address.
        </p>
        <Link to="/" className="button" style={{ width: '100%', height: '44px' }}>
          <svg style={{ width: '18px', height: '18px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Go Back to Dashboard
        </Link>
      </div>
    </div>
  );
}

export default NotFound;
