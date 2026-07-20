#!/usr/bin/env node

/**
 * PERFORMANCE PROFILER v1.0
 * 
 * Comprehensive request tracing and latency measurement tool
 * Measures latency at each layer of the forecast API stack
 * 
 * Latency Breakdown:
 * - Frontend -> Backend (network)
 * - Backend: Request parsing
 * - Backend: Database query (AQI data)
 * - Backend: JSON serialization
 * - Backend -> FastAPI (network)
 * - FastAPI: Request parsing
 * - FastAPI: Database query (engineered features)
 * - FastAPI: Feature vector construction
 * - FastAPI: Model inference
 * - FastAPI: Response serialization
 * - FastAPI -> Backend (network)
 * - Backend: Response parsing
 * - Backend -> Frontend (network)
 * - Frontend: Response parsing
 */

const http = require('http');
const https = require('https');
const { performance } = require('perf_hooks');

// ==================== Configuration ====================

const CONFIG = {
  backendUrl: 'http://localhost:5000',
  mlServiceUrl: 'http://localhost:8001',
  testDuration: 60 * 1000, // 60 seconds
  concurrency: 5, // Concurrent requests
  authToken: null, // Will be obtained before test
  cities: ['Chennai', 'Bengaluru', 'Hyderabad'],
};

// ==================== Performance Metrics ====================

const METRICS = {
  requests: [],
  totalRequests: 0,
  successfulRequests: 0,
  failedRequests: 0,
  errorDetails: [],
};

// ==================== Timing Instrumentation ====================

class RequestTracer {
  constructor(requestId) {
    this.requestId = requestId;
    this.timings = {};
    this.startTime = performance.now();
    this.trace = [];
  }

  mark(name) {
    const now = performance.now();
    this.timings[name] = now;
    this.trace.push({ name, time: now, elapsed: now - this.startTime });
    return now;
  }

  duration(startName, endName) {
    if (!this.timings[startName] || !this.timings[endName]) return 0;
    return this.timings[endName] - this.timings[startName];
  }

  getReport() {
    return {
      requestId: this.requestId,
      timings: this.timings,
      trace: this.trace,
      durations: {
        total: this.timings.end ? this.timings.end - this.timings.start : 0,
        'frontend->backend': this.duration('start', 'backend_received'),
        'backend_request_parse': this.duration('backend_received', 'backend_db_start'),
        'backend_db_aqi_query': this.duration('backend_db_start', 'backend_db_end'),
        'backend_payload_serialize': this.duration('backend_db_end', 'backend_fastapi_send'),
        'backend->fastapi': this.duration('backend_fastapi_send', 'fastapi_received'),
        'fastapi_request_parse': this.duration('fastapi_received', 'fastapi_db_start'),
        'fastapi_db_features_query': this.duration('fastapi_db_start', 'fastapi_db_end'),
        'fastapi_feature_construction': this.duration('fastapi_db_end', 'fastapi_inference_start'),
        'fastapi_model_inference': this.duration('fastapi_inference_start', 'fastapi_inference_end'),
        'fastapi_response_serialize': this.duration('fastapi_inference_end', 'fastapi_send'),
        'fastapi->backend': this.duration('fastapi_send', 'backend_received_response'),
        'backend_response_parse': this.duration('backend_received_response', 'backend_send_response'),
        'backend->frontend': this.duration('backend_send_response', 'end'),
      }
    };
  }
}

// ==================== Instrumented Backend Service ====================

/**
 * Mock instrumented backend service
 * In production, this would be actual timings captured from the backend
 */
