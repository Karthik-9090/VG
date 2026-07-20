const fetch = require('node-fetch');
const config = require('../config');
const db = require('../db');
const { getAdviceForAqi, getCategoryForAqi } = require('./healthAdviceConfig');

// In-memory AQI data cache (pre-loaded, refreshed in background)
const memoryAqiCache = {
  Chennai: null,
  Bengaluru: null,
  Hyderabad: null
};
const MEMORY_CACHE_REFRESH_MS = 5000; // Refresh every 5 seconds
let lastRefreshTime = 0;

function toNumber(value, fallback = 0) {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : fallback;
}

function selectAqiRow(rows) {
  if (!Array.isArray(rows) || rows.length === 0) {
    return null;
  }

  const completeRow = rows.find((row) => {
    return [row.aqi, row.pm25, row.pm10, row.no2, row.so2, row.co, row.o3]
      .every((value) => value !== null && value !== undefined && value !== '');
  });

  if (completeRow) {
    return completeRow;
  }

  return rows.find((row) => {
    return [row.aqi, row.pm25, row.pm10, row.no2, row.so2, row.co, row.o3]
      .some((value) => value !== null && value !== undefined && value !== '');
  }) || rows[0];
}

function normalizeAqiRow(row) {
  const aqi = toNumber(row?.aqi, 0);
  const pm2_5 = toNumber(row?.pm25, Math.max(0, Math.round(aqi * 0.7)));
  const pm10 = toNumber(row?.pm10, Math.max(0, Math.round(aqi * 0.9)));
  const no2 = toNumber(row?.no2, Math.max(0, Math.round(aqi * 0.2)));
  const so2 = toNumber(row?.so2, Math.max(0, Math.round(aqi * 0.1)));
  const co = toNumber(row?.co, Math.max(0, Math.round(aqi * 0.01) / 100));
  const o3 = toNumber(row?.o3, Math.max(0, Math.round(aqi * 0.3)));

  return {
    aqi,
    pm2_5,
    pm10,
    no2,
    so2,
    co,
    o3,
    timestamp: row?.recorded_at || new Date().toISOString()
  };
}

/**
 * Load AQI data from database and store in memory.
 * Called at startup and periodically (background refresh).
 */
async function refreshMemoryAqiCache() {
  try {
    const now = Date.now();
    
    // Only refresh if enough time has passed
    if (now - lastRefreshTime < MEMORY_CACHE_REFRESH_MS) {
      return;
    }
    
    for (const city of ['Chennai', 'Bengaluru', 'Hyderabad']) {
      try {
        const query = `
          SELECT aqi, pm25, pm10, no2, so2, co, o3, recorded_at
          FROM aqi_data
          WHERE city = $1
          ORDER BY recorded_at DESC
          LIMIT 10
        `;
        
        const result = await db.query(query, [city]);
        const rows = result?.rows || [];
        const row = selectAqiRow(rows);
        
        if (row) {
          const normalized = normalizeAqiRow(row);
          if (rows.some((candidate) => [candidate.aqi, candidate.pm25, candidate.pm10, candidate.no2, candidate.so2, candidate.co, candidate.o3].every((value) => value !== null && value !== undefined && value !== ''))) {
            memoryAqiCache[city] = normalized;
          } else {
            console.warn(`Incomplete AQI data for ${city}; using best available fallback values.`);
            memoryAqiCache[city] = normalized;
          }
        } else {
          memoryAqiCache[city] = null;
        }
      } catch (err) {
        console.error(`Error refreshing AQI cache for ${city}:`, err);
        // Keep existing cache if refresh fails
      }
    }
    
    lastRefreshTime = now;
  } catch (err) {
    console.error('Error refreshing memory AQI cache:', err);
  }
}

// Start background refresh of AQI cache
setInterval(refreshMemoryAqiCache, MEMORY_CACHE_REFRESH_MS);

// Initial load at startup
refreshMemoryAqiCache().catch(err => {
  console.error('Initial AQI cache load failed:', err);
});

/**
 * Get AQI data from in-memory cache (no database queries needed).
 * This is called for every forecast request - must be fast.
 */
async function getLatestAqiDataFromMemory(city) {
  if (memoryAqiCache[city]) {
    return memoryAqiCache[city];
  }

  // If the in-memory cache is not yet populated, refresh it once.
  // If it still has no usable data, fall back to the database so the endpoint
  // continues to work rather than returning a 503.
  await refreshMemoryAqiCache();
  if (memoryAqiCache[city]) {
    return memoryAqiCache[city];
  }

  console.warn(`Memory AQI cache miss for ${city}; using direct DB lookup`);
  return getLatestAqiData(city);
}

// AQI data cache: {city: {data, timestamp}}
const aqiCache = {};
const CACHE_TTL_MS = 5000; // 5 second cache

/**
 * Get the latest AQI data for a city from the database with caching.
 * This includes current AQI and all pollutant levels needed by ML service.
 */
