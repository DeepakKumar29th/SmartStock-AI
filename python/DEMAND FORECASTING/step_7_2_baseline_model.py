# ============================================================
# SMARTSTOCK AI
# STEP 7.2 - BASELINE RANDOM FOREST MODEL
# ============================================================

import psycopg2
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

DB = get_psycopg2_config()

print("="*70)
print("SMARTSTOCK AI - STEP 7.2")
print("Baseline Random Forest Model")
print("="*70)

engine = create_engine(
    f"postgresql+psycopg2://{DB['user']}:{DB['password']}@{DB['host']}:{DB['port']}/{DB['dbname']}"
)

# ------------------------------------------------------------
# Load only ML columns
# ------------------------------------------------------------

FEATURES = [
    "sale_amount",
    "lag_1_sales",
    "lag_3_sales",
    "lag_7_sales",
    "rolling_3_mean",
    "rolling_7_mean",
    "rolling_7_std",
    "stock_hour6_22_cnt",
    "total_stockout_hours",
    "discount",
    "holiday_flag",
    "activity_flag",
    "precpt",
    "avg_temperature",
    "avg_humidity",
    "avg_wind_level",
    "day_of_week",
    "week_of_year",
    "month"
]

TARGET = "target_next_day_sales"

print("\nLoading training data...")

train = pd.read_sql(
    f"""
    SELECT {",".join(FEATURES)}, {TARGET}
    FROM ml.train_dataset
    """,
    engine
)

print("Training rows:", len(train))

print("\nLoading testing data...")

test = pd.read_sql(
    f"""
    SELECT {",".join(FEATURES)}, {TARGET}
    FROM ml.test_dataset
    """,
    engine
)

print("Testing rows:", len(test))

# ------------------------------------------------------------
# Prepare data
# ------------------------------------------------------------

X_train = train[FEATURES].fillna(0)
y_train = train[TARGET]

X_test = test[FEATURES].fillna(0)
y_test = test[TARGET]

# ------------------------------------------------------------
# Train model
# ------------------------------------------------------------

print("\nTraining Random Forest...")

model = RandomForestRegressor(
    n_estimators=100,
    max_depth=20,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

print("PASS: Model trained.")

# ------------------------------------------------------------
# Prediction
# ------------------------------------------------------------

pred = model.predict(X_test)

mae = mean_absolute_error(y_test, pred)
rmse = np.sqrt(mean_squared_error(y_test, pred))
r2 = r2_score(y_test, pred)

print("\n" + "="*70)
print("MODEL PERFORMANCE")
print("="*70)

print(f"MAE  : {mae:.4f}")
print(f"RMSE : {rmse:.4f}")
print(f"R²   : {r2:.4f}")

print("\nPASS: STEP 7.2 completed successfully.")
































