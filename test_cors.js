const http = require('http');

const testOrigins = [
  { origin: 'http://localhost:3000', expected: 'allowed' },
  { origin: 'http://127.0.0.1:3000', expected: 'allowed' },
  { origin: 'http://example.com:3000', expected: 'denied' },
  { origin: 'http://malicious.site:3000', expected: 'denied' },
];

const makeRequest = (origin) => {
  return new Promise((resolve) => {
    const options = {
      hostname: '127.0.0.1',
      port: 5001,
      path: '/api/forecast',
      method: 'OPTIONS',
      headers: {
        'Origin': origin,
        'Access-Control-Request-Method': 'POST',
      },
    };

    const req = http.request(options, (res) => {
      resolve({
        origin,
        status: res.statusCode,
        corsHeader: res.headers['access-control-allow-origin'] || 'NOT SET',
      });
    });

    req.on('error', (e) => {
      resolve({ origin, status: 0, error: e.message, corsHeader: 'ERROR' });
    });

    req.end();
  });
};

(async () => {
  console.log('[CORS TEST] Testing allowed/denied origins...\n');

  const results = await Promise.all(testOrigins.map(t => makeRequest(t.origin)));

  results.forEach((res, idx) => {
    const expected = testOrigins[idx].expected;
    const allowed = res.corsHeader && res.corsHeader !== 'NOT SET';
    const status = allowed === (expected === 'allowed') ? '✅' : '❌';
    console.log(`${status} Origin: ${res.origin}`);
    console.log(`   Access-Control-Allow-Origin: ${res.corsHeader}`);
    console.log(`   Expected: ${expected}`);
  });
})();
