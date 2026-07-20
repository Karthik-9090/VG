const http = require('http');
const payload = JSON.stringify({ email: 'demo@vayuguard.com', password: 'Demo@123' });
const req = http.request({
  host: '127.0.0.1',
  port: 5000,
  path: '/api/auth/login',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(payload)
  }
}, (res) => {
  let body = '';
  res.on('data', (chunk) => body += chunk);
  res.on('end', () => {
    console.log('status', res.statusCode);
    console.log(body);
  });
});
req.on('error', (err) => {
  console.error(err);
  process.exit(1);
});
req.write(payload);
req.end();
