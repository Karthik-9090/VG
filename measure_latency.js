#!/usr/bin/env node

/**
 * DIRECT PERFORMANCE MEASUREMENT TOOL
 * 
 * This tool measures actual latencies by making real requests
 * and collecting timing data from the services
 */

const http = require('http');
const https = require('https');

// Configuration
const CONFIG = {
  backendUrl: 'http://localhost:5000',
  mlServiceUrl: 'http://localhost:8001',
  testDuration: 30 * 1000, // 30 seconds
  concurrency: 3,
  cities: ['Chennai', 'Bengaluru', 'Hyderabad'],
};

// Metrics collector
const metrics = {
  requests: [],
  totalRequests: 0,
  successRequests: 0,
  failedRequests: 0,
  totalLatency: 0,
  errors: [],
};

// Simple HTTP request wrapper with timing
function httpRequest(url, method = 'GET', body = null, token = null) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const isHttps = urlObj.protocol === 'https:';
    const client = isHttps ? https : http;

    const headers = {
      'Content-Type': 'application/json',
      'X-Trace-Request': `trace-${Date.now()}-${Math.random()}`,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const startTime = Date.now();

    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || (isHttps ? 443 : 80),
      path: urlObj.pathname + urlObj.search,
      method,
      headers,
      timeout: 30000,
    };

    const req = client.request(options, (res) => {
      let data = '';
      const headerTime = Date.now();

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        const endTime = Date.now();
        const totalTime = endTime - startTime;
        const headerTime_ms = headerTime - startTime;

        try {
          const parsed = JSON.parse(data);
          resolve({
            success: res.statusCode >= 200 && res.statusCode < 300,
            statusCode: res.statusCode,
            data: parsed,
            timing: {
              total: totalTime,
              toFirstByte: headerTime_ms,
              dataTransfer: endTime - headerTime,
            },
            headers: res.headers,
          });
        } catch (e) {
          reject(new Error(`Failed to parse response: ${e.message}`));
        }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout (30s)'));
    });

    if (body) {
      req.write(JSON.stringify(body));
    }

    req.end();
  });
}

// Authenticate and get token
async function authenticate() {
  console.log('🔐 Authenticating...');
  try {
    const result = await httpRequest(
      `${CONFIG.backendUrl}/api/auth/login`,
      'POST',
      { email: 'test@test.com', password: 'testpass123' }
    );

    if (result.success && result.data.token) {
      console.log('✅ Authentication successful\n');
      return result.data.token;
    } else {
      console.log('❌ Authentication failed\n');
      return null;
    }
  } catch (err) {
    console.log(`❌ Authentication error: ${err.message}\n`);
    return null;
  }
}

// Make a single forecast request and measure timing
async function makeForecastRequest(city, token) {
  const startTime = Date.now();

  try {
    // First, get the AQI data from backend (this includes a DB query)
    const aqiStart = Date.now();
    const aqiResult = await httpRequest(`${CONFIG.backendUrl}/api/aqi/${city}`, 'GET', null, token);
    const aqiTime = Date.now() - aqiStart;

    if (!aqiResult.success) {
      throw new Error(`Failed to get AQI: ${aqiResult.statusCode}`);
    }

    // Then make the forecast request to backend
    const forecastStart = Date.now();
    const forecastResult = await httpRequest(
      `${CONFIG.backendUrl}/api/forecast`,
      'POST',
      { city, horizon: 24 },
      token
    );
    const forecastTime = Date.now() - forecastStart;

    const totalTime = Date.now() - startTime;

    if (!forecastResult.success) {
      throw new Error(`Forecast failed: ${forecastResult.statusCode}`);
    }

    return {
      success: true,
      city,
      totalLatency: totalTime,
      aqiQueryLatency: aqiTime,
      forecastLatency: forecastTime,
      httpHeaderTime: forecastResult.timing.toFirstByte,
      httpDataTime: forecastResult.timing.dataTransfer,
      data: forecastResult.data,
    };
  } catch (err) {
    const totalTime = Date.now() - startTime;
    return {
      success: false,
      city,
      totalLatency: totalTime,
      error: err.message,
    };
  }
}

