# ============================================================
# SMARTSTOCK AI
# STEP 8.2 - STORE REPLENISHMENT RECOMMENDATIONS
# ============================================================

import psycopg2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

DB = get_psycopg2_config()

print("=" * 70)
print("SMARTSTOCK AI - STEP 8.2")
print("Store-wise Replenishment Recommendations")
print("=" * 70)

conn = psycopg2.connect(**DB)
cur = conn.cursor()

# ------------------------------------------------------------
# Create store recommendation table
# ------------------------------------------------------------
cur.execute("""
DROP TABLE IF EXISTS ml.store_recommendations;

CREATE TABLE ml.store_recommendations AS

SELECT
    store_id,

    COUNT(*) AS products,

    ROUND(SUM(actual_sales)::numeric,2) AS total_sales,
    ROUND(SUM(predicted_sales)::numeric,2) AS predicted_sales,

    SUM(CASE WHEN stockout_risk='HIGH' THEN 1 ELSE 0 END) AS high_risk_products,
    SUM(CASE WHEN replenishment_priority='HIGH' THEN 1 ELSE 0 END) AS urgent_reorders,

    ROUND(AVG(recommended_reorder_qty)::numeric,2) AS avg_reorder_qty,

    ROUND(
        100.0 *
        SUM(CASE WHEN stockout_risk='HIGH' THEN 1 ELSE 0 END)
        / COUNT(*),
        2
    ) AS high_risk_pct

FROM ml.forecast_recommendations

GROUP BY store_id;
""")

conn.commit()

print("PASS: Store recommendation table created.")

# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------
cur.execute("""
SELECT COUNT(*)
FROM ml.store_recommendations;
""")

stores = cur.fetchone()[0]

print(f"\nTotal Stores : {stores}")

print("\nTop 10 Highest Risk Stores")
print("-" * 70)

cur.execute("""
SELECT
    store_id,
    products,
    high_risk_products,
    urgent_reorders,
    predicted_sales,
    high_risk_pct

FROM ml.store_recommendations

ORDER BY high_risk_products DESC,
         predicted_sales DESC

LIMIT 10;
""")

rows = cur.fetchall()

for r in rows:
    print(r)

cur.close()
conn.close()

print("\nPASS: STEP 8.2 COMPLETED")
