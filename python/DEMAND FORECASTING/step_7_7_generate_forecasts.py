# ============================================================
# SMARTSTOCK AI
# STEP 7.7 - FINAL FORECAST & REPLENISHMENT TABLE
# ============================================================

import os
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

print("=" * 70)
print("SMARTSTOCK AI - STEP 7.7")
print("Final Forecast & Replenishment Table")
print("=" * 70)

# ------------------------------------------------------------
# Load prediction table
# ------------------------------------------------------------
query = """
SELECT
    p.store_id,
    p.product_id,
    p.dt,
    p.actual_sales,
    p.predicted_sales,
    p.stockout_risk,
    d.management_group_id,
    d.first_category_id,
    d.second_category_id,
    d.third_category_id
FROM ml.demand_predictions p
JOIN core.dim_product d
ON p.product_id = d.product_id
"""

df = pd.read_sql(query, engine)

print("Rows loaded:", len(df))

# ------------------------------------------------------------
# Business Logic
# ------------------------------------------------------------
df["recommended_reorder_qty"] = (
    (df["predicted_sales"] * 7).round().clip(lower=1)
)

df["replenishment_priority"] = "LOW"

df.loc[
    (df["stockout_risk"] == "MEDIUM") &
    (df["predicted_sales"] >= 1),
    "replenishment_priority"
] = "MEDIUM"

df.loc[
    (df["stockout_risk"] == "HIGH") &
    (df["predicted_sales"] >= 1.5),
    "replenishment_priority"
] = "HIGH"

# ------------------------------------------------------------
# Save PostgreSQL
# ------------------------------------------------------------
df.to_sql(
    "forecast_recommendations",
    engine,
    schema="ml",
    if_exists="replace",
    index=False
)

print("PASS: PostgreSQL table created.")

# ------------------------------------------------------------
# Export CSV
# ------------------------------------------------------------
os.makedirs("data/processed", exist_ok=True)

csv_path = "data/processed/forecast_recommendations.csv"

df.to_csv(csv_path, index=False)

print("PASS: CSV exported.")

# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------
summary = (
    df.groupby("replenishment_priority")
      .size()
      .reset_index(name="products")
)

print("\n" + "=" * 70)
print("REPLENISHMENT SUMMARY")
print("=" * 70)

print(summary)

print("\nTop 10 High Priority Products")

top = (
    df[df["replenishment_priority"] == "HIGH"]
      .sort_values("predicted_sales", ascending=False)
      [["store_id","product_id","predicted_sales",
        "recommended_reorder_qty","stockout_risk"]]
      .head(10)
)

print(top)

print("\nRows exported:", len(df))
print("\nSTEP 7 COMPLETED SUCCESSFULLY")
