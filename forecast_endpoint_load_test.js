#!/usr/bin/env node
/**
 * FORECAST ENDPOINT LOAD TEST
 * 
 * Validates connection pool performance on actual business endpoint
 * Tests: 10, 50, 100 concurrent users
 * Verifies: Predictions, logging, model inference, pool management
 */

const http = require('http');
const crypto = require('crypto');

// Use JWT from backend's node_modules
let jwt;
try {
  jwt = require('./backend/node_modules/jsonwebtoken');
} catch (e) {
  console.error('Failed to load jsonwebtoken module');
  process.exit(1);
}

// Test configuration
const tests = [
  { name: '10 Concurrent Users', concurrency: 10, requests: 50 },
  { name: '50 Concurrent Users', concurrency: 50, requests: 100 },
  { name: '100 Concurrent Users', concurrency: 100, requests: 200 },
];

const config = {
  host: 'localhost',
  port: 5001,
  endpoint: '/api/forecast',
  timeout: 30000,
  jwtSecret: 'vayuguard-secret', // Same as backend default
};

// Generate valid JWT token for testing
const testToken = jwt.sign(
  { sub: 'test-user-' + crypto.randomBytes(4).toString('hex'), role: 'user' },
  config.jwtSecret,
  { expiresIn: '24h' }
);

// Valid cities in the system
const cities = ['Chennai', 'Bengaluru', 'Hyderabad'];

/**
 * Make a forecast request
 */
function makeForecastRequest(city = 'Chennai') {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const requestData = JSON.stringify({
      city,
      horizon: 24
    });

    const options = {
      hostname: config.host,
      port: config.port,
      path: config.endpoint,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(requestData),
        'Authorization': `Bearer ${testToken}`
      },
      timeout: config.timeout
    };

    const req = http.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        const endTime = Date.now();
        const latency = endTime - startTime;
        
        try {
          const response = JSON.parse(data);
          
          resolve({
            statusCode: res.statusCode,
            latency,
            city,
            success: res.statusCode === 200,
            response: {
              hasForecast: !!response.forecast_aqi,
              hasModel: !!response.model,
              hasTimestamp: !!response.timestamp,
              hasPredictionId: !!response.prediction_id
            }
          });
        } catch (e) {
          resolve({
            statusCode: res.statusCode,
            latency,
            city,
            success: false,
            error: 'JSON parse failed',
            response: {}
          });
        }
      });
    });

    req.on('error', (err) => {
      const endTime = Date.now();
      const latency = endTime - startTime;
      
      reject({
        statusCode: 0,
        latency,
        city,
        error: err.message,
        success: false
      });
    });

    req.on('timeout', () => {
      req.destroy();
      const endTime = Date.now();
      const latency = endTime - startTime;
      
      reject({
        statusCode: 0,
        latency,
        city,
        error: 'timeout',
        success: false
      });
    });

    req.write(requestData);
    req.end();
  });
}

/**
 * Calculate percentile
 */
function calculatePercentile(sorted, percentile) {
  if (sorted.length === 0) return 0;
  const index = Math.ceil((percentile / 100) * sorted.length) - 1;
  return sorted[Math.max(0, index)];
}

/**
 * Run a single load test scenario
 */
