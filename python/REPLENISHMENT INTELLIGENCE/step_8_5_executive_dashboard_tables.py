# ============================================================
# SMARTSTOCK AI
# STEP 8.5 - EXECUTIVE DASHBOARD TABLES
# ============================================================

import psycopg2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

DB = get_psycopg2_config()

print("=" * 70)
print("SMARTSTOCK AI - STEP 8.5")
print("Executive Dashboard Tables")
print("=" * 70)

conn = psycopg2.connect(**DB)
cur = conn.cursor()

# ------------------------------------------------------------
# Top 20 High Priority Products
# ------------------------------------------------------------

cur.execute("""
DROP TABLE IF EXISTS ml.dashboard_top20_products;

CREATE TABLE ml.dashboard_top20_products AS

SELECT
    fr.store_id,
    fr.product_id,

    dp.management_group_id,
    dp.first_category_id,
    dp.second_category_id,
    dp.third_category_id,

    fr.actual_sales,
    fr.predicted_sales,
    fr.stockout_risk,
    fr.recommended_reorder_qty,
    fr.replenishment_priority

FROM ml.forecast_recommendations fr

JOIN core.dim_product dp
ON fr.product_id = dp.product_id

WHERE fr.replenishment_priority = 'HIGH'

ORDER BY
    fr.predicted_sales DESC,
    fr.recommended_reorder_qty DESC

LIMIT 20;
""")

conn.commit()

print("PASS: Dashboard Top20 table created.")

# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

cur.execute("""
SELECT COUNT(*)
FROM ml.dashboard_top20_products;
""")

count = cur.fetchone()[0]

print(f"\nTop 20 Rows : {count}")

print("\nTop 20 Products")
print("-" * 70)

cur.execute("""
SELECT
    store_id,
    product_id,
    predicted_sales,
    recommended_reorder_qty,
    stockout_risk

FROM ml.dashboard_top20_products;
""")

for row in cur.fetchall():
    print(row)

cur.close()
conn.close()

print("\nPASS: STEP 8.5 COMPLETED")
