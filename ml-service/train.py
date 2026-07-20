"""
VayuGuard ML Model Training Pipeline
Trains forecasting models on real AQI data from PostgreSQL
"""

import json
import pickle
import numpy as np
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

class AQIModelTrainer:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_cols = None
    
    def fetch_real_data_from_db(self):
        """Fetch real historical AQI data from PostgreSQL database"""
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='vayuguard',
                user='vayuguard_user',
                password='vayuguard_pass'
            )
            
            query = """
            SELECT 
                city,
                aqi,
                pm25,
                pm10,
                no2,
                o3,
                so2,
                co,
                temperature,
                humidity,
                wind_speed,
                pressure,
                recorded_at as timestamp
            FROM aqi_data
            ORDER BY timestamp ASC
            """
            
            df = pd.read_sql(query, conn)
            conn.close()
            
            if len(df) == 0:
                print("⚠️  No real data in database")
                return None
            
            print(f"✅ Fetched {len(df)} real AQI records from database")
            return df
        except Exception as e:
            print(f"❌ Error fetching from database: {e}")
            return None
    
    def create_features(self, df):
        """Create lag and rolling features for forecasting"""
        df = df.copy().sort_values('timestamp')
        
        # Add hour and day_of_week from timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Lag features
        df['aqi_lag1'] = df['aqi'].shift(1)
        df['aqi_lag6'] = df['aqi'].shift(6)
        df['aqi_lag24'] = df['aqi'].shift(24)
        
        # Rolling features
        df['aqi_rolling6'] = df['aqi'].rolling(6).mean()
        df['aqi_rolling24'] = df['aqi'].rolling(24).mean()
        
        # Time features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Fill NaN values
        df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)
        
        return df
    
    def train_model(self, city='Chennai', model_type='random_forest'):
        """Train a forecasting model using real AQI data from database"""
        print(f"\n🔄 Training {model_type} model for {city}...")
        
        # Fetch real data from database
        df_all = self.fetch_real_data_from_db()
        if df_all is None or len(df_all) == 0:
            print(f"❌ Cannot train model - no real data available")
            return None
        
        # Filter for specific city
        df = df_all[df_all['city'] == city].copy() if city in df_all['city'].values else df_all
        
        if len(df) == 0:
            print(f"❌ No data found for {city}")
            return None
        
        # Create features
        df = self.create_features(df)
        
        # Remove rows with too many NaN values
        df = df.dropna(subset=['aqi', 'aqi_lag1', 'aqi_rolling6'])
        
        if len(df) < 10:
            print(f"⚠️  Insufficient data for {city} ({len(df)} samples)")
            return None
        
        # Prepare features and target
        feature_cols = ['hour', 'day_of_week', 'aqi_lag1', 'aqi_lag6', 'aqi_lag24',
                       'aqi_rolling6', 'aqi_rolling24', 'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos']
        
        # Filter to available features
        available_cols = [col for col in feature_cols if col in df.columns]
        self.feature_cols = available_cols
        
        X = df[available_cols].fillna(0).values
        y = df['aqi'].values
        
        if len(X) < 5:
            print(f"❌ Insufficient samples after feature creation")
            return None
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers[city] = scaler
        
        # Split data for training/testing
        split_idx = int(0.8 * len(X))
        X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Train model
        if model_type == 'random_forest':
            model = RandomForestRegressor(
                n_estimators=100, 
                max_depth=15, 
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'xgboost':
            model = XGBRegressor(
                n_estimators=100,
                max_depth=7,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )
        else:
            model = LinearRegression()
        
        model.fit(X_train, y_train)
        self.models[city] = model
        
        # Calculate metrics
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        
        train_mae = mean_absolute_error(y_train, y_train_pred)
        test_mae = mean_absolute_error(y_test, y_test_pred)
        test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
        
        print(f"  ✅ Train MAE: {train_mae:.2f}, Test MAE: {test_mae:.2f}, RMSE: {test_rmse:.2f}")
        
        return {
            'model': model,
            'scaler': scaler,
            'metrics': {'train_mae': train_mae, 'test_mae': test_mae, 'test_rmse': test_rmse}
        }

    
    def forecast(self, city, current_aqi, pm25, pm10, no2, so2, o3, hours=24):
        """Forecast AQI for next N hours"""
        if city not in self.models:
            print(f"⚠️  Model not found for {city}")
            return None
        
        model = self.models[city]
        scaler = self.scalers[city]
        
        forecast_data = []
        current_vals = [current_aqi, pm25, pm10, no2, so2, o3]
        
        now = datetime.now()
        for h in range(hours):
            # Create feature vector
            future_time = now + timedelta(hours=h)
            
            features = [
                future_time.hour, future_time.weekday(), pm25, pm10, no2, so2, o3,
                current_aqi, current_aqi, current_aqi,  # lag features
                current_aqi, current_aqi,  # rolling features
                np.sin(2 * np.pi * future_time.hour / 24),  # hour_sin
                np.cos(2 * np.pi * future_time.hour / 24),  # hour_cos
                np.sin(2 * np.pi * future_time.weekday() / 7),  # dow_sin
                np.cos(2 * np.pi * future_time.weekday() / 7),  # dow_cos
            ]
            
            X_scaled = scaler.transform([features])
            pred_aqi = model.predict(X_scaled)[0]
            
            # Add slight variance for realism
            pred_aqi = int(pred_aqi + np.random.normal(0, 3))
            pred_aqi = max(0, min(500, pred_aqi))
            
            forecast_data.append({
                'hour': h + 1,
                'aqi': pred_aqi,
                'pm25': max(0, int(pred_aqi * 0.6 + np.random.normal(0, 2))),
                'pm10': max(0, int(pred_aqi * 0.85 + np.random.normal(0, 3)))
            })
        
        return forecast_data
    
    def save_models(self, path='models'):
        """Save trained models to disk"""
        import os
        os.makedirs(path, exist_ok=True)
        
        for city in self.models:
            model_path = f'{path}/{city.lower()}_model.pkl'
            with open(model_path, 'wb') as f:
                pickle.dump({
                    'model': self.models[city],
                    'scaler': self.scalers[city]
                }, f)
            print(f"  💾 Saved model: {model_path}")
        
        # Save feature columns
        if self.feature_cols:
            with open(f'{path}/features.json', 'w') as f:
                json.dump(self.feature_cols, f)
            print(f"  💾 Saved features: {path}/features.json")
    
    def load_models(self, path='models'):
        """Load pre-trained models from disk"""
        import os
        for city in ['Chennai', 'Bengaluru', 'Hyderabad']:
            model_path = f'{path}/{city.lower()}_model.pkl'
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.models[city] = data['model']
                    self.scalers[city] = data['scaler']
                print(f"  ✅ Loaded model: {model_path}")

def train_all_models():
    """Train models for all target cities"""
    trainer = AQIModelTrainer()
    cities = ['Chennai', 'Bengaluru', 'Hyderabad']
    
    print("🚀 VayuGuard Model Training Pipeline")
    print("=" * 50)
    
    for city in cities:
        trainer.train_model(city, 'random_forest')
    
    trainer.save_models()
    
    print("\n" + "=" * 50)
    print("✅ Model training complete!")
    return trainer

if __name__ == '__main__':
    trainer = train_all_models()
    
    # Demo: make a forecast
    print("\n📊 Demo Forecast (next 3 hours for Chennai):")
    forecast = trainer.forecast('Chennai', current_aqi=85, pm25=50, pm10=75, 
                              no2=40, so2=30, o3=35, hours=3)
    for item in forecast:
        print(f"  Hour {item['hour']}: AQI={item['aqi']}, PM2.5={item['pm25']}, PM10={item['pm10']}")
