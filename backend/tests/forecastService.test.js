jest.mock('node-fetch', () => jest.fn());

const fetch = require('node-fetch');
const db = require('../db');
const forecastService = require('../services/forecastService');

describe('forecastService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('falls back to a usable AQI row when the latest record is incomplete', async () => {
    db.query = jest.fn()
      .mockResolvedValueOnce({
        rows: [{
          aqi: 88,
          pm25: 34,
          pm10: 40,
          no2: 18,
          so2: null,
          co: 0.7,
          o3: 30,
          recorded_at: '2024-01-01T00:00:00Z'
        }]
      });

    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ forecast_aqi: 96, confidence: 0.91, city: 'Chennai' })
    });

    const result = await forecastService.getForecast('Chennai', 24);

    expect(result.forecast_aqi).toBe(96);
    expect(result.current_aqi).toBe(88);
    expect(fetch).toHaveBeenCalled();
  });
});
