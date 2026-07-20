const express = require('express');
const { body, validationResult } = require('express-validator');
const authService = require('../services/authService');

const router = express.Router();

function getBodyValue(req, field) {
  if (!req.body || typeof req.body !== 'object') {
    return undefined;
  }

  const value = req.body[field];
  return typeof value === 'string' ? value.trim() : value;
}

router.post(
  '/register',
  [
    body('email').optional().isEmail().normalizeEmail(),
    body('password').optional().isLength({ min: 8 }).trim(),
    body('name').optional().notEmpty().trim(),
  ],
  async (req, res, next) => {
    try {
      const email = getBodyValue(req, 'email');
      const password = getBodyValue(req, 'password');
      const name = getBodyValue(req, 'name');

      if (!email || !password || !name) {
        return res.status(422).json({ error: 'Email, password, and name are required' });
      }

      const result = await authService.register(email, password, name);
      res.status(201).json(result);
    } catch (err) {
      next(err);
    }
  }
);

router.post(
  '/login',
  [body('email').optional().isString(), body('password').optional().isString()],
  async (req, res, next) => {
    try {
      const email = getBodyValue(req, 'email') || req.query?.email;
      const password = getBodyValue(req, 'password') || req.query?.password;

      if (!email || !password) {
        return res.status(422).json({ error: 'Email and password are required' });
      }

      const result = await authService.login(email, password);
      res.json(result);
    } catch (err) {
      next(err);
    }
  }
);

module.exports = router;
