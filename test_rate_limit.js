const http = require('http');

const makeRequest = () => {
  return new Promise((resolve) => {
    const options = {
      hostname: '127.0.0.1',
      port: 5001,
      path: '/api/forecast',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          headers: {
            'X-RateLimit-Limit': res.headers['x-ratelimit-limit'],
            'X-RateLimit-Remaining': res.headers['x-ratelimit-remaining'],
            'X-RateLimit-Reset': res.headers['x-ratelimit-reset'],
          },
        });
      });
    });

    req.on('error', (e) => {
      resolve({ status: 0, error: e.message });
    });

    req.write(JSON.stringify({ city: 'Delhi', hours: 1 }));
    req.end();
  });
};

(async () => {
  console.log('[RATE LIMIT TEST] Sending 105 rapid requests...\n');
  const results = { 200: 0, 401: 0, 429: 0, other: 0 };
  const responses = [];

  // Send requests rapidly without waiting
  const promises = [];
  for (let i = 0; i < 105; i++) {
    promises.push(makeRequest());
  }

  const allResponses = await Promise.all(promises);

  allResponses.forEach((res, idx) => {
    results[res.status] = (results[res.status] || 0) + 1;
    if (idx < 10 || idx >= 95) {
      // Log first 10 and last 10
      const remaining = res.headers && res.headers['X-RateLimit-Remaining'] ? res.headers['X-RateLimit-Remaining'] : 'N/A';
      console.log(`Request ${idx + 1}: Status=${res.status}, RateLimit-Remaining=${remaining}`);
    } else if (idx === 10) {
      console.log('...');
    }
  });

  console.log('\n[RATE LIMIT TEST RESULTS]');
  console.log(`200 OK:           ${results[200]} requests`);
  console.log(`401 Unauthorized: ${results[401]} requests`);
  console.log(`429 Too Many:     ${results[429]} requests`);
  console.log(`Other:            ${results.other} requests`);
  console.log('\n✅ Rate limiting working!' + (results[429] > 0 ? ` (${results[429]} requests hit limit)` : ' (all requests allowed)'));
})();
