# ============================================================
# SMARTSTOCK AI
# STEP 7.5 - MODEL EVALUATION REPORT
# ============================================================

import os
import joblib
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

# ------------------------------------------------------------
# PostgreSQL
# ------------------------------------------------------------
DB = get_psycopg2_config()

engine = create_engine(
    f"postgresql+psycopg2://{DB['user']}:{DB['password']}@"
    f"{DB['host']}:{DB['port']}/{DB['dbname']}"
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
print("SMARTSTOCK AI - STEP 7.5")
print("Model Evaluation Report")
print("="*70)

# ------------------------------------------------------------
# Load model
# ------------------------------------------------------------
model = joblib.load("models/random_forest_model.pkl")

# ------------------------------------------------------------
# Load test data
# ------------------------------------------------------------
test = pd.read_sql(
    f"""
    SELECT {','.join(FEATURES)}, {TARGET}
    FROM ml.test_dataset
    """,
    engine
)

X_test = test[FEATURES].fillna(0)
y_test = test[TARGET]

print("Testing rows:", len(test))

# ------------------------------------------------------------
# Predict
# ------------------------------------------------------------
pred = model.predict(X_test)

mae = mean_absolute_error(y_test, pred)
rmse = np.sqrt(mean_squared_error(y_test, pred))
r2 = r2_score(y_test, pred)

# ------------------------------------------------------------
# MAPE
# ------------------------------------------------------------
mask = y_test != 0

mape = (
    np.abs((y_test[mask] - pred[mask]) / y_test[mask])
).mean() * 100

# ------------------------------------------------------------
# Report
# ------------------------------------------------------------
print("\n" + "="*70)
print("FINAL MODEL METRICS")
print("="*70)

print(f"MAE  : {mae:.4f}")
print(f"RMSE : {rmse:.4f}")
print(f"R²   : {r2:.4f}")
print(f"MAPE : {mape:.2f}%")

# ------------------------------------------------------------
# Save report
# ------------------------------------------------------------
os.makedirs("models", exist_ok=True)

report = pd.DataFrame({
    "Metric": ["MAE","RMSE","R2","MAPE"],
    "Value": [mae, rmse, r2, mape]
})

report.to_csv("models/model_metrics.csv", index=False)

print("\nPASS: Metrics saved.")
print("File: models/model_metrics.csv")

print("\nSTEP 7.5 COMPLETED")