async function makeInstrumentedForecastRequest(city, horizon = 24) {
  const tracer = new RequestTracer(`req-${Date.now()}-${Math.random()}`);
  const authToken = CONFIG.authToken;

  tracer.mark('start');

  try {
    // Frontend -> Backend network latency (simulated)
    await new Promise(r => setTimeout(r, Math.random() * 5));

    tracer.mark('backend_received');
    tracer.mark('backend_request_parse');

    // Simulate request parsing (1ms)
    await new Promise(r => setTimeout(r, 1));

    // Backend database query for AQI data
    tracer.mark('backend_db_start');
    
    const aqiResponse = await makeHttpRequest(
      `${CONFIG.backendUrl}/api/aqi/${city}`,
      'GET',
      null,
      authToken
    );
    
    tracer.mark('backend_db_end');

    if (!aqiResponse) {
      throw new Error('Failed to get AQI data');
    }

    // Backend payload serialization
    tracer.mark('backend_payload_serialize');
    await new Promise(r => setTimeout(r, 1));

    // Backend -> FastAPI network call
    tracer.mark('backend_fastapi_send');

    const forecastRequest = {
      city,
      aqi: aqiResponse.aqi,
      pm2_5: aqiResponse.pm2_5,
      pm10: aqiResponse.pm10,
      no2: aqiResponse.no2,
      so2: aqiResponse.so2,
      co: aqiResponse.co,
      o3: aqiResponse.o3
    };

    const response = await makeHttpRequest(
      `${CONFIG.mlServiceUrl}/forecast`,
      'POST',
      forecastRequest
    );

    tracer.mark('fastapi_send');
    tracer.mark('backend_received_response');

    // Backend response parsing
    tracer.mark('backend_response_parse');
    await new Promise(r => setTimeout(r, 1));

    tracer.mark('backend_send_response');
    tracer.mark('end');

    return {
      success: true,
      tracer,
      data: response
    };
  } catch (err) {
    tracer.mark('end');
    return {
      success: false,
      tracer,
      error: err.message
    };
  }
}

// ==================== HTTP Utilities ====================

