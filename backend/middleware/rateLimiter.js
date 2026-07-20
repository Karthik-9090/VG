/**
 * Rate Limiter Middleware
 * Enforces 100 requests per minute per IP address
 */

const rateLimitStore = new Map();
const RATE_LIMIT = 100; // requests per minute
const WINDOW_MS = 60 * 1000; // 1 minute

const rateLimiter = (req, res, next) => {
  const clientIp = req.ip || req.socket.remoteAddress || 'unknown';
  const now = Date.now();
  
  if (!rateLimitStore.has(clientIp)) {
    rateLimitStore.set(clientIp, []);
  }
  
  const requests = rateLimitStore.get(clientIp);
  
  // Remove old requests outside the window
  const validRequests = requests.filter(timestamp => now - timestamp < WINDOW_MS);
  
  if (validRequests.length >= RATE_LIMIT) {
    return res.status(429).json({
      error: 'Too many requests',
      message: `Rate limit exceeded: ${RATE_LIMIT} requests per minute per IP`,
      retryAfter: Math.ceil((validRequests[0] + WINDOW_MS - now) / 1000)
    });
  }
  
  validRequests.push(now);
  rateLimitStore.set(clientIp, validRequests);
  
  // Set rate limit headers
  res.set('X-RateLimit-Limit', RATE_LIMIT);
  res.set('X-RateLimit-Remaining', RATE_LIMIT - validRequests.length);
  res.set('X-RateLimit-Reset', new Date(now + WINDOW_MS).toISOString());
  
  next();
};

// Cleanup old entries every 5 minutes
setInterval(() => {
  const now = Date.now();
  for (const [ip, requests] of rateLimitStore.entries()) {
    const validRequests = requests.filter(timestamp => now - timestamp < WINDOW_MS);
    if (validRequests.length === 0) {
      rateLimitStore.delete(ip);
    } else {
      rateLimitStore.set(ip, validRequests);
    }
  }
}, 5 * 60 * 1000);

module.exports = rateLimiter;