// Run the test
async function runLoadTest(token) {
  console.log('📊 Starting performance measurement...\n');
  console.log(`Testing for ${CONFIG.testDuration / 1000} seconds with ${CONFIG.concurrency} concurrent requests\n`);

  const startTime = Date.now();
  const inFlight = [];

  let requestIndex = 0;

  while (Date.now() - startTime < CONFIG.testDuration) {
    // Maintain concurrency
    while (inFlight.length < CONFIG.concurrency && Date.now() - startTime < CONFIG.testDuration) {
      const city = CONFIG.cities[requestIndex % CONFIG.cities.length];
      requestIndex++;

      const promise = makeForecastRequest(city, token)
        .then((result) => {
          metrics.requests.push(result);
          metrics.totalRequests++;

          if (result.success) {
            metrics.successRequests++;
            metrics.totalLatency += result.totalLatency;
            process.stdout.write('.');
          } else {
            metrics.failedRequests++;
            metrics.errors.push(result.error);
            process.stdout.write('E');
          }
        })
        .catch((err) => {
          metrics.failedRequests++;
          metrics.errors.push(err.message);
          metrics.totalRequests++;
          process.stdout.write('F');
        });

      inFlight.push(promise);
    }

    // Wait for any request to complete
    if (inFlight.length > 0) {
      await Promise.race(inFlight);
      inFlight.splice(0, 1);
    }
  }

  // Wait for remaining requests
  console.log('\n\n⏳ Waiting for in-flight requests to complete...');
  await Promise.all(inFlight);
  console.log('✅ All requests completed\n');
}

