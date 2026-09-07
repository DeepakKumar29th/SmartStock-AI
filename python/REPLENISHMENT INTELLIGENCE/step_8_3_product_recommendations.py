# ============================================================
# SMARTSTOCK AI
# STEP 8.3 - PRODUCT REPLENISHMENT RECOMMENDATIONS
# ============================================================

import psycopg2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

DB = get_psycopg2_config()

print("=" * 70)
print("SMARTSTOCK AI - STEP 8.3")
print("Product-wise Replenishment Recommendations")
print("=" * 70)

conn = psycopg2.connect(**DB)
cur = conn.cursor()

# ------------------------------------------------------------
# Create product recommendation table
# ------------------------------------------------------------
cur.execute("""
DROP TABLE IF EXISTS ml.product_recommendations;

CREATE TABLE ml.product_recommendations AS

SELECT
    fr.product_id,
    dp.management_group_id,
    dp.first_category_id,
    dp.second_category_id,
    dp.third_category_id,

    COUNT(*) AS observations,

    ROUND(SUM(fr.actual_sales)::numeric,2) AS total_sales,
    ROUND(SUM(fr.predicted_sales)::numeric,2) AS predicted_sales,

    SUM(CASE WHEN fr.stockout_risk='HIGH' THEN 1 ELSE 0 END) AS high_risk_days,
    SUM(CASE WHEN fr.replenishment_priority='HIGH' THEN 1 ELSE 0 END) AS urgent_reorders,

    ROUND(AVG(fr.recommended_reorder_qty)::numeric,2) AS avg_reorder_qty,

    ROUND(
        100.0 *
        SUM(CASE WHEN fr.stockout_risk='HIGH' THEN 1 ELSE 0 END)
        / COUNT(*),
        2
    ) AS high_risk_pct

FROM ml.forecast_recommendations fr

JOIN core.dim_product dp
ON fr.product_id = dp.product_id

GROUP BY
    fr.product_id,
    dp.management_group_id,
    dp.first_category_id,
    dp.second_category_id,
    dp.third_category_id;
""")

conn.commit()

print("PASS: Product recommendation table created.")

# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------
cur.execute("""
SELECT COUNT(*)
FROM ml.product_recommendations;
""")

products = cur.fetchone()[0]

print(f"\nTotal Products : {products}")

print("\nTop 10 Highest Priority Products")
print("-" * 70)

cur.execute("""
SELECT
    product_id,
    observations,
    total_sales,
    predicted_sales,
    high_risk_days,
    urgent_reorders,
    avg_reorder_qty,
    high_risk_pct

FROM ml.product_recommendations

ORDER BY urgent_reorders DESC,
         predicted_sales DESC

LIMIT 10;
""")

rows = cur.fetchall()

for r in rows:
    print(r)

cur.close()
conn.close()

print("\nPASS: STEP 8.3 COMPLETED")
