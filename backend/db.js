const { Pool } = require('pg');
const config = require('./config');

const pool = new Pool(config.db);

pool.on('error', (err) => {
  console.error('Unexpected error on idle client', err);
});

pool.on('connect', (client) => {
  client.on('error', (err) => {
    console.error('Unexpected error on client', err);
  });
});

// Graceful shutdown handler
const gracefulShutdown = async () => {
  try {
    console.log('[DB] Gracefully shutting down connection pool...');
    await pool.end();
    console.log('[DB] Connection pool closed successfully');
  } catch (err) {
    console.error('[DB] Error during pool shutdown:', err);
    process.exit(1);
  }
};

module.exports = {
  query: (text, params) => pool.query(text, params),
  getClient: () => pool.connect(),
  pool,
  gracefulShutdown,
};