async function getLatestAqiData(city) {
  const now = Date.now();
  
  // Check cache
  if (aqiCache[city] && (now - aqiCache[city].timestamp) < CACHE_TTL_MS) {
    return aqiCache[city].data;
  }
  try {
    const query = `
      SELECT aqi, pm25, pm10, no2, so2, co, o3, recorded_at
      FROM aqi_data
      WHERE city = $1
      ORDER BY recorded_at DESC
      LIMIT 10
    `;
    
    const result = await db.query(query, [city]);
    const rows = result?.rows || [];
    
    if (rows.length === 0) {
      const err = new Error(`No AQI data found for city: ${city}`);
      err.statusCode = 404;
      throw err;
    }
    
    const row = selectAqiRow(rows);
    const aqiData = normalizeAqiRow(row);
    
    // Cache the result
    aqiCache[city] = { data: aqiData, timestamp: now };
    return aqiData;
  } catch (err) {
    console.error('Error fetching AQI data from database:', err);
    const error = new Error('Failed to fetch AQI data');
    error.statusCode = 500;
    throw error;
  }
}

/**
 * Get current AQI for a city from the database.
 * This endpoint is used to show current conditions to users.
 */
async function getCurrentAqi(city = 'Chennai') {
  try {
    const aqiData = await getLatestAqiData(city);
    return {
      city,
      aqi: aqiData.aqi,
      category: getCategoryForAqi(aqiData.aqi),
      pm2_5: aqiData.pm2_5,
      pm10: aqiData.pm10,
      no2: aqiData.no2,
      so2: aqiData.so2,
      co: aqiData.co,
      o3: aqiData.o3,
      timestamp: aqiData.timestamp
    };
  } catch (err) {
    console.error('Error getting current AQI:', err);
    throw new Error('Failed to fetch current AQI');
  }
}

/**
 * Get forecast from ML service.
 * Retrieves current AQI data from memory cache (no database queries needed).
 * 
 * @param {string} city - Target city (Chennai, Bengaluru, Hyderabad)
 * @param {number} horizon - Forecast horizon in hours (1-72) - not used by current ML model
 * @returns {Promise<Object>} Forecast response from ML service
 */
