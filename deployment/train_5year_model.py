"""
FloodGuard AI — Real-Data Model Training Script
Trains on genuine OPW Waterworks Weir data (2019-present).

Usage:
    python train_5year_model.py

Required files in same directory:
    waterworks_level.csv   — OPW level data (station 19102)
    waterworks_temp.csv    — OPW water temperature data (station 19102)

Optional (fetched automatically if internet available):
    Historical rainfall from Open-Meteo archive API (Cork City)

Output:
    flood_model_5y.pkl  — trained GradientBoosting model dict
"""

import os, warnings
import pandas as pd
import numpy as np
from io import StringIO
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error
import joblib

warnings.filterwarnings('ignore')

DIR        = os.path.dirname(__file__)
MODEL_PATH = os.path.join(DIR, "flood_model_5y.pkl")
LEVEL_CSV  = os.path.join(DIR, "waterworks_level.csv")
TEMP_CSV   = os.path.join(DIR, "waterworks_temp.csv")

FEATURES = [
    'lag_1h',  'lag_3h',  'lag_6h',  'lag_12h', 'lag_24h', 'lag_48h',
    'rise_1h', 'rise_3h', 'rise_6h',
    'roll_mean_6h', 'roll_mean_24h', 'roll_std_6h', 'roll_max_24h',
    'temp', 'hour_sin', 'hour_cos', 'month_sin', 'month_cos',
]

def parse_opw(path, value_col):
    """Parse OPW semicolon-delimited CSV, keep quality codes 254/31/32."""
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    data_lines = [l.strip() for l in lines if l.strip() and not l.startswith('#')]
    df = pd.read_csv(StringIO('\n'.join(data_lines)), sep=';', header=None,
                     names=['timestamp', value_col, 'quality'], on_bad_lines='skip')
    df['timestamp'] = pd.to_datetime(df['timestamp'],
                          format='%Y-%m-%dT%H:%M:%S.%fZ', utc=True, errors='coerce')
    df[value_col]   = pd.to_numeric(df[value_col], errors='coerce')
    df['quality']   = pd.to_numeric(df['quality'],  errors='coerce')
    # Quality codes: 254=excellent, 31=good, 32=estimated | 101=suspect, -1=missing
    df = df[df['quality'].isin([254, 31, 32]) & df[value_col].notna()]
    return df[['timestamp', value_col]].dropna().sort_values('timestamp').reset_index(drop=True)

def fetch_rainfall(start_date, end_date):
    """Fetch hourly Cork rainfall from Open-Meteo archive API (free, no key)."""
    try:
        import requests
        r = requests.get("https://archive-api.open-meteo.com/v1/archive", params={
            "latitude": 51.8985, "longitude": -8.4756,
            "start_date": start_date, "end_date": end_date,
            "hourly": "precipitation", "timezone": "UTC"
        }, timeout=30)
        if r.status_code == 200:
            data = r.json()
            rain_df = pd.DataFrame({
                'timestamp': pd.to_datetime(data['hourly']['time'], utc=True),
                'precip_mm': data['hourly']['precipitation']
            })
            print(f"   Fetched {len(rain_df):,} hourly rainfall readings from Open-Meteo")
            return rain_df
    except Exception as e:
        print(f"   Rainfall fetch failed ({e}) - model will train without rainfall feature")
    return None

# ============================================================
print("=" * 60)
print("  FloodGuard AI - Real-Data Model Training")
print("=" * 60)

print(f"\nLoading OPW data...")
assert os.path.exists(LEVEL_CSV), f"Missing: {LEVEL_CSV}"
assert os.path.exists(TEMP_CSV),  f"Missing: {TEMP_CSV}"

level = parse_opw(LEVEL_CSV, 'level')
temp  = parse_opw(TEMP_CSV,  'temp')
print(f"   Level : {len(level):,} rows  "
      f"{level['timestamp'].min().date()} to {level['timestamp'].max().date()}")
print(f"   Temp  : {len(temp):,} rows")

# Resample level to regular 15-min grid, interpolate gaps up to 2 hours
level = (level.set_index('timestamp')
              .resample('15min').mean()
              .interpolate(method='time', limit=8)
              .reset_index())

# Temperature hourly -> forward-fill to 15-min
temp = (temp.set_index('timestamp')
             .resample('15min').ffill()
             .reset_index())

# Merge level + temp
df = pd.merge_asof(level.sort_values('timestamp'),
                   temp.sort_values('timestamp'),
                   on='timestamp', direction='nearest',
                   tolerance=pd.Timedelta('1h'))

# Optional rainfall
print(f"\nFetching historical rainfall (Cork City)...")
rain_df = fetch_rainfall(str(level['timestamp'].min().date()),
                         str(level['timestamp'].max().date()))
