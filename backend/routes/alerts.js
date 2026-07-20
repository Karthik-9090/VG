const express = require('express');
const { body, validationResult } = require('express-validator');
const { authenticate } = require('../middleware/auth');
const db = require('../db');

const router = express.Router();

// Get all alerts for the current user
router.get('/', authenticate, async (req, res, next) => {
  try {
    const userId = req.user.sub;
    const result = await db.query(
      'SELECT id, city, threshold, is_active, created_at FROM alerts WHERE user_id = $1 AND is_active = true ORDER BY created_at DESC',
      [userId]
    );
    
    res.json({ alerts: result.rows });
  } catch (err) {
    next(err);
  }
});

// Create a new alert
router.post(
  '/',
  authenticate,
  [
    body('city').notEmpty().isString(),
    body('threshold').isInt({ min: 0, max: 500 })
  ],
  async (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(422).json({ errors: errors.array() });
    }

    try {
      const userId = req.user.sub;
      const { city, threshold } = req.body;
      
      const result = await db.query(
        'INSERT INTO alerts (user_id, city, alert_type, comparison, threshold, is_active) VALUES ($1, $2, $3, $4, $5, true) RETURNING id, city, threshold, is_active, created_at',
        [userId, city, 'aqi_threshold', 'gt', threshold]
      );
      
      const alert = result.rows[0];
      res.status(201).json(alert);
    } catch (err) {
      next(err);
    }
  }
);

// Update an alert
router.put(
  '/:id',
  authenticate,
  [body('threshold').optional().isInt({ min: 0, max: 500 })],
  async (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(422).json({ errors: errors.array() });
    }

    try {
      const { id } = req.params;
      const userId = req.user.sub;
      const { threshold } = req.body;
      
      const result = await db.query(
        'UPDATE alerts SET threshold = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2 AND user_id = $3 RETURNING id, city, threshold, is_active, created_at',
        [threshold || null, id, userId]
      );
      
      if (result.rows.length === 0) {
        const err = new Error('Alert not found');
        err.statusCode = 404;
        throw err;
      }
      
      res.json(result.rows[0]);
    } catch (err) {
      next(err);
    }
  }
);

// Delete an alert (soft delete by marking as inactive)
router.delete('/:id', authenticate, async (req, res, next) => {
  try {
    const { id } = req.params;
    const userId = req.user.sub;
    
    const result = await db.query(
      'UPDATE alerts SET is_active = false, updated_at = CURRENT_TIMESTAMP WHERE id = $1 AND user_id = $2 RETURNING id',
      [id, userId]
    );
    
    if (result.rows.length === 0) {
      const err = new Error('Alert not found');
      err.statusCode = 404;
      throw err;
    }
    
    res.status(204).send();
  } catch (err) {
    next(err);
  }
});

module.exports = router;