async function runLoadTest(testConfig) {
  console.log(`\n${'='.repeat(80)}`);
  console.log(`TEST: ${testConfig.name}`);
  console.log(`${'='.repeat(80)}`);
  console.log(`  Concurrency: ${testConfig.concurrency}`);
  console.log(`  Total Requests: ${testConfig.requests}`);
  console.log(`  Starting...`);

  const results = [];
  const errors = [];
  
  const startTime = Date.now();
  const batchSize = testConfig.concurrency;
  const numBatches = Math.ceil(testConfig.requests / batchSize);

  for (let batch = 0; batch < numBatches; batch++) {
    const batchRequests = [];
    const requestsThisBatch = Math.min(batchSize, testConfig.requests - (batch * batchSize));
    
    // Randomly select cities
    for (let i = 0; i < requestsThisBatch; i++) {
      const city = cities[i % cities.length];
      batchRequests.push(
        makeForecastRequest(city)
          .then(result => {
            results.push(result);
            return result;
          })
          .catch(err => {
            errors.push(err);
            results.push(err);
            return err;
          })
      );
    }

    await Promise.all(batchRequests);
    
    const completed = Math.min((batch + 1) * batchSize, testConfig.requests);
    const progress = Math.round((completed / testConfig.requests) * 100);
    console.log(`  Progress: ${completed}/${testConfig.requests} (${progress}%)`);
  }

  const endTime = Date.now();
  const totalTime = (endTime - startTime) / 1000;

  // Calculate statistics
  const successfulResults = results.filter(r => r.success);
  const failedResults = results.filter(r => !r.success);
  const latencies = successfulResults
    .map(r => r.latency)
    .sort((a, b) => a - b);

  const avgLatency = latencies.length > 0 
    ? (latencies.reduce((a, b) => a + b, 0) / latencies.length).toFixed(2)
    : 0;
  
  const p50 = calculatePercentile(latencies, 50);
  const p95 = calculatePercentile(latencies, 95);
  const p99 = calculatePercentile(latencies, 99);
  const minLatency = latencies.length > 0 ? latencies[0] : 0;
  const maxLatency = latencies.length > 0 ? latencies[latencies.length - 1] : 0;

  const successCount = successfulResults.length;
  const failCount = failedResults.length;
  const errorRate = ((failCount / results.length) * 100).toFixed(2);
  const successRate = ((successCount / results.length) * 100).toFixed(2);

  const throughput = (testConfig.requests / totalTime).toFixed(2);

  // Response validation
  let allResponsesValid = true;
  let invalidCount = 0;
  successfulResults.forEach(r => {
    if (!r.response.hasForecast || !r.response.hasModel || !r.response.hasTimestamp) {
      allResponsesValid = false;
      invalidCount++;
    }
  });

  // Results
  console.log(`\n[LATENCY METRICS]`);
  console.log(`  Minimum:     ${minLatency.toFixed(2)}ms`);
  console.log(`  Average:     ${avgLatency}ms`);
  console.log(`  P50:         ${p50.toFixed(2)}ms`);
  console.log(`  P95:         ${p95.toFixed(2)}ms`);
  console.log(`  P99:         ${p99.toFixed(2)}ms`);
  console.log(`  Maximum:     ${maxLatency.toFixed(2)}ms`);

  console.log(`\n[SUCCESS METRICS]`);
  console.log(`  Successful:  ${successCount}/${results.length} (${successRate}%)`);
  console.log(`  Failed:      ${failCount}/${results.length} (${errorRate}%)`);
  console.log(`  Throughput:  ${throughput} RPS`);
  console.log(`  Duration:    ${totalTime.toFixed(2)}s`);

  console.log(`\n[RESPONSE VALIDATION]`);
  console.log(`  All responses valid: ${allResponsesValid ? 'YES' : `NO (${invalidCount} invalid)`}`);
  if (failCount > 0) {
    const errorTypes = {};
    failedResults.forEach(r => {
      const key = r.error || `HTTP ${r.statusCode}`;
      errorTypes[key] = (errorTypes[key] || 0) + 1;
    });
    console.log(`  Error types:`);
    Object.entries(errorTypes).forEach(([type, count]) => {
      console.log(`    - ${type}: ${count}`);
    });
  }

  // Pass/Fail for this scenario
  const p95Pass = p95 < 500;
  const errorRatePass = parseFloat(errorRate) < 1;
  const throughputPass = parseFloat(throughput) > 100;

  console.log(`\n[PASS/FAIL]`);
  console.log(`  P95 < 500ms:        ${p95Pass ? '✅ PASS' : '❌ FAIL'} (${p95.toFixed(2)}ms)`);
  console.log(`  Error Rate < 1%:    ${errorRatePass ? '✅ PASS' : '❌ FAIL'} (${errorRate}%)`);
  console.log(`  Throughput > 100:   ${throughputPass ? '✅ PASS' : '❌ FAIL'} (${throughput} RPS)`);

  return {
    testName: testConfig.name,
    concurrency: testConfig.concurrency,
    requests: testConfig.requests,
    successCount,
    failCount,
    errorRate: parseFloat(errorRate),
    successRate: parseFloat(successRate),
    latencies: {
      min: minLatency,
      avg: parseFloat(avgLatency),
      p50,
      p95,
      p99,
      max: maxLatency
    },
    throughput: parseFloat(throughput),
    duration: totalTime,
    responseValidation: {
      allValid: allResponsesValid,
      invalidCount
    },
    pass: {
      p95: p95Pass,
      errorRate: errorRatePass,
      throughput: throughputPass,
      overall: p95Pass && errorRatePass && throughputPass
    }
  };
}

