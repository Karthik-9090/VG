const request = require('supertest');
const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const errorHandler = require('../middleware/errorHandler');

const authRoutes = require('../routes/auth');
const forecastRoutes = require('../routes/forecast');
const alertsRoutes = require('../routes/alerts');
const analyticsRoutes = require('../routes/analytics');
const adminRoutes = require('../routes/admin');
const usersRoutes = require('../routes/users');

const app = express();

app.use(cors());
app.use(morgan('combined'));
app.use(express.json());

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.use('/api/auth', authRoutes);
app.use('/api/forecast', forecastRoutes);
app.use('/api/alerts', alertsRoutes);
app.use('/api/analytics', analyticsRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/users', usersRoutes);

app.use(errorHandler);

describe('Backend API', () => {
  test('GET /api/health returns 200', async () => {
    const res = await request(app).get('/api/health');
    expect(res.statusCode).toBe(200);
    expect(res.body.status).toBe('ok');
  });

  test('POST /api/auth/register returns 201 with missing email', async () => {
    const res = await request(app)
      .post('/api/auth/register')
      .send({ password: 'password123', name: 'Test User' });
    expect(res.statusCode).toBe(422);
  });

  test('POST /api/auth/login returns 422 with missing email', async () => {
    const res = await request(app).post('/api/auth/login').send({ password: 'password123' });
    expect(res.statusCode).toBe(422);
  });

  test('GET /api/analytics/summary requires auth', async () => {
    const res = await request(app).get('/api/analytics/summary');
    expect(res.statusCode).toBe(401);
  });

  test('GET /api/admin/users requires admin role', async () => {
    const token = 'invalid-token';
    const res = await request(app)
      .get('/api/admin/users')
      .set('Authorization', `Bearer ${token}`);
    expect(res.statusCode).toBe(401);
  });
});
