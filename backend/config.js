require('dotenv').config();

module.exports = {
  port: process.env.PORT || 5001,
  db: {
    host: process.env.DB_HOST || '127.0.0.1',
    port: process.env.DB_PORT || 5432,
    database: process.env.DB_NAME || 'vayuguard',
    user: process.env.DB_USER || 'vayuguard_user',
    password: process.env.DB_PASSWORD || 'vayuguard_pass',
    // Connection pool configuration for high concurrency
    max: parseInt(process.env.DB_POOL_MAX || '100', 10),           // Max connections (increased for background tasks)
    min: parseInt(process.env.DB_POOL_MIN || '10', 10),            // Min warm connections (increased)
    idleTimeoutMillis: parseInt(process.env.DB_POOL_IDLE_TIMEOUT || '30000', 10),           // 30 seconds
    connectionTimeoutMillis: parseInt(process.env.DB_POOL_CONNECTION_TIMEOUT || '5000', 10), // 5 seconds
    statement_timeout: 30000,  // Query timeout: 30 seconds
    query_timeout: 30000,      // Query timeout: 30 seconds
  },
  jwt: {
    secret: process.env.JWT_SECRET || 'vayuguard-secret',
    expiresIn: '24h',
  },
  mlServiceUrl: process.env.ML_SERVICE_URL || 'http://127.0.0.1:8001',
  nodeEnv: process.env.NODE_ENV || 'development',
  // Security settings
  frontendUrl: process.env.FRONTEND_URL || 'http://localhost:3000',
  tlsCertPath: process.env.TLS_CERT_PATH || null,
  tlsKeyPath: process.env.TLS_KEY_PATH || null,
};
