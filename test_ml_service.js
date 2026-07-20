const http = require('http');

const options = {
  hostname: '127.0.0.1',
  port: 8001,
  path: '/forecast',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  }
};

const req = http.request(options, (res) => {
  console.log(`Status: ${res.statusCode}`);
  let data = '';
  
  res.on('data', (chunk) => {
    data += chunk;
  });
  
  res.on('end', () => {
    console.log('Response:', data);
  });
});

req.on('error', (err) => {
  console.error('Error:', err.message);
});

const payload = {
  city: 'Chennai',
  aqi: 100,
  pm2_5: 50,
  pm10: 75,
  no2: 30,
  so2: 20,
  co: 1,
  o3: 50
};

req.write(JSON.stringify(payload));
req.end();

console.log('Sent request to ML service...');
