# ============================================================
# SMARTSTOCK AI
# STEP 7.3 - PRODUCTION RANDOM FOREST + SAVE MODEL
# ============================================================

import os
import joblib
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

# ------------------------------------------------------------
# PostgreSQL
# ------------------------------------------------------------
DB = get_psycopg2_config()

engine = create_engine(
    f"postgresql+psycopg2://{DB['user']}:{DB['password']}@{DB['host']}:{DB['port']}/{DB['dbname']}"
)

FEATURES = [
    "sale_amount","lag_1_sales","lag_3_sales","lag_7_sales",
    "rolling_3_mean","rolling_7_mean","rolling_7_std",
    "stock_hour6_22_cnt","total_stockout_hours",
    "discount","holiday_flag","activity_flag",
    "precpt","avg_temperature","avg_humidity",
    "avg_wind_level","day_of_week","week_of_year","month"
]

TARGET = "target_next_day_sales"

print("="*70)
print("SMARTSTOCK AI - STEP 7.3")
print("Production Model + Save")
print("="*70)

# ------------------------------------------------------------
# Load training data
# ------------------------------------------------------------
train = pd.read_sql(
    f"SELECT {','.join(FEATURES)}, {TARGET} FROM ml.train_dataset",
    engine
)

X = train[FEATURES].fillna(0)
y = train[TARGET]

# ------------------------------------------------------------
# Train final model
# ------------------------------------------------------------
model = RandomForestRegressor(
    n_estimators=100,
    max_depth=20,
    random_state=42,
    n_jobs=-1
)

print("\nTraining final model...")
model.fit(X, y)

print("PASS: Final model trained.")

# ------------------------------------------------------------
# Save model
# ------------------------------------------------------------
os.makedirs("models", exist_ok=True)

model_path = "models/random_forest_model.pkl"

joblib.dump(model, model_path)

print("\nPASS: Model saved.")
print("Location :", model_path)

# ------------------------------------------------------------
# Feature importance
# ------------------------------------------------------------
importance = pd.DataFrame({
    "Feature": FEATURES,
    "Importance": model.feature_importances_
}).sort_values("Importance", ascending=False)

print("\nTop 10 Important Features")
print("-"*45)

for _, row in importance.head(10).iterrows():
    print(f"{row['Feature']:<25} {row['Importance']:.4f}")

importance.to_csv(
    "models/feature_importance.csv",
    index=False
)

print("\nPASS: Feature importance exported.")
print("\nSTEP 7.3 COMPLETED")
