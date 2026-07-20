const express = require('express');
const { authenticate } = require('../middleware/auth');

const router = express.Router();

router.get('/me', authenticate, async (req, res) => {
  res.json({ id: req.user.sub, role: req.user.role });
});

router.get('/health-profile', authenticate, async (req, res) => {
  res.json({ profile: 'general', id: req.user.sub });
});

router.post('/health-profile', authenticate, async (req, res) => {
  const { profile } = req.body;
  res.json({ profile, saved: true });
});

module.exports = router;
