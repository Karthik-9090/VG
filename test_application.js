const http = require('http');

// Test users to create
const testUsers = [
  { email: 'admin@vayuguard.com', password: 'Admin@123', name: 'Admin User' },
  { email: 'demo@vayuguard.com', password: 'Demo@123', name: 'Demo User' },
  { email: 'user@vayuguard.com', password: 'User@123', name: 'Regular User' }
];

// Make HTTP request
function makeRequest(method, path, data = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'localhost',
      port: 5001,
      path: path,
      method: method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(body);
          resolve({ status: res.statusCode, body: json, headers: res.headers });
        } catch (e) {
          resolve({ status: res.statusCode, body: body, headers: res.headers });
        }
      });
    });

    req.on('error', reject);
    if (data) req.write(JSON.stringify(data));
    req.end();
  });
}

async function runTests() {
  console.log('VayuGuard Application Test Suite');
  console.log('================================\n');

  try {
    // Test 1: Health check
    console.log('[1] Testing Backend Health...');
    const health = await makeRequest('GET', '/api/health');
    if (health.status === 200) {
      console.log('✓ Backend Health: PASS');
      console.log(`  Response: ${JSON.stringify(health.body)}\n`);
    } else {
      console.log(`✗ Backend Health: FAIL (Status ${health.status})\n`);
    }

    // Test 2: Create test users
    console.log('[2] Creating Test Users...');
    const tokens = {};
    for (const user of testUsers) {
      const result = await makeRequest('POST', '/api/auth/register', {
        email: user.email,
        password: user.password,
        name: user.name
      });

      if (result.status === 201 || result.status === 409) { // 409 = already exists
        console.log(`✓ User created/exists: ${user.email}`);
        if (result.body.token) tokens[user.email] = result.body.token;
      } else {
        console.log(`✗ Failed to create user: ${user.email} (Status ${result.status})`);
      }
    }
    console.log();

    // Test 3: Login test
    console.log('[3] Testing Login...');
    const login = await makeRequest('POST', '/api/auth/login', {
      email: 'user@vayuguard.com',
      password: 'User@123'
    });

    if (login.status === 200 && login.body.token) {
      console.log('✓ Login: PASS');
      console.log(`  Token: ${login.body.token.substring(0, 20)}...\n`);
      tokens['user@vayuguard.com'] = login.body.token;
    } else {
      console.log(`✗ Login: FAIL (Status ${login.status})\n`);
    }

    // Test 4: Get user profile
    if (tokens['user@vayuguard.com']) {
      console.log('[4] Testing Get User Profile...');
      const userToken = tokens['user@vayuguard.com'];
      const profile = await makeRequest('GET', '/api/users/profile', null);
      profile.headers['Authorization'] = `Bearer ${userToken}`;

      // Re-make request with auth
      const options = {
        hostname: 'localhost',
        port: 5001,
        path: '/api/users/profile',
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${userToken}`
        }
      };

      const profileResult = await new Promise((resolve, reject) => {
        const req = http.request(options, (res) => {
          let body = '';
          res.on('data', chunk => body += chunk);
          res.on('end', () => {
            try {
              resolve({ status: res.statusCode, body: JSON.parse(body) });
            } catch(e) {
              resolve({ status: res.statusCode, body: body });
            }
          });
        });
        req.on('error', reject);
        req.end();
      });

      if (profileResult.status === 200) {
        console.log('✓ Get Profile: PASS');
        console.log(`  User: ${profileResult.body.email}\n`);
      } else {
        console.log(`✗ Get Profile: FAIL (Status ${profileResult.status})\n`);
      }
    }

    // Test 5: AQI Data endpoint
    console.log('[5] Testing AQI Data Endpoints...');
    const aqiCities = await makeRequest('GET', '/api/aqi/cities');
    if (aqiCities.status === 200) {
      console.log('✓ Get Cities: PASS');
    } else {
      console.log(`✗ Get Cities: FAIL (Status ${aqiCities.status})`);
    }

    const aqiChennai = await makeRequest('GET', '/api/aqi/city/Chennai');
    if (aqiChennai.status === 200) {
      console.log('✓ Get Chennai AQI: PASS');
    } else {
      console.log(`✗ Get Chennai AQI: FAIL (Status ${aqiChennai.status})`);
    }
    console.log();

    // Summary
    console.log('================================');
    console.log('Test Credentials:');
    console.log('');
    console.log('Admin:');
    console.log('  Email: admin@vayuguard.com');
    console.log('  Password: Admin@123');
    console.log('');
    console.log('Demo:');
    console.log('  Email: demo@vayuguard.com');
    console.log('  Password: Demo@123');
    console.log('');
    console.log('User:');
    console.log('  Email: user@vayuguard.com');
    console.log('  Password: User@123');
    console.log('');
    console.log('Application URLs:');
    console.log('  Frontend: http://localhost:3000');
    console.log('  Backend: http://localhost:5001');
    console.log('  ML Service: http://localhost:8001');
    console.log('');

  } catch (err) {
    console.error('Error:', err.message);
  }

  process.exit(0);
}

// Wait for backend to be ready
setTimeout(runTests, 2000);
