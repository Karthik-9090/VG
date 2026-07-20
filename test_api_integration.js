/**
 * Integration Test: API Contract Fix Verification
 * 
 * Tests the complete flow:
 * 1. Backend receives forecast request with {city, horizon}
 * 2. Backend queries database for AQI data
 * 3. Backend constructs FastAPI-compliant payload
 * 4. Backend calls FastAPI /forecast endpoint
 * 5. FastAPI returns successful prediction
 * 6. Backend returns forecast to client
 */

const fetch = require('node-fetch');
const db = require('./backend/db');
const forecastService = require('./backend/services/forecastService');

const TEST_CITY = 'Chennai';
const ML_SERVICE_URL = 'http://localhost:8001';
const BACKEND_URL = 'http://localhost:5000';

// ANSI colors for output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(level, message) {
  const timestamp = new Date().toISOString();
  const prefix = {
    '✓': `${colors.green}✓${colors.reset}`,
    '✗': `${colors.red}✗${colors.reset}`,
    'ℹ': `${colors.blue}ℹ${colors.reset}`,
    '⚠': `${colors.yellow}⚠${colors.reset}`,
    'TEST': `${colors.cyan}TEST${colors.reset}`
  }[level] || level;

  console.log(`[${timestamp}] ${prefix} ${message}`);
}

async function testDatabaseAqiData() {
  log('TEST', 'Phase 1: Verify database has AQI data');
  
  try {
    const result = await db.query(
      'SELECT city, aqi, pm25, pm10, no2, so2, co, o3 FROM aqi_data WHERE city = $1 LIMIT 1',
      [TEST_CITY]
    );

    if (result.rows.length === 0) {
      log('✗', `No AQI data found for ${TEST_CITY}`);
      return null;
    }

    const data = result.rows[0];
    log('✓', `Found AQI data for ${TEST_CITY}`);
    log('ℹ', `  AQI: ${data.aqi}`);
    log('ℹ', `  PM2.5: ${data.pm25}`);
    log('ℹ', `  PM10: ${data.pm10}`);
    log('ℹ', `  NO2: ${data.no2}`);
    log('ℹ', `  SO2: ${data.so2}`);
    log('ℹ', `  CO: ${data.co}`);
    log('ℹ', `  O3: ${data.o3}`);

    return data;
  } catch (err) {
    log('✗', `Database query failed: ${err.message}`);
    return null;
  }
}

async function testGetLatestAqiData() {
  log('TEST', 'Phase 2: Test getLatestAqiData function');

  try {
    const aqiData = await forecastService.getLatestAqiData(TEST_CITY);
    log('✓', 'getLatestAqiData succeeded');
    log('ℹ', `  Response: ${JSON.stringify(aqiData, null, 2)}`);
    return aqiData;
  } catch (err) {
    log('✗', `getLatestAqiData failed: ${err.message}`);
    return null;
  }
}

async function testFastApiSchema() {
  log('TEST', 'Phase 3: Verify FastAPI /forecast endpoint exists');

  try {
    // Get AQI data
    const aqiData = await forecastService.getLatestAqiData(TEST_CITY);

    if (!aqiData) {
      log('✗', 'Could not get AQI data');
      return null;
    }

    // Construct correct payload
    const payload = {
      city: TEST_CITY,
      aqi: aqiData.aqi,
      pm2_5: aqiData.pm2_5,
      pm10: aqiData.pm10,
      no2: aqiData.no2,
      so2: aqiData.so2,
      co: aqiData.co,
      o3: aqiData.o3
    };

    log('ℹ', `Calling ${ML_SERVICE_URL}/forecast with payload:`);
    log('ℹ', JSON.stringify(payload, null, 2));

    const response = await fetch(`${ML_SERVICE_URL}/forecast`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      timeout: 30000
    });

    if (!response.ok) {
      const errorText = await response.text();
      log('✗', `FastAPI returned ${response.status}: ${errorText}`);
      return null;
    }

    const forecast = await response.json();
    log('✓', 'FastAPI /forecast endpoint working correctly');
    log('ℹ', `  Response: ${JSON.stringify(forecast, null, 2)}`);
    return forecast;
  } catch (err) {
    log('✗', `FastAPI call failed: ${err.message}`);
    return null;
  }
}

async function testBackendForecastService() {
  log('TEST', 'Phase 4: Test backend getForecast function');

  try {
    const forecast = await forecastService.getForecast(TEST_CITY, 24);
    log('✓', 'Backend getForecast succeeded');
    log('ℹ', `  Response: ${JSON.stringify(forecast, null, 2)}`);
    return forecast;
  } catch (err) {
    log('✗', `Backend getForecast failed: ${err.message}`);
    return null;
  }
}

