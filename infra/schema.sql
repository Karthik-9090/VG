-- VayuGuard Database Schema

-- Drop existing objects
DROP TYPE IF EXISTS user_role CASCADE;
DROP TYPE IF EXISTS health_profile_type CASCADE;
DROP TYPE IF EXISTS alert_comparison CASCADE;
DROP TYPE IF EXISTS alert_type CASCADE;
DROP TYPE IF EXISTS aqi_category CASCADE;

-- Enums
CREATE TYPE user_role AS ENUM ('admin', 'user');
CREATE TYPE health_profile_type AS ENUM ('general', 'respiratory', 'cardiac', 'children', 'elderly');
CREATE TYPE alert_comparison AS ENUM ('gt', 'lt', 'eq');
CREATE TYPE alert_type AS ENUM ('aqi_threshold', 'health_risk');
CREATE TYPE aqi_category AS ENUM ('Good', 'Satisfactory', 'Moderately Polluted', 'Heavily Polluted', 'Severely Polluted');

-- Users table
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  role user_role DEFAULT 'user',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Health profiles table
CREATE TABLE health_profiles (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id) ON DELETE CASCADE,
  profile_type health_profile_type NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, profile_type)
);

-- AQI data table
CREATE TABLE aqi_data (
  id SERIAL PRIMARY KEY,
  city VARCHAR(100) NOT NULL,
  aqi INT NOT NULL,
  category aqi_category,
  pm25 FLOAT,
  pm10 FLOAT,
  no2 FLOAT,
  o3 FLOAT,
  so2 FLOAT,
  co FLOAT,
  temperature FLOAT,
  humidity FLOAT,
  wind_speed FLOAT,
  pressure FLOAT,
  recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weather data table
CREATE TABLE weather_data (
  id SERIAL PRIMARY KEY,
  city VARCHAR(100) NOT NULL,
  temperature FLOAT,
  humidity FLOAT,
  wind_speed FLOAT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Forecasts table
CREATE TABLE forecasts (
  id SERIAL PRIMARY KEY,
  city VARCHAR(100) NOT NULL,
  horizon_hours INT,
  forecast_data JSONB,
  model_used VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  valid_until TIMESTAMP
);

-- Alerts table
CREATE TABLE alerts (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id) ON DELETE CASCADE,
  city VARCHAR(100) NOT NULL,
  alert_type alert_type,
  comparison alert_comparison,
  threshold INT,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model metadata table
CREATE TABLE model_metadata (
  id SERIAL PRIMARY KEY,
  model_name VARCHAR(100) NOT NULL,
  model_version VARCHAR(50),
  performance_metrics JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data ingestion logs table
CREATE TABLE ingestion_logs (
  id SERIAL PRIMARY KEY,
  data_source VARCHAR(100),
  records_ingested INT,
  status VARCHAR(50),
  error_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_aqi_city_time ON aqi_data(city, timestamp DESC);
CREATE INDEX idx_weather_city_time ON weather_data(city, timestamp DESC);
CREATE INDEX idx_alerts_user ON alerts(user_id);
CREATE INDEX idx_forecasts_city_time ON forecasts(city, created_at DESC);
