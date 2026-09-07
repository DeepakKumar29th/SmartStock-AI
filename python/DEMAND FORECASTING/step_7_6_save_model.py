# ============================================================
# SMARTSTOCK AI
# STEP 7.6 - SAVE PREDICTIONS
# ============================================================

import os
import joblib
import pandas as pd
from sqlalchemy import create_engine
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

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

print("=" * 70)
print("SMARTSTOCK AI - STEP 7.6")
print("Generate Prediction Table")
print("=" * 70)

# ------------------------------------------------------------
# Load model
# ------------------------------------------------------------
model = joblib.load("models/random_forest_model.pkl")

# ------------------------------------------------------------
# Load test dataset
# ------------------------------------------------------------
query = f"""
SELECT
    store_id,
    product_id,
    dt,
    target_next_day_sales,
    stockout_risk,
    {",".join(FEATURES)}
FROM ml.test_dataset
"""

df = pd.read_sql(query, engine)

print("Rows loaded:", len(df))

# ------------------------------------------------------------
# Predict
# ------------------------------------------------------------
X = df[FEATURES].fillna(0)

df["predicted_sales"] = model.predict(X)

# ------------------------------------------------------------
# Keep final columns
# ------------------------------------------------------------
predictions = df[[
    "store_id",
    "product_id",
    "dt",
    "target_next_day_sales",
    "predicted_sales",
    "stockout_risk"
]].copy()

predictions.rename(columns={
    "target_next_day_sales": "actual_sales"
}, inplace=True)

# ------------------------------------------------------------
# Save CSV
# ------------------------------------------------------------
os.makedirs("data/processed", exist_ok=True)

csv_path = "data/processed/demand_predictions.csv"

predictions.to_csv(csv_path, index=False)

print("\nPASS: CSV exported.")
print(csv_path)

# ------------------------------------------------------------
# Save to PostgreSQL
# ------------------------------------------------------------
predictions.to_sql(
    "demand_predictions",
    engine,
    schema="ml",
    if_exists="replace",
    index=False
)

print("PASS: PostgreSQL table created.")

print("\nSample")
print(predictions.head())

print("\nRows exported:", len(predictions))

print("\nSTEP 7.6 COMPLETED")
