# ============================================================
# SMARTSTOCK AI
# STEP 6.4 - ROLLING FEATURE ENGINEERING
# ============================================================

import psycopg2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

DB_CONFIG = get_psycopg2_config()

print("=" * 70)
print("SMARTSTOCK AI - STEP 6.4")
print("Rolling Feature Engineering")
print("=" * 70)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# ------------------------------------------------------------
# Add rolling columns
# ------------------------------------------------------------
print("\nAdding rolling columns...")

cur.execute("""
ALTER TABLE ml.features_daily
ADD COLUMN IF NOT EXISTS rolling_3_mean NUMERIC,
ADD COLUMN IF NOT EXISTS rolling_7_mean NUMERIC,
ADD COLUMN IF NOT EXISTS rolling_7_std NUMERIC;
""")

conn.commit()
print("PASS: Columns created.")

# ------------------------------------------------------------
# Generate rolling features
# ------------------------------------------------------------
print("\nGenerating rolling statistics...")

cur.execute("""
WITH rolling_values AS (

    SELECT
        store_id,
        product_id,
        dt,

        AVG(sale_amount) OVER(
            PARTITION BY store_id, product_id
            ORDER BY dt
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS r3,

        AVG(sale_amount) OVER(
            PARTITION BY store_id, product_id
            ORDER BY dt
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS r7,

        STDDEV_POP(sale_amount) OVER(
            PARTITION BY store_id, product_id
            ORDER BY dt
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS s7

    FROM ml.features_daily
)

UPDATE ml.features_daily f

SET
    rolling_3_mean = r.r3,
    rolling_7_mean = r.r7,
    rolling_7_std  = r.s7

FROM rolling_values r

WHERE
    f.store_id = r.store_id
    AND f.product_id = r.product_id
    AND f.dt = r.dt;
""")

conn.commit()
print("PASS: Rolling features generated.")

# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------
cur.execute("""
SELECT
    COUNT(*),
    COUNT(rolling_3_mean),
    COUNT(rolling_7_mean),
    COUNT(rolling_7_std)
FROM ml.features_daily;
""")

rows = cur.fetchone()

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

print(f"Rows              : {rows[0]:,}")
print(f"Rolling3 populated: {rows[1]:,}")
print(f"Rolling7 populated: {rows[2]:,}")
print(f"Rolling7 STD      : {rows[3]:,}")

cur.execute("""
SELECT
    store_id,
    product_id,
    dt,
    sale_amount,
    rolling_3_mean,
    rolling_7_mean,
    rolling_7_std
FROM ml.features_daily
ORDER BY store_id, product_id, dt
LIMIT 10;
""")

print("\nSample Records")
for row in cur.fetchall():
    print(row)

print("\nPASS: STEP 6.4 completed successfully.")

cur.close()
conn.close()
print("Connection closed.")
