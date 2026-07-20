const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const promClient = require('prom-client');
const config = require('./config');
const db = require('./db');
const errorHandler = require('./middleware/errorHandler');
const rateLimiter = require('./middleware/rateLimiter');
const { validateSecurityEnvVars, getAllowedOrigins, getHttpsConfig } = require('./middleware/securityConfig');
const https = require('https');
const fs = require('fs');

// Validate security environment variables at startup
const { missing, warnings } = validateSecurityEnvVars();
if (missing.length > 0) {
  console.error(`[SECURITY] Missing required environment variables: ${missing.join(', ')}`);
  process.exit(1);
}
warnings.forEach(warn => console.warn(`[SECURITY] WARNING: ${warn}`));

// Increase maximum concurrent HTTP connections
// Default is 10, we need much higher for concurrent load
const http = require('http');
http.globalAgent.maxSockets = 500;
http.globalAgent.maxFreeSockets = 100;
http.globalAgent.keepAliveTimeout = 60000;

// Add connection pool status logging
const logPoolStatus = () => {
  const { pool } = db;
  const waitingCount = pool.waitingCount || 0;
  const idleCount = pool.idleCount || 0;
  const totalCount = pool.totalCount || 0;
  
  if (waitingCount > 0) {
    console.warn(`[POOL STATUS] Waiting: ${waitingCount}, Idle: ${idleCount}, Total: ${totalCount}`);
  }
};

// Log pool status every 5 seconds if there are queued requests
setInterval(logPoolStatus, 5000);

const authRoutes = require('./routes/auth');
const forecastRoutes = require('./routes/forecast');
const alertsRoutes = require('./routes/alerts');
const analyticsRoutes = require('./routes/analytics');
const adminRoutes = require('./routes/admin');
const usersRoutes = require('./routes/users');
const sseRoutes = require('./routes/sse');

const app = express();

// CORS Configuration - Restrict to production frontend URL
const corsOptions = {
  origin: getAllowedOrigins(),
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  maxAge: 86400, // 24 hours
  optionsSuccessStatus: 200
};

console.log(`[SECURITY] CORS allowed origins: ${corsOptions.origin.join(', ')}`);

// Middleware
app.use(cors(corsOptions));
app.use(morgan('combined'));
app.use(express.json());

// Debug: log POST bodies to /api/forecast to aid troubleshooting
app.use('/api/forecast', (req, res, next) => {
  if (req.method === 'POST') {
    try {
      console.log('[DEBUG] /api/forecast POST body:', JSON.stringify(req.body));
    } catch (e) {
      console.log('[DEBUG] /api/forecast POST body: <unserializable>');
    }
  }
  next();
});

// Security: Rate limiting (100 requests/min per IP)
app.use(rateLimiter);

// Security: Content Security Policy headers
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  next();
});

// Prometheus metrics
const httpRequestDuration = new promClient.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
});

app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    httpRequestDuration.observe({ method: req.method, route: req.path, status_code: res.statusCode }, duration);
  });
  next();
});

// Health check
app.get('/api/health', async (req, res) => {
  try {
    await db.query('SELECT 1');
    res.json({ status: 'ok' });
  } catch (err) {
    res.status(503).json({ status: 'error', error: err.message });
  }
});

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/forecast', forecastRoutes);
app.use('/api/alerts', alertsRoutes);
app.use('/api/analytics', analyticsRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/users', usersRoutes);
app.use('/api/sse', sseRoutes);

// Metrics endpoint
app.get('/api/metrics', async (req, res) => {
  res.set('Content-Type', promClient.register.contentType);
  res.end(await promClient.register.metrics());
});

// Error handler
app.use(errorHandler);

const port = process.env.PORT || 8000;
const host = process.env.HOST || '0.0.0.0';
const httpsConfig = getHttpsConfig();

let server;
if (httpsConfig) {
  server = https.createServer(httpsConfig, app);
  console.log('[SECURITY] HTTPS enabled with TLS certificates');
} else {
  server = http.createServer(app);
  console.log('[SECURITY] HTTPS disabled (no TLS certificates provided)');
}

server.listen(port, host, 2048, () => {
  const protocol = httpsConfig ? 'HTTPS' : 'HTTP';
  console.log(`[SERVER] backend listening on ${host}:${port} (${protocol})`);
  console.log(`[POOL] Configuration: max=${config.db.max}, min=${config.db.min}`);
  console.log(`[SERVER] Listen backlog: 2048 (high concurrency mode)`);
});

// Increase max connection listeners (prevent memory leak warnings)
server.setMaxListeners(0);

// Graceful shutdown handlers
const shutdown = async (signal) => {
  console.log(`[SERVER] ${signal} received, starting graceful shutdown...`);
  
  // Stop accepting new connections
  server.close(async () => {
    console.log('[SERVER] HTTP server closed');
    
    // Close database pool
    await db.gracefulShutdown();
    
    // Exit process
    process.exit(0);
  });
  
  // Force shutdown after 10 seconds
  setTimeout(() => {
    console.error('[SERVER] Forced shutdown (timeout)');
    process.exit(1);
  }, 10000);
};

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));
