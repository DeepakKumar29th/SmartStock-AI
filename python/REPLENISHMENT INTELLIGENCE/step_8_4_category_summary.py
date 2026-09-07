# ============================================================
# SMARTSTOCK AI
# STEP 8.4 - CATEGORY SUMMARY
# ============================================================

import psycopg2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

DB = get_psycopg2_config()

print("=" * 70)
print("SMARTSTOCK AI - STEP 8.4")
print("Category Summary")
print("=" * 70)

conn = psycopg2.connect(**DB)
cur = conn.cursor()

# ------------------------------------------------------------
# Create category summary table
# ------------------------------------------------------------
cur.execute("""
DROP TABLE IF EXISTS ml.category_summary;

CREATE TABLE ml.category_summary AS

SELECT
    management_group_id,
    first_category_id,
    second_category_id,
    third_category_id,

    COUNT(*) AS products,

    ROUND(SUM(total_sales)::numeric,2) AS total_sales,
    ROUND(SUM(predicted_sales)::numeric,2) AS predicted_sales,

    SUM(high_risk_days) AS high_risk_days,
    SUM(urgent_reorders) AS urgent_reorders,

    ROUND(AVG(avg_reorder_qty)::numeric,2) AS avg_reorder_qty,

    ROUND(
        100.0 * SUM(high_risk_days) / NULLIF(SUM(observations),0),
        2
    ) AS high_risk_pct

FROM ml.product_recommendations

GROUP BY
    management_group_id,
    first_category_id,
    second_category_id,
    third_category_id;
""")

conn.commit()

print("PASS: Category summary created.")

# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------
cur.execute("""
SELECT COUNT(*)
FROM ml.category_summary;
""")

rows = cur.fetchone()[0]

print(f"\nTotal Category Groups : {rows}")

print("\nTop 10 Highest Risk Categories")
print("-" * 70)

cur.execute("""
SELECT
    management_group_id,
    first_category_id,
    second_category_id,
    third_category_id,
    products,
    total_sales,
    high_risk_pct,
    urgent_reorders

FROM ml.category_summary

ORDER BY urgent_reorders DESC,
         high_risk_pct DESC

LIMIT 10;
""")

for row in cur.fetchall():
    print(row)

cur.close()
conn.close()

print("\nPASS: STEP 8.4 COMPLETED")
