const express = require('express');
const { authenticate } = require('../middleware/auth');
const db = require('../db');

const router = express.Router();

// Root summary - convenience endpoint
router.get('/', authenticate, async (req, res) => {
  try {
    const avgRes = await db.query(
      `SELECT AVG(aqi)::float AS avg FROM (
         SELECT DISTINCT ON (city) city, aqi
         FROM aqi_data
         ORDER BY city, recorded_at DESC
       ) s`
    );
    const citiesRes = await db.query(`SELECT DISTINCT city FROM aqi_data`);
    const alertsRes = await db.query(`SELECT COUNT(*)::int AS cnt FROM alerts WHERE is_active = true`);

    const avgAqi = avgRes.rows[0] && avgRes.rows[0].avg ? Number(avgRes.rows[0].avg) : 0;
    const cities = citiesRes.rows.map(r => r.city);
    const alerts = alertsRes.rows[0] ? alertsRes.rows[0].cnt : 0;

    res.json({ avgAqi, cities, alerts, summary: 'Operational' });
  } catch (err) {
    console.error('Analytics / error:', err);
    res.status(500).json({ error: 'Failed to compute analytics summary' });
  }
});

// GET /summary - returns basic KPIs used by the frontend
router.get('/summary', authenticate, async (req, res) => {
  try {
    const avgRes = await db.query(
      `SELECT AVG(aqi)::float AS avg FROM (
         SELECT DISTINCT ON (city) city, aqi
         FROM aqi_data
         ORDER BY city, recorded_at DESC
       ) s`
    );
    const citiesRes = await db.query(`SELECT DISTINCT city FROM aqi_data`);
    const alertsRes = await db.query(`SELECT COUNT(*)::int AS cnt FROM alerts WHERE is_active = true`);

    const avgAqi = avgRes.rows[0] && avgRes.rows[0].avg ? Number(avgRes.rows[0].avg) : 0;
    const cities = citiesRes.rows.map(r => r.city);
    const alerts = alertsRes.rows[0] ? alertsRes.rows[0].cnt : 0;

    res.json({ avgAqi, cities, alerts });
  } catch (err) {
    console.error('Analytics /summary error:', err);
    res.status(500).json({ error: 'Failed to fetch analytics summary' });
  }
});

// GET /hotspots - top cities by latest AQI
router.get('/hotspots', authenticate, async (req, res) => {
  try {
    const hotspotsRes = await db.query(
      `SELECT t.city, t.aqi, t.recorded_at FROM aqi_data t
       INNER JOIN (
         SELECT city, MAX(recorded_at) AS mx FROM aqi_data GROUP BY city
       ) latest ON latest.city = t.city AND latest.mx = t.recorded_at
       ORDER BY t.aqi DESC LIMIT 10`
    );
    res.json({ hotspots: hotspotsRes.rows });
  } catch (err) {
    console.error('Analytics /hotspots error:', err);
    res.status(500).json({ error: 'Failed to fetch hotspots' });
  }
});

// GET /trends - daily average AQI per city for last 7 days
router.get('/trends', authenticate, async (req, res) => {
  try {
    const trendsRes = await db.query(
      `SELECT city, DATE(recorded_at) AS day, AVG(aqi)::float AS avg_aqi
       FROM aqi_data
       WHERE recorded_at >= NOW() - INTERVAL '7 days'
       GROUP BY city, DATE(recorded_at)
       ORDER BY city, day`
    );

    // Group rows by city for frontend convenience
    const grouped = {};
    for (const row of trendsRes.rows) {
      if (!grouped[row.city]) grouped[row.city] = [];
      grouped[row.city].push({ day: row.day, avgAqi: Number(row.avg_aqi) });
    }

    res.json({ trends: grouped });
  } catch (err) {
    console.error('Analytics /trends error:', err);
    res.status(500).json({ error: 'Failed to fetch trends' });
  }
});

module.exports = router;