/**
 * Main execution
 */
async function main() {
  console.log('\n' + '='.repeat(80));
  console.log('FORECAST ENDPOINT LOAD TEST');
  console.log('='.repeat(80));
  console.log(`Target: http://${config.host}:${config.port}${config.endpoint}`);
  console.log(`Pass Criteria:`);
  console.log(`  - P95 Latency < 500ms`);
  console.log(`  - Error Rate < 1%`);
  console.log(`  - Throughput > 100 RPS`);

  const allResults = [];
  
  for (const testConfig of tests) {
    const result = await runLoadTest(testConfig);
    allResults.push(result);
  }

  // Summary
  console.log(`\n${'='.repeat(80)}`);
  console.log('TEST SUMMARY');
  console.log('='.repeat(80));

  console.log(`\n[LATENCY SUMMARY]`);
  allResults.forEach(r => {
    const status = r.pass.p95 ? '✅' : '❌';
    console.log(`${status} ${r.testName.padEnd(30)} P95: ${r.latencies.p95.toFixed(2)}ms`);
  });

  console.log(`\n[ERROR RATE SUMMARY]`);
  allResults.forEach(r => {
    const status = r.pass.errorRate ? '✅' : '❌';
    console.log(`${status} ${r.testName.padEnd(30)} Error: ${r.errorRate.toFixed(2)}%`);
  });

  console.log(`\n[THROUGHPUT SUMMARY]`);
  allResults.forEach(r => {
    const status = r.pass.throughput ? '✅' : '❌';
    console.log(`${status} ${r.testName.padEnd(30)} RPS: ${r.throughput.toFixed(2)}`);
  });

  // Overall verdict
  const allPass = allResults.every(r => r.pass.overall);
  
  console.log(`\n${'='.repeat(80)}`);
  console.log('FINAL VERDICT');
  console.log('='.repeat(80));
  console.log(`\nAll scenarios passed: ${allPass ? '✅ YES' : '❌ NO'}`);
  
  if (!allPass) {
    console.log(`\nFailed scenarios:`);
    allResults.forEach(r => {
      if (!r.pass.overall) {
        console.log(`  - ${r.testName}`);
        if (!r.pass.p95) console.log(`    • P95: ${r.latencies.p95.toFixed(2)}ms (target: <500ms)`);
        if (!r.pass.errorRate) console.log(`    • Error Rate: ${r.errorRate.toFixed(2)}% (target: <1%)`);
        if (!r.pass.throughput) console.log(`    • Throughput: ${r.throughput.toFixed(2)} RPS (target: >100)`);
      }
    });
  }

  console.log(`\n${'='.repeat(80)}\n`);

  return { allResults, verdict: allPass ? 'PASS' : 'FAIL' };
}

// Export for use in other scripts
module.exports = { runLoadTest, config };

// Run if executed directly
if (require.main === module) {
  main()
    .then(result => {
      process.exit(result.verdict === 'PASS' ? 0 : 1);
    })
    .catch(err => {
      console.error('Test failed:', err);
      process.exit(1);
    });
}
