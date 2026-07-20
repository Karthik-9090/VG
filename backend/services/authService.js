const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const db = require('../db');
const config = require('../config');

const SALT_ROUNDS = 12;

function normalizeEmail(email) {
  return typeof email === 'string' ? email.trim().toLowerCase() : email;
}

async function register(email, password, name) {
  const normalizedEmail = normalizeEmail(email);

  // Check if user exists
  const existing = await db.query('SELECT id FROM users WHERE email = $1', [normalizedEmail]);
  if (existing.rows.length) {
    const err = new Error('Email already registered');
    err.statusCode = 409;
    throw err;
  }

  // Hash password
  const passwordHash = await bcrypt.hash(password, SALT_ROUNDS);

  // Insert user
  const result = await db.query(
    'INSERT INTO users (email, password_hash, name, role) VALUES ($1, $2, $3, $4) RETURNING id, email, name, role',
    [normalizedEmail, passwordHash, name, 'user']
  );

  const user = result.rows[0];
  const token = jwt.sign({ sub: user.id, role: user.role }, config.jwt.secret, {
    expiresIn: config.jwt.expiresIn,
  });

  return { user, token };
}

async function login(email, password) {
  const normalizedEmail = normalizeEmail(email);
  const result = await db.query('SELECT id, email, password_hash, name, role FROM users WHERE email = $1', [
    normalizedEmail,
  ]);

  if (!result.rows.length) {
    const err = new Error('Invalid credentials');
    err.statusCode = 401;
    throw err;
  }

  const user = result.rows[0];
  const valid = await bcrypt.compare(password, user.password_hash);

  if (!valid) {
    const err = new Error('Invalid credentials');
    err.statusCode = 401;
    throw err;
  }

  const token = jwt.sign({ sub: user.id, role: user.role }, config.jwt.secret, {
    expiresIn: config.jwt.expiresIn,
  });

  return { user: { id: user.id, email: user.email, name: user.name, role: user.role }, token };
}

module.exports = { register, login };