// Analyze results
function analyzeResults() {
  console.log('\n' + '='.repeat(100));
  console.log('PERFORMANCE ANALYSIS RESULTS');
  console.log('='.repeat(100) + '\n');

  if (metrics.successRequests === 0) {
    console.log('❌ No successful requests to analyze\n');
    return;
  }

  const successfulRequests = metrics.requests.filter((r) => r.success);
  const latencies = successfulRequests.map((r) => r.totalLatency);

  latencies.sort((a, b) => a - b);

  // Calculate percentiles
  const p50 = latencies[Math.floor(latencies.length * 0.50)];
  const p75 = latencies[Math.floor(latencies.length * 0.75)];
  const p95 = latencies[Math.floor(latencies.length * 0.95)];
  const p99 = latencies[Math.floor(latencies.length * 0.99)];
  const avg = metrics.totalLatency / metrics.successRequests;
  const min = Math.min(...latencies);
  const max = Math.max(...latencies);

  console.log('📈 OVERALL LATENCY DISTRIBUTION');
  console.log('-'.repeat(100));
  console.log(
    `  Min         ${min.toFixed(0).padStart(6)}ms |  Average    ${avg.toFixed(0).padStart(6)}ms |  Max        ${max.toFixed(0).padStart(6)}ms`
  );
  console.log(
    `  P50         ${p50.toFixed(0).padStart(6)}ms |  P75        ${p75.toFixed(0).padStart(6)}ms |  P95        ${p95.toFixed(0).padStart(6)}ms  ⚠️ TARGET: 750ms`
  );
  console.log(
    `  P99         ${p99.toFixed(0).padStart(6)}ms |  Difference ${(p95 - 750).toFixed(0).padStart(6)}ms OVER TARGET`
  );

  // Latency contribution analysis
  console.log('\n📊 LATENCY CONTRIBUTION BREAKDOWN');
  console.log('-'.repeat(100));

  const aqiQueryLatencies = successfulRequests.map((r) => r.aqiQueryLatency);
  const forecastLatencies = successfulRequests.map((r) => r.forecastLatency);
  const httpHeaderLatencies = successfulRequests.map((r) => r.httpHeaderTime);
  const httpDataLatencies = successfulRequests.map((r) => r.httpDataTime);

  aqiQueryLatencies.sort((a, b) => a - b);
  forecastLatencies.sort((a, b) => a - b);
  httpHeaderLatencies.sort((a, b) => a - b);
  httpDataLatencies.sort((a, b) => a - b);

  const avgAqi = aqiQueryLatencies.reduce((a, b) => a + b, 0) / aqiQueryLatencies.length;
  const p95Aqi = aqiQueryLatencies[Math.floor(aqiQueryLatencies.length * 0.95)];

  const avgForecast = forecastLatencies.reduce((a, b) => a + b, 0) / forecastLatencies.length;
  const p95Forecast = forecastLatencies[Math.floor(forecastLatencies.length * 0.95)];

  const avgHttpHeader = httpHeaderLatencies.reduce((a, b) => a + b, 0) / httpHeaderLatencies.length;
  const avgHttpData = httpDataLatencies.reduce((a, b) => a + b, 0) / httpDataLatencies.length;

  console.log(`  Backend AQI Query (DB):    Avg ${avgAqi.toFixed(0).padStart(5)}ms  |  P95 ${p95Aqi.toFixed(0).padStart(5)}ms  |  % of Total ${(avgAqi / avg * 100).toFixed(1).padStart(5)}%`);
  console.log(`  Backend Forecast Request:  Avg ${avgForecast.toFixed(0).padStart(5)}ms  |  P95 ${p95Forecast.toFixed(0).padStart(5)}ms  |  % of Total ${(avgForecast / avg * 100).toFixed(1).padStart(5)}%`);
  console.log(`  HTTP Header/Connection:    Avg ${avgHttpHeader.toFixed(0).padStart(5)}ms`);
  console.log(`  HTTP Data Transfer:        Avg ${avgHttpData.toFixed(0).padStart(5)}ms`);

  // Identify primary bottleneck
  const components = [
    { name: 'Backend AQI Query', avg: avgAqi, p95: p95Aqi },
    { name: 'Backend Forecast', avg: avgForecast, p95: p95Forecast },
    { name: 'HTTP Overhead', avg: avgHttpHeader + avgHttpData, p95: 0 },
  ];

  components.sort((a, b) => b.avg - a.avg);

  console.log('\n🎯 PRIMARY BOTTLENECK');
  console.log('-'.repeat(100));
  console.log(`  Component:  ${components[0].name}`);
  console.log(`  Average:    ${components[0].avg.toFixed(0)}ms (${(components[0].avg / avg * 100).toFixed(1)}% of total)`);
  console.log(`  P95:        ${components[0].p95.toFixed(0)}ms`);

  // Reliability
  console.log('\n📊 RELIABILITY METRICS');
  console.log('-'.repeat(100));

  const successRate = (metrics.successRequests / metrics.totalRequests * 100).toFixed(2);
  const errorRate = (metrics.failedRequests / metrics.totalRequests * 100).toFixed(2);
  const throughput = (metrics.totalRequests / (CONFIG.testDuration / 1000)).toFixed(2);

  console.log(`  Total Requests:    ${metrics.totalRequests}`);
  console.log(`  Successful:        ${metrics.successRequests} (${successRate}%)`);
  console.log(`  Failed:            ${metrics.failedRequests} (${errorRate}%) ${errorRate > 5 ? '⚠️ HIGH ERROR RATE' : ''}`);
  console.log(`  Throughput:        ${throughput} RPS (Target: 50+ RPS) ${throughput < 50 ? '⚠️ LOW' : ''}`);

  if (metrics.errors.length > 0) {
    console.log(`\n  Top Errors:`);
    const errorCounts = {};
    metrics.errors.forEach((err) => {
      errorCounts[err] = (errorCounts[err] || 0) + 1;
    });
    Object.entries(errorCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .forEach(([error, count]) => {
        console.log(`    - ${error} (${count}x)`);
      });
  }

  // Performance verdict
  console.log('\n🔍 PERFORMANCE VERDICT');
  console.log('-'.repeat(100));

  if (p95 <= 750) {
    console.log('  ✅ PASS - Latency target met');
  } else {
    console.log(`  ❌ FAIL - P95 latency is ${p95 - 750}ms over target (${((p95 / 750 - 1) * 100).toFixed(0)}% over)`);
  }

  if (errorRate < 5) {
    console.log('  ✅ PASS - Error rate acceptable');
  } else {
    console.log(`  ⚠️ WARN - Error rate ${errorRate}% is high (target: <5%)`);
  }

  if (throughput >= 50) {
    console.log('  ✅ PASS - Throughput target met');
  } else {
    console.log(`  ⚠️ WARN - Throughput ${throughput} RPS is below target (target: 50+ RPS)`);
  }

  console.log('\n' + '='.repeat(100) + '\n');

  // Export data for report generation
  return {
    latencies: {
      min,
      avg,
      p50,
      p75,
      p95,
      p99,
      max,
    },
    components: {
      aqiQuery: { avg: avgAqi, p95: p95Aqi, percentage: (avgAqi / avg * 100) },
      forecast: { avg: avgForecast, p95: p95Forecast, percentage: (avgForecast / avg * 100) },
    },
    reliability: {
      successRate: parseFloat(successRate),
      errorRate: parseFloat(errorRate),
      throughput: parseFloat(throughput),
    },
    verdict: {
      latencyPass: p95 <= 750,
      errorPass: errorRate < 5,
      throughputPass: throughput >= 50,
    },
  };
}

// Main
async function main() {
  console.log('\n' + '='.repeat(100));
  console.log('VAYUGUARD FORECAST API - PERFORMANCE MEASUREMENT');
  console.log('='.repeat(100) + '\n');

  const token = await authenticate();
  if (!token) {
    console.log('❌ Cannot proceed without authentication\n');
    process.exit(1);
  }

  try {
    await runLoadTest(token);
    const results = analyzeResults();

    // Save results for report generation
    require('fs').writeFileSync(
      'performance_measurement_results.json',
      JSON.stringify({ timestamp: new Date().toISOString(), ...results }, null, 2)
    );

    console.log('📁 Results saved to: performance_measurement_results.json\n');
  } catch (err) {
    console.error('❌ Test failed:', err);
    process.exit(1);
  }
}

main();
