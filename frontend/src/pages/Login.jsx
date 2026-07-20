import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import EnvironmentalBackdrop from '../components/EnvironmentalBackdrop';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const { data } = await authAPI.login(email, password);
      login(data.user, data.token);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Environmental Backdrop background */}
      <EnvironmentalBackdrop leafCount={3} />

      <div className="card premium-glow fade-in-up" style={{ maxWidth: '440px', width: '100%', padding: '40px var(--spacing-lg)', zIndex: 1, position: 'relative' }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%)',
            color: 'white',
            marginBottom: '16px',
            boxShadow: '0 4px 12px rgba(37, 99, 235, 0.2)'
          }}>
            <svg style={{ width: '28px', height: '28px' }} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="white" stroke="white" strokeWidth="1" strokeLinejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h1 style={{ fontSize: '24px', fontWeight: 800, letterSpacing: '-0.5px', marginBottom: '8px' }}>Welcome back</h1>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Log in to monitor live forecasts and analytics</p>
        </div>

        {error && (
          <div className="alert alert-error" style={{ fontSize: '13px', padding: '12px 16px' }}>
            <svg style={{ width: '18px', height: '18px', minWidth: '18px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="input-group" style={{ marginBottom: '12px' }}>
            <label htmlFor="password" style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 700, marginBottom: '8px' }}>PASSWORD</label>
            <div style={{ position: 'relative', border: '1px solid rgba(2,6,23,0.08)', borderRadius: '12px', padding: '8px 10px', display: 'flex', alignItems: 'center', background: 'transparent' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                placeholder=""
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={{
                  padding: '8px 0',
                  border: 'none',
                  outline: 'none',
                  background: 'transparent',
                  width: '100%',
                  fontSize: '14px',
                  color: 'var(--text-primary)'
                }}
              />
            <button
              type="button"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              onClick={() => setShowPassword((s) => !s)}
              style={{
                height: '34px',
                width: '34px',
                padding: '6px',
                border: '1px solid rgba(2,6,23,0.06)',
                background: '#ffffff',
                cursor: 'pointer',
                color: '#475569',
                borderRadius: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              {showPassword ? (
                /* visible: show open eye */
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M1.5 12s4-7.5 10.5-7.5S22.5 12 22.5 12s-4 7.5-10.5 7.5S1.5 12 1.5 12z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              ) : (
                /* hidden: show slashed eye */
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M2 12s4-7.5 10-7.5S22 12 22 12s-2 3.5-6 6.5M9.5 9.5a3 3 0 104 4" />
                  <path d="M2 2l20 20" />
                </svg>
              )}
            </button>
          </div>
        </div>

          <button type="submit" className="button" style={{ width: '100%', height: '44px', marginTop: '8px' }} disabled={loading}>
            {loading ? (
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></span>
                Logging in...
              </span>
            ) : 'Log In'}
          </button>
        </form>

        <div style={{ marginTop: '24px', textAlign: 'center', borderTop: '1px solid var(--border)', paddingTop: '20px' }}>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
            Don't have an account? <Link to="/register" style={{ fontWeight: 600, color: 'var(--primary)' }}>Register here</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
