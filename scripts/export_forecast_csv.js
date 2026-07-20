const fs = require('fs');
const path = require('path');
const inFile = path.join(__dirname, '..', 'forecast_48.json');
const outDir = path.join(__dirname, '..', 'exports');
const outFile = path.join(outDir, 'forecast_Chennai_48.csv');

if (!fs.existsSync(inFile)) {
  console.error('Input file not found:', inFile);
  process.exit(2);
}

const raw = fs.readFileSync(inFile, 'utf8');
const data = JSON.parse(raw);

const rows = [
  ['Forecast Report', `${data.city} (${data.horizon} hours)`],
  ['Generated', new Date().toLocaleString()],
  [''],
  ['CURRENT CONDITIONS'],
  ['City', data.city],
  ['Current AQI', data.current_aqi],
  ['Forecast End AQI', data.forecast_aqi],
  ['Category', data.category],
  ['Confidence', data.confidence],
  [''],
  ['CURRENT POLLUTANTS'],
  ...Object.entries(data.current_pollutants || {}).map(([key, value]) => [key.replace('_', '.').toUpperCase(), value]),
  [''],
  ['HEALTH RECOMMENDATIONS'],
  ['Health Risk', data.health_risk],
  ['Mask Required', data.mask_required ? 'Yes' : 'No'],
  ['Outdoor Activity', data.outdoor_activity],
  ['Ventilation', data.ventilation],
  ['Emergency Warning', data.emergency_warning],
  ...((data.recommendations || []).length > 0 ? [[''], ['RECOMMENDATIONS'], ...data.recommendations.map((rec, idx) => [`Recommendation ${idx + 1}`, rec])] : []),
  [''],
  ['### Hourly Forecast'],
  ['Hour', 'Timestamp', 'AQI', 'Category']
];

if (data.forecast_timeseries && data.forecast_timeseries.length > 0) {
  data.forecast_timeseries.forEach(point => {
    rows.push([
      `Hour ${point.hour}`,
      point.timestamp,
      point.aqi,
      point.category
    ]);
  });
}

const csv = rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n');

fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(outFile, csv, 'utf8');
console.log('Wrote', outFile);