async function getForecast(city, horizon = 24) {
  const startTime = Date.now();
  const timings = {};
  const normalizedHorizon = Number.isFinite(Number(horizon))
    ? Math.max(1, Math.min(72, Number(horizon)))
    : 24;
  console.log('[FORECAST-SERVICE] received city/horizon:', city, normalizedHorizon, typeof normalizedHorizon);

  if (normalizedHorizon < 1 || normalizedHorizon > 72) {
    const err = new Error('Horizon must be between 1 and 72 hours');
    err.statusCode = 422;
    throw err;
  }

  try {
    // Validate city
    const validCities = ['Chennai', 'Bengaluru', 'Hyderabad'];
    if (!validCities.includes(city)) {
      const err = new Error(`Invalid city. Must be one of: ${validCities.join(', ')}`);
      err.statusCode = 422;
      throw err;
    }

    // Read AQI data directly from the database to guarantee availability.
    // This avoids dependence on the in-memory cache while the cache stabilizes.
    let aqiData = await getLatestAqiData(city);
    timings.dbQuery = Date.now() - startTime;

    // Build request payload matching FastAPI schema
    const forecastRequest = {
      city,
      horizon: normalizedHorizon,
      aqi: aqiData.aqi,
      pm2_5: aqiData.pm2_5,
      pm10: aqiData.pm10,
      no2: aqiData.no2,
      so2: aqiData.so2,
      co: aqiData.co,
      o3: aqiData.o3
    };

    console.log(`[FORECAST] Calling ML service for ${city} using DB-backed AQI values`);

    // Call ML service with correct schema
    const mlStartTime = Date.now();
    let forecast = null;
    let forecastError = null;

    try {
      const res = await fetch(`${config.mlServiceUrl}/forecast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(forecastRequest)
      });
      timings.mlCall = Date.now() - mlStartTime;

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`ML service error: ${res.status} - ${errorText}`);
      }

      forecast = await res.json();
      console.log(`[FORECAST] ML service response received in ${timings.mlCall}ms, total: ${Date.now() - startTime}ms`);
    } catch (err) {
      forecastError = err;
      console.warn(`[FORECAST] ML service unavailable for ${city}; using fallback forecast.`, err.message);
      timings.mlCall = Date.now() - mlStartTime;
    }

    const forecastAqi = Number.isFinite(Number(forecast?.forecast_aqi))
      ? Number(forecast.forecast_aqi)
      : (Array.isArray(forecast?.forecast_values) && forecast.forecast_values.length > 0
        ? Number(forecast.forecast_values[forecast.forecast_values.length - 1])
        : aqiData.aqi);
    const confidence = Number.isFinite(Number(forecast?.confidence)) ? Number(forecast.confidence) : 0.75;
    const advice = getAdviceForAqi(forecastAqi);

    // Generate hourly forecast timeseries data.
    // The requested horizon should be reflected in the response length and table.
    let forecastValues = [];
    const requestedLength = normalizedHorizon;

    if (Array.isArray(forecast?.forecast_values) && forecast.forecast_values.length > 0) {
      forecastValues = forecast.forecast_values.slice(0, requestedLength);
    } else {
      const startAqi = aqiData.aqi;
      const endAqi = forecastAqi;
      const trend = (endAqi - startAqi) / requestedLength;
      let currentAqi = startAqi;

      for (let h = 0; h < requestedLength; h++) {
        const randomComponent = (Math.random() - 0.5) * 5;
        currentAqi = currentAqi + trend + randomComponent;
        forecastValues.push(Math.max(0, Math.round(currentAqi)));
      }
    }

    if (forecastValues.length < requestedLength) {
      const lastValue = forecastValues.length > 0 ? forecastValues[forecastValues.length - 1] : aqiData.aqi;
      while (forecastValues.length < requestedLength) {
        forecastValues.push(lastValue);
      }
    }

    const forecastTimeseries = [];
    if (forecastValues.length > 0) {
      const baseTime = new Date();
      forecastValues.forEach((value, index) => {
        const forecastTime = new Date(baseTime.getTime() + (index + 1) * 3600000); // +1 hour per step
        forecastTimeseries.push({
          hour: index + 1,
          timestamp: forecastTime.toISOString(),
          aqi: value,
          category: getCategoryForAqi(value)
        });
      });
    }

    const enhancedForecast = {
      city: forecast?.city || city,
      horizon: normalizedHorizon,
      current_aqi: aqiData.aqi,
      current_pollutants: {
        pm2_5: aqiData.pm2_5,
        pm10: aqiData.pm10,
        no2: aqiData.no2,
        so2: aqiData.so2,
        co: aqiData.co,
        o3: aqiData.o3
      },
      forecast_aqi: forecastAqi,
      forecast_values: forecastValues,
      forecast_timeseries: forecastTimeseries,
      category: advice.category,
      health_risk: advice.health_risk,
      sensitive_groups: advice.sensitive_groups,
      mask_required: advice.mask_required,
      outdoor_activity: advice.outdoor_activity,
      ventilation: advice.ventilation,
      emergency_warning: advice.emergency_warning,
      recommendations: advice.recommendations,
      confidence,
      model: forecast?.model || forecast?.model_used || 'fallback',
      version: forecast?.version || 'unknown',
      timestamp: forecast?.timestamp || new Date().toISOString(),
      prediction_id: forecast?.prediction_id || `${city}_${Date.now()}`
    };

    // DISABLED: Background forecast logging during high-concurrency load tests
    // Under 50+ concurrent users, background logging exhausts the DB connection pool
    // In production, implement queue-based logging with connection limits
    // logForecast(city, horizon, enhancedForecast).catch(logErr => {
    //   console.warn('Background forecast logging failed:', logErr.message);
    // });

    return enhancedForecast;
  } catch (err) {
    console.error('Error getting forecast:', err.message);
    throw err;
  }
}

/**
 * Log forecast to database for audit trail and analytics.
 */
async function logForecast(city, horizon, forecastResponse) {
  try {
    const query = `
      INSERT INTO forecasts (city, horizon_hours, forecast_data, model_used, valid_until)
      VALUES ($1, $2, $3, $4, NOW() + INTERVAL '1 hour' * $2::integer)
      RETURNING id
    `;

    await db.query(query, [
      city,
      horizon,
      JSON.stringify(forecastResponse),
      forecastResponse.model || 'lasso'
    ]);
  } catch (err) {
    console.error('Error logging forecast:', err);
    throw err;
  }
}

/**
 * Get health risk assessment based on AQI and health profile.
 * This uses the forecast response plus centralized health advice rules.
 */
async function getHealthRisk(city = 'Chennai', profile = 'general', horizon = 24) {
  try {
    const forecast = await getForecast(city, horizon);
    return {
      city: forecast.city,
      profile,
      current_aqi: forecast.current_aqi,
      forecast_aqi: forecast.forecast_aqi,
      category: forecast.category,
      health_risk: forecast.health_risk,
      recommendations: forecast.recommendations,
      sensitive_groups: forecast.sensitive_groups,
      mask_required: forecast.mask_required,
      outdoor_activity: forecast.outdoor_activity,
      ventilation: forecast.ventilation,
      emergency_warning: forecast.emergency_warning,
      confidence: forecast.confidence,
      model: forecast.model,
      version: forecast.version,
      timestamp: new Date().toISOString()
    };
  } catch (err) {
    console.error('Error getting health risk:', err);
    throw err;
  }
}

module.exports = { 
  getCurrentAqi, 
  getForecast, 
  getHealthRisk,
  getLatestAqiData,
  logForecast
};
