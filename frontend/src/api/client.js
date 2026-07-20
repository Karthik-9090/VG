import axios from 'axios';

const API_BASE = '/api';

const client = axios.create({
  baseURL: API_BASE
});

// Add token to request headers
client.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  register: (email, password, name) =>
    client.post('/auth/register', { email, password, name }),

  login: (email, password) =>
    client.post('/auth/login', { email, password })
};

export const forecastAPI = {
  getCurrentAqi: (city = 'Chennai') =>
    client.get('/forecast/current-aqi', { params: { city } }),

  getForecast: (city, horizon = 24) =>
    client.post(`/forecast?horizon=${encodeURIComponent(horizon)}`, { city, horizon }),

  getHealthRisk: (city = 'Chennai', profile = 'general', horizon = 24) =>
    client.post('/forecast/health-risk', { city, profile, horizon })
};

export const alertsAPI = {
  getAlerts: () => client.get('/alerts'),
  createAlert: (city, threshold) =>
    client.post('/alerts', { city, threshold }),
  updateAlert: (id, data) => client.put(`/alerts/${id}`, data),
  deleteAlert: (id) => client.delete(`/alerts/${id}`)
};

export const analyticsAPI = {
  getSummary: () => client.get('/analytics/summary'),
  getHotspots: () => client.get('/analytics/hotspots'),
  getTrends: () => client.get('/analytics/trends')
};

export const adminAPI = {
  getUsers: () => client.get('/admin/users'),
  getStatistics: () => client.get('/admin/statistics')
};

export const userAPI = {
  getProfile: () => client.get('/users/me'),
  getHealthProfile: () => client.get('/users/health-profile'),
  setHealthProfile: (profile) =>
    client.post('/users/health-profile', { profile })
};

export default client;
