const express = require('express');
const { body, validationResult, query } = require('express-validator');
// Forecast endpoints are intentionally public; authentication removed to allow
// unauthenticated dashboard access (frontend will include tokens when available).
const forecastService = require('../services/forecastService');

const router = express.Router();

router.get('/current-aqi', [query('city').optional().isString()], async (req, res, next) => {
  try {
    const city = req.query.city || 'Chennai';
    const result = await forecastService.getCurrentAqi(city);
    res.json(result);
  } catch (err) {
    next(err);
  }
});

router.post(
  '/',
  [body('city').optional().isString(), body('horizon').optional().isInt({ min: 1, max: 72 })],
  async (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      const onlyInvalidCity = errors.array().every((error) => error.path === 'city');
      if (!onlyInvalidCity) {
        return res.status(422).json({ errors: errors.array() });
      }
    }

    try {
      const city = req.body?.city || 'Chennai';
      const requestedHorizon = Number(req.body?.horizon ?? req.query?.horizon ?? req.headers['x-horizon'] ?? 24);
      const horizon = Number.isFinite(requestedHorizon)
        ? Math.max(1, Math.min(72, requestedHorizon))
        : 24;
      console.log('[ROUTE] /api/forecast request body:', JSON.stringify(req.body));
      console.log('[ROUTE] /api/forecast query:', req.query);
      console.log('[ROUTE] /api/forecast headers x-horizon:', req.headers['x-horizon']);
      console.log('[ROUTE] /api/forecast parsed horizon:', horizon);
      const result = await forecastService.getForecast(city, horizon);
      try {
        console.log('[ROUTE] /api/forecast response horizon:', result.horizon, 'timeseries:', (result.forecast_timeseries && result.forecast_timeseries.length) || (result.forecast_values && result.forecast_values.length));
      } catch (e) {
        console.log('[ROUTE] /api/forecast response: <unserializable>');
      }
      res.json(result);
    } catch (err) {
      next(err);
    }
  }
);

router.post(
  '/health-risk',
  [body('city').optional().isString(), body('profile').optional().isString(), body('horizon').optional().isInt({ min: 1, max: 72 })],
  async (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(422).json({ errors: errors.array() });
    }

    try {
      const city = req.body?.city || 'Chennai';
      const profile = req.body?.profile || 'general';
      const horizon = req.body?.horizon || 24;
      const result = await forecastService.getHealthRisk(city, profile, horizon);
      res.json(result);
    } catch (err) {
      next(err);
    }
  }
);

module.exports = router;
