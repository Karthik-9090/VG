const express = require('express');
const { authenticate, authorize } = require('../middleware/auth');

const router = express.Router();

router.get('/users', authenticate, authorize(['admin']), async (req, res) => {
  res.json({ users: [] });
});

router.get('/statistics', authenticate, authorize(['admin']), async (req, res) => {
  res.json({ stats: {} });
});

module.exports = router;