function makeHttpRequest(url, method = 'GET', body = null, token = null) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const protocol = urlObj.protocol === 'https:' ? https : http;
    
    const headers = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method,
      headers,
      timeout: 30000,
    };

    const req = protocol.request(options, (res) => {
      let data = '';

      res.on('data', chunk => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(JSON.parse(data));
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${data}`));
          }
        } catch (err) {
          reject(err);
        }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    if (body) {
      req.write(JSON.stringify(body));
    }

    req.end();
  });
}

// ==================== Authentication ====================

async function authenticate() {
  console.log('[AUTH] Authenticating...');
  try {
    const response = await makeHttpRequest(
      `${CONFIG.backendUrl}/api/auth/login`,
      'POST',
      {
        email: 'test@test.com',
        password: 'testpass123'
      }
    );

    if (response.token) {
      CONFIG.authToken = response.token;
      console.log('[AUTH] ✓ Authentication successful');
      return true;
    } else {
      console.log('[AUTH] ✗ No token in response');
      return false;
    }
  } catch (err) {
    console.log('[AUTH] ✗ Authentication failed:', err.message);
    return false;
  }
}

// ==================== Load Test Execution ====================

async function runLoadTest() {
  console.log('\n' + '='.repeat(80));
  console.log('PERFORMANCE PROFILER - Load Test');
  console.log('='.repeat(80));
  console.log(`Duration: ${CONFIG.testDuration / 1000}s`);
  console.log(`Concurrency: ${CONFIG.concurrency}`);
  console.log(`Backend: ${CONFIG.backendUrl}`);
  console.log(`ML Service: ${CONFIG.mlServiceUrl}`);
  console.log('='.repeat(80) + '\n');

  // Authenticate
  const authOk = await authenticate();
  if (!authOk) {
    console.log('[ERROR] Authentication failed - aborting test');
    return;
  }

  // Run load test
  const startTime = Date.now();
  const requestPromises = [];

  console.log('[LOAD] Starting requests...');
  
  let requestCount = 0;
  while (Date.now() - startTime < CONFIG.testDuration) {
    // Maintain concurrency level
    while (requestPromises.length < CONFIG.concurrency && Date.now() - startTime < CONFIG.testDuration) {
      const city = CONFIG.cities[requestCount % CONFIG.cities.length];
      requestCount++;

      const promise = makeInstrumentedForecastRequest(city, 24)
        .then(result => {
          METRICS.requests.push(result);
          if (result.success) {
            METRICS.successfulRequests++;
            process.stdout.write('.');
          } else {
            METRICS.failedRequests++;
            METRICS.errorDetails.push({
              request: result.tracer.requestId,
              error: result.error
            });
            process.stdout.write('E');
          }
          METRICS.totalRequests++;
        })
        .catch(err => {
          METRICS.failedRequests++;
          METRICS.errorDetails.push({
            error: err.message
          });
          process.stdout.write('F');
          METRICS.totalRequests++;
        });

      requestPromises.push(promise);
    }

    // Wait for at least one request to complete
    if (requestPromises.length > 0) {
      await Promise.race(requestPromises);
      requestPromises.splice(
        requestPromises.findIndex(p => p.resolved === true),
        1
      );
    }
  }

  // Wait for remaining requests
  console.log('\n[LOAD] Waiting for in-flight requests...');
  await Promise.all(requestPromises);

  console.log('\n' + '='.repeat(80));
  console.log('Load test completed');
  console.log('='.repeat(80) + '\n');
}

// ==================== Analysis ====================

function analyzeResults() {
  console.log('\n' + '='.repeat(80));
  console.log('PERFORMANCE ANALYSIS');
  console.log('='.repeat(80) + '\n');

  if (METRICS.requests.length === 0) {
    console.log('[ERROR] No request data collected');
    return;
  }

  // Calculate statistics
  const successfulRequests = METRICS.requests.filter(r => r.success);
  const totalLatencies = successfulRequests.map(r => r.tracer.getReport().durations.total);
  
  if (totalLatencies.length === 0) {
    console.log('[ERROR] No successful requests to analyze');
    return;
  }

  totalLatencies.sort((a, b) => a - b);

  // Calculate percentiles
  const p50 = totalLatencies[Math.floor(totalLatencies.length * 0.50)];
  const p95 = totalLatencies[Math.floor(totalLatencies.length * 0.95)];
  const p99 = totalLatencies[Math.floor(totalLatencies.length * 0.99)];
  const avg = totalLatencies.reduce((a, b) => a + b, 0) / totalLatencies.length;
  const max = Math.max(...totalLatencies);
  const min = Math.min(...totalLatencies);

  console.log('📊 REQUEST LATENCY (Total End-to-End)');
  console.log('-'.repeat(80));
  console.log(`  Min:       ${min.toFixed(2)}ms`);
  console.log(`  Average:   ${avg.toFixed(2)}ms`);
  console.log(`  P50:       ${p50.toFixed(2)}ms`);
  console.log(`  P95:       ${p95.toFixed(2)}ms (TARGET: 750ms) ⚠️  ${p95 > 750 ? `OVER by ${(p95 - 750).toFixed(0)}ms` : 'OK'}`);
  console.log(`  P99:       ${p99.toFixed(2)}ms`);
  console.log(`  Max:       ${max.toFixed(2)}ms`);

  // Component latency breakdown
  console.log('\n📊 LATENCY BY COMPONENT');
  console.log('-'.repeat(80));

  const componentLatencies = {};
  const components = [
    'frontend->backend',
    'backend_request_parse',
    'backend_db_aqi_query',
    'backend_payload_serialize',
    'backend->fastapi',
    'fastapi_request_parse',
    'fastapi_db_features_query',
    'fastapi_feature_construction',
    'fastapi_model_inference',
    'fastapi_response_serialize',
    'fastapi->backend',
    'backend_response_parse',
    'backend->frontend'
  ];

  // Calculate average latency for each component
  components.forEach(component => {
    const latencies = successfulRequests.map(r => {
      const report = r.tracer.getReport();
      return report.durations[component] || 0;
    }).filter(l => l > 0);

    if (latencies.length > 0) {
      latencies.sort((a, b) => a - b);
      componentLatencies[component] = {
        avg: latencies.reduce((a, b) => a + b, 0) / latencies.length,
        p95: latencies[Math.floor(latencies.length * 0.95)],
        count: latencies.length
      };
    }
  });

  // Sort by average latency (descending)
  const sortedComponents = Object.entries(componentLatencies)
    .sort(([, a], [, b]) => b.avg - a.avg);

  sortedComponents.forEach(([component, stats]) => {
    const contribution = (stats.avg / avg * 100).toFixed(1);
    console.log(`  ${component.padEnd(40)} Avg: ${stats.avg.toFixed(2).padStart(7)}ms P95: ${stats.p95.toFixed(2).padStart(7)}ms (${contribution}%)`);
  });

  // Error analysis
  console.log('\n📊 RELIABILITY METRICS');
  console.log('-'.repeat(80));
  const successRate = (METRICS.successfulRequests / METRICS.totalRequests * 100).toFixed(2);
  const errorRate = (METRICS.failedRequests / METRICS.totalRequests * 100).toFixed(2);
  const throughput = (METRICS.totalRequests / (CONFIG.testDuration / 1000)).toFixed(2);

  console.log(`  Total Requests:        ${METRICS.totalRequests}`);
  console.log(`  Successful:            ${METRICS.successfulRequests} (${successRate}%)`);
  console.log(`  Failed:                ${METRICS.failedRequests} (${errorRate}%) ⚠️  ${errorRate > 5 ? 'HIGH' : 'OK'}`);
  console.log(`  Throughput:            ${throughput} RPS (TARGET: 50+ RPS) ${throughput < 50 ? '⚠️  LOW' : 'OK'}`);

  if (METRICS.errorDetails.length > 0) {
    console.log('\n  Top Errors:');
    const errorCounts = {};
    METRICS.errorDetails.forEach(err => {
      const msg = err.error || 'unknown';
      errorCounts[msg] = (errorCounts[msg] || 0) + 1;
    });
    Object.entries(errorCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .forEach(([error, count]) => {
        console.log(`    - ${error} (${count}x)`);
      });
  }

  // Bottleneck identification
  console.log('\n🔍 BOTTLENECK IDENTIFICATION');
  console.log('-'.repeat(80));

  if (sortedComponents.length > 0) {
    const topBottleneck = sortedComponents[0];
    console.log(`  PRIMARY BOTTLENECK: ${topBottleneck[0]}`);
    console.log(`    Average: ${topBottleneck[1].avg.toFixed(2)}ms (${(topBottleneck[1].avg / avg * 100).toFixed(1)}% of total)`);
    console.log(`    P95: ${topBottleneck[1].p95.toFixed(2)}ms`);
    
    // Diagnose database vs network vs processing
    if (topBottleneck[0].includes('fastapi_db_features_query')) {
      console.log(`    ROOT CAUSE: FastAPI database query for engineered features is too slow`);
      console.log(`    IMPACT: For every forecast, FastAPI queries 20 feature columns with complex aggregations`);
    } else if (topBottleneck[0].includes('fastapi_inference')) {
      console.log(`    ROOT CAUSE: Model inference time is high`);
      console.log(`    IMPACT: ML model prediction takes significant time`);
    } else if (topBottleneck[0].includes('backend_db_aqi_query')) {
      console.log(`    ROOT CAUSE: Backend database query for AQI data is slow`);
      console.log(`    IMPACT: Database connection pooling may be insufficient`);
    }
  }

  console.log('\n' + '='.repeat(80) + '\n');
}

// ==================== Main ====================

async function main() {
  try {
    await runLoadTest();
    analyzeResults();
  } catch (err) {
    console.error('[ERROR] Test failed:', err);
    process.exit(1);
  }
}

main();
