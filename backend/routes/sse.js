const express = require('express');
const jwt = require('jsonwebtoken');
const config = require('../config');
const forecastService = require('../services/forecastService');

const router = express.Router();

// Server-Sent Events endpoint for AQI updates
// Accepts token via query param `token` or Authorization header `Bearer <token>`
router.get('/aqi', async (req, res) => {
  try {
    const token = req.query.token || (req.headers.authorization && req.headers.authorization.split(' ')[1]);
    if (!token) return res.status(401).json({ error: 'Missing token' });

    let decoded;
    try {
      decoded = jwt.verify(token, config.jwt.secret);
    } catch (err) {
      return res.status(401).json({ error: 'Invalid token' });
    }

    // SSE headers
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive'
    });

    // Ensure the underlying socket doesn't time out and enable keep-alive
    try {
      if (res.socket && typeof res.socket.setKeepAlive === 'function') {
        res.socket.setKeepAlive(true, 60000);
      }
      if (res.socket && typeof res.socket.setTimeout === 'function') {
        res.socket.setTimeout(0); // disable timeout
      }
    } catch (e) {
      console.warn('[SSE] could not configure socket keepalive/timeout:', e.message);
    }

    // Helper to send AQI payload with debug logging
    const sendAqi = async () => {
      try {
        const city = req.query.city || 'Chennai';
        const data = await forecastService.getCurrentAqi(city);
        const payload = { data, ts: new Date().toISOString() };
        const chunk = `data: ${JSON.stringify(payload)}\n\n`;
        // Debug log
        console.debug(`[SSE] sending chunk to ${req.ip || req.connection.remoteAddress}: ${chunk.length} bytes`);
        res.write(chunk);
      } catch (err) {
        console.error('[SSE] sendAqi error:', err);
        try {
          res.write(`event: error\ndata: ${JSON.stringify({ error: err.message })}\n\n`);
        } catch (e) {
          console.error('[SSE] failed to write error chunk to client:', e.message);
        }
      }
    };

    // Send initial data immediately
    await sendAqi();

    // Send updates every 5 seconds
    const interval = setInterval(sendAqi, 5000);
    // Send a lightweight comment heartbeat every 15s to keep proxies from closing idle connections
    const heartbeat = setInterval(() => {
      try {
        res.write(`: heartbeat\n\n`);
        console.debug(`[SSE] heartbeat sent to ${req.ip || req.connection.remoteAddress}`);
      } catch (e) {
        console.error('[SSE] heartbeat write error:', e.message);
      }
    }, 15000);

    // Clean up when client disconnects
    req.on('close', () => {
      console.log(`[SSE] client disconnected ${req.ip || req.connection.remoteAddress}`);
      clearInterval(interval);
      clearInterval(heartbeat);
    });
    req.on('error', (err) => {
      console.error('[SSE] request error:', err);
    });
    res.on('error', (err) => {
      console.error('[SSE] response error:', err);
    });
  } catch (err) {
    console.error('SSE /aqi error:', err);
    // If headers not yet sent
    if (!res.headersSent) res.status(500).json({ error: 'SSE error' });
  }
});

module.exports = router;