if rain_df is not None:
    rain_df = rain_df.set_index('timestamp').resample('15min').ffill().reset_index()
    df = pd.merge_asof(df.sort_values('timestamp'),
                       rain_df.sort_values('timestamp'),
                       on='timestamp', direction='nearest',
                       tolerance=pd.Timedelta('1h'))
    df['precip_mm'] = df['precip_mm'].fillna(0)
    FEATURES.append('precip_mm')
    print(f"   Rainfall feature added")

print(f"\nEngineering features...")
for name, steps in [('1h',4),('3h',12),('6h',24),('12h',48),('24h',96),('48h',192)]:
    df[f'lag_{name}'] = df['level'].shift(steps)
df['rise_1h']       = df['level'] - df['lag_1h']
df['rise_3h']       = df['level'] - df['lag_3h']
df['rise_6h']       = df['level'] - df['lag_6h']
df['roll_mean_6h']  = df['level'].rolling(24,  min_periods=4).mean()
df['roll_mean_24h'] = df['level'].rolling(96,  min_periods=4).mean()
df['roll_std_6h']   = df['level'].rolling(24,  min_periods=4).std()
df['roll_max_24h']  = df['level'].rolling(96,  min_periods=4).max()
df['hour_sin']      = np.sin(2*np.pi*df['timestamp'].dt.hour  / 24)
df['hour_cos']      = np.cos(2*np.pi*df['timestamp'].dt.hour  / 24)
df['month_sin']     = np.sin(2*np.pi*df['timestamp'].dt.month / 12)
df['month_cos']     = np.cos(2*np.pi*df['timestamp'].dt.month / 12)
df['temp']          = df['temp'].fillna(df['temp'].median())
df['target']        = df['level'].shift(-24)
df = df.dropna(subset=FEATURES + ['target']).reset_index(drop=True)

print(f"   {len(df):,} usable rows after feature engineering")
print(f"   Level distribution:")
print(f"     Normal  (<2.2m) : {(df['level']<2.2).mean()*100:.1f}%")
print(f"     Alert (2.2-2.8m): {((df['level']>=2.2)&(df['level']<2.8)).mean()*100:.1f}%")
print(f"     Flood (2.8-3.4m): {((df['level']>=2.8)&(df['level']<3.4)).mean()*100:.1f}%")
print(f"     Critical (>3.4m): {(df['level']>=3.4).mean()*100:.1f}%")

# Train/test split - time ordered, last 15% as test
split   = int(len(df) * 0.85)
X_train = df[FEATURES].iloc[:split]
X_test  = df[FEATURES].iloc[split:]
y_train = df['target'].iloc[:split]
y_test  = df['target'].iloc[split:]
print(f"\nSplit: {len(X_train):,} train / {len(X_test):,} test")
print(f"   Train: {df['timestamp'].iloc[0].date()} to {df['timestamp'].iloc[split].date()}")
print(f"   Test : {df['timestamp'].iloc[split].date()} to {df['timestamp'].iloc[-1].date()}")

print(f"\nTraining Gradient Boosting Regressor...")
model = GradientBoostingRegressor(
    n_estimators=150, max_depth=5, learning_rate=0.08,
    min_samples_leaf=20, subsample=0.8, random_state=42
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
r2  = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)

print(f"\nModel Performance (out-of-sample):")
print(f"   R2 Score : {r2:.4f}  (1.0 = perfect)")
print(f"   MAE      : {mae:.4f}m  ({mae*100:.1f}cm avg error on 6-hour forecast)")
print(f"   {'PRODUCTION READY - Accuracy exceeds 85% threshold' if r2 > 0.85 else 'CHECK DATA - below threshold'}")

# Storm Babet check
babet = df[(df['timestamp'] >= '2023-10-17') & (df['timestamp'] <= '2023-10-22')]
if len(babet) > 0:
    bp = model.predict(babet[FEATURES])
    bt = babet['target'].values
    print(f"\nStorm Babet Validation (Oct 17-22 2023):")
    print(f"   Actual peak   : {bt.max():.3f}m")
    print(f"   Predicted peak: {bp.max():.3f}m  (error: {abs(bt.max()-bp.max())*100:.1f}cm)")
    print(f"   MAE during event: {mean_absolute_error(bt, bp):.4f}m")

print(f"\nFeature Importances:")
for feat, imp in sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1]):
    bar = 'X' * int(imp * 50)
    print(f"   {feat:<20} {bar} {imp:.3f}")

joblib.dump({
    'model':       model,
    'features':    FEATURES,
    'thresholds':  {'Alert': 2.2, 'Flood': 2.8, 'Critical': 3.4},
    'trained_on':  f"Real OPW data 2019-{df['timestamp'].max().year}, "
                   f"Waterworks Weir 19102 ({len(df):,} records)",
    'horizon_hours':  6,
    'step_minutes':   15,
    'r2':          round(r2, 4),
    'mae_m':       round(mae, 4),
}, MODEL_PATH)

print(f"\nModel saved: {MODEL_PATH}")
print("=" * 60)
print("  Training complete. Run: streamlit run floodguard_live.py")
print("=" * 60)
