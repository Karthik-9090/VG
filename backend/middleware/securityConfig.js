/**
 * Security Configuration
 * Handles HTTPS/TLS, CORS, and security validations
 */

const fs = require('fs');
const path = require('path');

// Validate required environment variables
const validateSecurityEnvVars = () => {
  const required = [
    'DB_HOST',
    'DB_PORT',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
    'JWT_SECRET',
    'ML_SERVICE_URL'
  ];
  
  const missing = [];
  const warnings = [];
  
  required.forEach(envVar => {
    if (!process.env[envVar]) {
      missing.push(envVar);
    }
  });
  
  // Warnings for weak secrets
  if (process.env.JWT_SECRET === 'vayuguard-secret' || !process.env.JWT_SECRET) {
    warnings.push('JWT_SECRET is using default/weak value - set strong secret in production');
  }
  
  if (process.env.NODE_ENV === 'production' && !process.env.FRONTEND_URL) {
    warnings.push('FRONTEND_URL not set in production - CORS restricted to localhost');
  }
  
  return { missing, warnings };
};

// Get HTTPS/TLS configuration
const getHttpsConfig = () => {
  const certPath = process.env.TLS_CERT_PATH;
  const keyPath = process.env.TLS_KEY_PATH;
  
  if (!certPath || !keyPath) {
    return null; // HTTP only
  }
  
  try {
    return {
      cert: fs.readFileSync(certPath),
      key: fs.readFileSync(keyPath)
    };
  } catch (err) {
    console.error(`[SECURITY] Failed to load TLS certificates: ${err.message}`);
    return null;
  }
};

// Get CORS allowed origins
const getAllowedOrigins = () => {
  const nodeEnv = process.env.NODE_ENV || 'development';
  const frontendUrl = process.env.FRONTEND_URL;
  
  const defaultOrigins = {
    development: ['http://localhost:3000', 'http://127.0.0.1:3000'],
    staging: [frontendUrl || 'https://staging.vayuguard.com'],
    production: [frontendUrl || 'https://vayuguard.com']
  };
  
  return defaultOrigins[nodeEnv] || defaultOrigins.development;
};

module.exports = {
  validateSecurityEnvVars,
  getHttpsConfig,
  getAllowedOrigins,
  RATE_LIMIT: 100, // requests per minute
  RATE_LIMIT_WINDOW: 60 * 1000, // 1 minute
};
