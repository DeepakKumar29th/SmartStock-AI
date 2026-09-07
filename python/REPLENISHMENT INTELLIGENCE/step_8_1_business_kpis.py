# ============================================================
# SMARTSTOCK AI
# STEP 8.1 - BUSINESS KPI TABLE
# ============================================================

import psycopg2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

DB = get_psycopg2_config()

print("=" * 70)
print("SMARTSTOCK AI - STEP 8.1")
print("Business KPI Table")
print("=" * 70)

conn = psycopg2.connect(**DB)
cur = conn.cursor()

# ------------------------------------------------------------
# Create KPI table
# ------------------------------------------------------------
cur.execute("""
DROP TABLE IF EXISTS ml.business_kpis;

CREATE TABLE ml.business_kpis AS

SELECT
    COUNT(*) AS total_predictions,
    COUNT(DISTINCT store_id) AS total_stores,
    COUNT(DISTINCT product_id) AS total_products,

    ROUND(SUM(actual_sales)::numeric,2) AS total_actual_sales,
    ROUND(SUM(predicted_sales)::numeric,2) AS total_predicted_sales,

    ROUND(AVG(actual_sales)::numeric,4) AS avg_actual_sales,
    ROUND(AVG(predicted_sales)::numeric,4) AS avg_predicted_sales,

    SUM(CASE WHEN stockout_risk='HIGH' THEN 1 ELSE 0 END) AS high_risk_products,
    SUM(CASE WHEN stockout_risk='MEDIUM' THEN 1 ELSE 0 END) AS medium_risk_products,
    SUM(CASE WHEN stockout_risk='LOW' THEN 1 ELSE 0 END) AS low_risk_products,

    SUM(CASE WHEN replenishment_priority='HIGH' THEN 1 ELSE 0 END) AS high_priority_reorders,
    SUM(CASE WHEN replenishment_priority='MEDIUM' THEN 1 ELSE 0 END) AS medium_priority_reorders,
    SUM(CASE WHEN replenishment_priority='LOW' THEN 1 ELSE 0 END) AS low_priority_reorders,

    ROUND(AVG(recommended_reorder_qty)::numeric,2) AS avg_reorder_qty

FROM ml.forecast_recommendations;
""")

conn.commit()

print("PASS: KPI table created.")

# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------
cur.execute("SELECT * FROM ml.business_kpis;")
row = cur.fetchone()

cols = [d[0] for d in cur.description]

print("\n" + "=" * 70)
print("BUSINESS KPIs")
print("=" * 70)

for c, v in zip(cols, row):
    print(f"{c:<30} {v}")

cur.close()
conn.close()

print("\nPASS: STEP 8.1 COMPLETED")
