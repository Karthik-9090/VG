import React, { useEffect, useState } from 'react';
import { userAPI } from '../api/client';
import { useAuth } from '../contexts/AuthContext';

function Profile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState('general');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeTab, setActiveTab] = useState('account'); // 'account' or 'health'

  useEffect(() => {
    fetchHealthProfile();
  }, []);

  const fetchHealthProfile = async () => {
    try {
      const { data } = await userAPI.getHealthProfile();
      setProfile(data.profile);
    } catch (err) {
      setError('Failed to load personalized health settings.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    try {
      setError('');
      setSuccess('');
      await userAPI.setHealthProfile(profile);
      setSuccess('Health configuration saved successfully.');
      // Notify other pages (Health Advisory, Dashboard) that profile changed
      window.dispatchEvent(new CustomEvent('profile_updated', { detail: profile }));
    } catch (err) {
      setError('Failed to update health profile preferences.');
    }
  };

  if (loading) {
    return (
      <div className="loading" style={{ minHeight: '60vh' }}>
        <div className="spinner"></div>
        <p>Loading account details...</p>
      </div>
    );
  }

  return (
    <div className="fade-in-up">
      <h1 style={{ fontSize: '26px', fontWeight: 800, letterSpacing: '-0.5px', marginBottom: '4px' }}>Account Settings</h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '24px' }}>
        Manage your profile details, platform roles, and personalized medical warning configurations.
      </p>

      {error && (
        <div className="alert alert-error">
          <svg style={{ width: '20px', height: '20px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          <svg style={{ width: '20px', height: '20px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{success}</span>
        </div>
      )}

      {/* SETTINGS TAB LINKS */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', gap: '20px', marginBottom: '24px' }}>
        <button
          onClick={() => setActiveTab('account')}
          style={{
            padding: '12px 8px',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'account' ? '2px solid var(--primary)' : '2px solid transparent',
            color: activeTab === 'account' ? 'var(--primary)' : 'var(--text-secondary)',
            fontWeight: 600,
            fontSize: '14px',
            cursor: 'pointer',
            transition: 'all var(--transition-fast)'
          }}
        >
          Account Details
        </button>
        <button
          onClick={() => setActiveTab('health')}
          style={{
            padding: '12px 8px',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'health' ? '2px solid var(--primary)' : '2px solid transparent',
            color: activeTab === 'health' ? 'var(--primary)' : 'var(--text-secondary)',
            fontWeight: 600,
            fontSize: '14px',
            cursor: 'pointer',
            transition: 'all var(--transition-fast)'
          }}
        >
          Health Profile Setup
        </button>
      </div>

      {/* ACCOUNT DETAILS TAB CONTENT */}
      {activeTab === 'account' && (
        <div className="card">
          <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '20px' }}>Authentication Details</h2>
          
          <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
            <div style={{ padding: '20px', backgroundColor: 'var(--bg-page)', border: '1px solid var(--border)', borderRadius: '12px' }}>
              <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>Email Address</span>
              <p style={{ margin: '4px 0 0 0', fontWeight: 700, fontSize: '15px', color: 'var(--text-primary)' }}>
                {user?.email || 'user@example.com'}
              </p>
            </div>

            <div style={{ padding: '20px', backgroundColor: 'var(--bg-page)', border: '1px solid var(--border)', borderRadius: '12px' }}>
              <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>System Platform Role</span>
              <p style={{ margin: '6px 0 0 0', fontWeight: 600 }}>
                <span className="badge badge-primary" style={{ fontSize: '11px', padding: '2px 10px' }}>
                  {user?.role || 'Member'}
                </span>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* HEALTH PREFERENCES TAB CONTENT */}
      {activeTab === 'health' && (
        <div className="card">
          <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '12px' }}>Atmospheric Sensitivity Configurations</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '24px' }}>
            VayuGuard utilizes this configuration to dynamically filter outdoor safety risk categories and mask requirements.
          </p>

          <div className="input-group">
            <label htmlFor="health-profile">Personal Wellness Profile</label>
            <select
              id="health-profile"
              value={profile}
              onChange={(e) => setProfile(e.target.value)}
              style={{ height: '44px', fontWeight: 500 }}
            >
              <option value="general">👤 General Population</option>
              <option value="respiratory">🫁 Respiratory Issues</option>
              <option value="cardiac">❤️ Cardiac Issues</option>
              <option value="children">👶 Children</option>
              <option value="elderly">👴 Elderly</option>
            </select>
          </div>

          <div style={{
            padding: '16px',
            backgroundColor: 'var(--primary-light)',
            borderLeft: '4px solid var(--primary)',
            borderRadius: '8px',
            marginTop: '20px',
            fontSize: '13px',
            color: '#1e40af',
            lineHeight: '1.5'
          }}>
            <strong>💡 Dynamic Safety Recommendations</strong>
            <div style={{ marginTop: '4px' }}>
              Once saved, the system will instantly prioritize recommendations corresponding to your profile category on both the Dashboard and Health Advisory panels.
            </div>
          </div>

          <button
            onClick={handleSaveProfile}
            className="button"
            style={{ marginTop: '24px', minWidth: '160px', height: '42px' }}
          >
            <svg style={{ width: '18px', height: '18px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2v-9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
            </svg>
            Save Preferences
          </button>
        </div>
      )}
    </div>
  );
}

export default Profile;
