import React, { useEffect, useState } from 'react';
import { adminAPI } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';

function Admin() {
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { user } = useAuth();

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchAdminData();
    }
  }, [user]);

  const fetchAdminData = async () => {
    try {
      const [usersRes, statsRes] = await Promise.all([
        adminAPI.getUsers(),
        adminAPI.getStatistics()
      ]);
      setUsers(usersRes.data.users || []);
      setStats(statsRes.data.stats || {});
    } catch (err) {
      setError('Failed to load system administrative metrics.');
    } finally {
      setLoading(false);
    }
  };

  if (user?.role !== 'admin') {
    return <Navigate to="/" />;
  }

  if (loading) {
    return (
      <div className="loading" style={{ minHeight: '60vh' }}>
        <div className="spinner"></div>
        <p>Loading administrative dashboard...</p>
      </div>
    );
  }

  return (
    <div className="fade-in-up">
      <h1 style={{ fontSize: '26px', fontWeight: 800, letterSpacing: '-0.5px', marginBottom: '4px' }}>Administrative Console</h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '24px' }}>
        System-level metrics, operational analytics database telemetry, and registered account audits.
      </p>

      {error && (
        <div className="alert alert-error">
          <svg style={{ width: '20px', height: '20px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* STATS CONFIG CARD */}
      <div className="grid">
        <div className="card">
          <div className="card-header" style={{ marginBottom: '16px' }}>
            <h2>System Health & Cluster Statistics</h2>
            <span className="live-indicator">
              <div className="live-pulse"></div>
              Nominal
            </span>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px', marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Active Platform Users</span>
              <span style={{ fontWeight: 700 }}>{users.length}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Atmospheric Ingest Status</span>
              <span style={{ fontWeight: 600, color: 'var(--success)' }}>Operational (200 OK)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Cluster Telemetries</span>
              <span style={{ fontWeight: 600, color: 'var(--primary)' }}>3 Active Stations</span>
            </div>
          </div>

          <h3 style={{ fontSize: '13px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '8px' }}>
            Raw Telemetry Metadata
          </h3>
          <pre style={{
            padding: '12px',
            backgroundColor: 'var(--bg-page)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            fontSize: '11px',
            color: 'var(--text-secondary)',
            maxHeight: '120px',
            overflowY: 'auto'
          }}>
            {JSON.stringify(stats, null, 2)}
          </pre>
        </div>

        {/* REGISTERED USERS MANAGEMENT CARD */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header" style={{ marginBottom: '20px' }}>
            <h2>User Account Directory</h2>
            <span className="badge badge-info">{users.length} Accounts Registered</span>
          </div>

          {users.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">👥</div>
              <h3>No Directory Data</h3>
              <p>No registered user accounts retrieved from database registry.</p>
            </div>
          ) : (
            <div className="table-container" style={{ margin: 0 }}>
              <table>
                <thead>
                  <tr>
                    <th>Account ID</th>
                    <th>Email Address</th>
                    <th>Platform Role</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-muted)' }}>#{u.id}</td>
                      <td style={{ fontWeight: 500 }}>{u.email}</td>
                      <td>
                        <span className={`badge ${u.role === 'admin' ? 'badge-danger' : 'badge-primary'}`} style={{ padding: '2px 8px', fontSize: '10px' }}>
                          {u.role}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Admin;