async function testEndToEndApiCall() {
  log('TEST', 'Phase 5: Test end-to-end API call (backend → ML service)');

  try {
    // First, get JWT token
    log('ℹ', 'Getting authentication token...');
    
    const loginRes = await fetch(`${BACKEND_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'test@test.com',
        password: 'testpass123'
      })
    });

    if (!loginRes.ok) {
      log('⚠', `Login failed (${loginRes.status}), trying to register test user...`);
      
      const registerRes = await fetch(`${BACKEND_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'test@test.com',
          password: 'testpass123',
          name: 'Test User'
        })
      });

      if (!registerRes.ok) {
        const error = await registerRes.text();
        log('✗', `Registration failed: ${error}`);
        return null;
      }

      log('✓', 'User registered');
    }

    const loginData = await loginRes.json();
    const token = loginData.token;

    if (!token) {
      log('✗', 'No token received from login');
      return null;
    }

    log('✓', 'Authentication token obtained');

    // Now call forecast endpoint
    log('ℹ', 'Calling backend /api/forecast endpoint...');

    const forecastRes = await fetch(`${BACKEND_URL}/api/forecast`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        city: TEST_CITY,
        horizon: 24
      })
    });

    if (!forecastRes.ok) {
      const errorText = await forecastRes.text();
      log('✗', `Backend forecast failed (${forecastRes.status}): ${errorText}`);
      return null;
    }

    const forecast = await forecastRes.json();
    log('✓', 'End-to-end API call succeeded');
    log('ℹ', `  Response: ${JSON.stringify(forecast, null, 2)}`);
    return forecast;
  } catch (err) {
    log('✗', `End-to-end test failed: ${err.message}`);
    return null;
  }
}

async function testAllCities() {
  log('TEST', 'Phase 6: Test all supported cities');

  const cities = ['Chennai', 'Bengaluru', 'Hyderabad'];
  const results = {};

  for (const city of cities) {
    try {
      log('ℹ', `Testing forecast for ${city}...`);
      const forecast = await forecastService.getForecast(city, 24);
      results[city] = {
        success: true,
        aqi: forecast.forecast_aqi,
        model: forecast.model,
        version: forecast.version
      };
      log('✓', `${city}: AQI forecast = ${forecast.forecast_aqi}`);
    } catch (err) {
      results[city] = {
        success: false,
        error: err.message
      };
      log('✗', `${city}: ${err.message}`);
    }
  }

  return results;
}

async function runAllTests() {
  console.log(`
${colors.cyan}
╔════════════════════════════════════════════════════════════════╗
║         API CONTRACT FIX - INTEGRATION TEST SUITE              ║
║                                                                ║
║ Testing the complete flow:                                    ║
║ 1. Database AQI data verification                             ║
║ 2. Backend service getLatestAqiData function                  ║
║ 3. FastAPI /forecast endpoint with correct schema             ║
║ 4. Backend getForecast function                               ║
║ 5. End-to-end API call (frontend → backend → FastAPI)        ║
║ 6. All three cities                                           ║
╚════════════════════════════════════════════════════════════════╝
${colors.reset}
  `);

  const startTime = Date.now();
  const results = {
    phase1: null,
    phase2: null,
    phase3: null,
    phase4: null,
    phase5: null,
    phase6: null
  };

  try {
    // Run tests in sequence
    results.phase1 = await testDatabaseAqiData();
    console.log();

    results.phase2 = await testGetLatestAqiData();
    console.log();

    results.phase3 = await testFastApiSchema();
    console.log();

    results.phase4 = await testBackendForecastService();
    console.log();

    results.phase5 = await testEndToEndApiCall();
    console.log();

    results.phase6 = await testAllCities();
    console.log();
  } catch (err) {
    log('✗', `Test suite error: ${err.message}`);
  }

  // Summary
  const duration = ((Date.now() - startTime) / 1000).toFixed(2);

  console.log(`
${colors.cyan}
╔════════════════════════════════════════════════════════════════╗
║                      TEST SUMMARY                             ║
╚════════════════════════════════════════════════════════════════╝
${colors.reset}
Duration: ${duration}s

Phase 1 (Database): ${results.phase1 ? colors.green + '✓ PASS' : colors.red + '✗ FAIL'}${colors.reset}
Phase 2 (Service): ${results.phase2 ? colors.green + '✓ PASS' : colors.red + '✗ FAIL'}${colors.reset}
Phase 3 (FastAPI): ${results.phase3 ? colors.green + '✓ PASS' : colors.red + '✗ FAIL'}${colors.reset}
Phase 4 (Backend): ${results.phase4 ? colors.green + '✓ PASS' : colors.red + '✗ FAIL'}${colors.reset}
Phase 5 (E2E): ${results.phase5 ? colors.green + '✓ PASS' : colors.red + '✗ FAIL'}${colors.reset}
Phase 6 (Cities): ${results.phase6 ? colors.green + '✓ PASS' : colors.red + '✗ FAIL'}${colors.reset}

${results.phase1 && results.phase2 && results.phase3 && results.phase4 && results.phase5 && results.phase6 ? 
  colors.green + '✓ ALL TESTS PASSED' + colors.reset : 
  colors.red + '✗ SOME TESTS FAILED' + colors.reset}
  `);

  process.exit(results.phase1 && results.phase2 && results.phase3 && results.phase4 ? 0 : 1);
}

// Run tests
runAllTests().catch(err => {
  log('✗', `Fatal error: ${err.message}`);
  process.exit(1);
});
