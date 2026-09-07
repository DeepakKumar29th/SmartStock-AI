# ============================================================
# SMARTSTOCK AI
# STEP 6.3 - LAG FEATURE ENGINEERING
# ============================================================

import psycopg2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

DB_CONFIG = get_psycopg2_config()

print("=" * 70)
print("SMARTSTOCK AI - STEP 6.3")
print("Lag Feature Engineering")
print("=" * 70)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# ------------------------------------------------------------
# Add lag columns
# ------------------------------------------------------------

print("\nAdding lag columns...")

cur.execute("""
ALTER TABLE ml.features_daily
ADD COLUMN IF NOT EXISTS lag_1_sales NUMERIC,
ADD COLUMN IF NOT EXISTS lag_3_sales NUMERIC,
ADD COLUMN IF NOT EXISTS lag_7_sales NUMERIC;
""")

conn.commit()
print("PASS: Columns created.")

# ------------------------------------------------------------
# Populate lag features
# ------------------------------------------------------------

print("\nGenerating lag features...")

cur.execute("""
WITH lag_values AS (
    SELECT
        store_id,
        product_id,
        dt,

        LAG(sale_amount,1) OVER(
            PARTITION BY store_id, product_id
            ORDER BY dt
        ) AS l1,

        LAG(sale_amount,3) OVER(
            PARTITION BY store_id, product_id
            ORDER BY dt
        ) AS l3,

        LAG(sale_amount,7) OVER(
            PARTITION BY store_id, product_id
            ORDER BY dt
        ) AS l7

    FROM ml.features_daily
)

UPDATE ml.features_daily f

SET
    lag_1_sales = l.l1,
    lag_3_sales = l.l3,
    lag_7_sales = l.l7

FROM lag_values l

WHERE
    f.store_id = l.store_id
    AND f.product_id = l.product_id
    AND f.dt = l.dt;
""")

conn.commit()

print("PASS: Lag values generated.")

# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

cur.execute("""
SELECT
    COUNT(*) AS rows,

    COUNT(lag_1_sales),
    COUNT(lag_3_sales),
    COUNT(lag_7_sales)

FROM ml.features_daily;
""")

rows = cur.fetchone()

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

print(f"Rows           : {rows[0]:,}")
print(f"Lag1 populated : {rows[1]:,}")
print(f"Lag3 populated : {rows[2]:,}")
print(f"Lag7 populated : {rows[3]:,}")

cur.execute("""
SELECT
    store_id,
    product_id,
    dt,
    sale_amount,
    lag_1_sales,
    lag_3_sales,
    lag_7_sales
FROM ml.features_daily
ORDER BY store_id, product_id, dt
LIMIT 10;
""")

print("\nSample Records")
for r in cur.fetchall():
    print(r)

print("\nPASS: STEP 6.3 completed successfully.")

cur.close()
conn.close()
print("Connection closed.")
