# ============================================================
# SMARTSTOCK AI
# STEP 6.5 - STOCKOUT HISTORY FEATURES
# ============================================================

import psycopg2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

DB_CONFIG = get_psycopg2_config()

print("=" * 70)
print("SMARTSTOCK AI - STEP 6.5")
print("Stockout Feature Engineering")
print("=" * 70)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# ------------------------------------------------------------
# Add feature columns
# ------------------------------------------------------------
print("\nAdding stockout feature columns...")

cur.execute("""
ALTER TABLE ml.features_daily
ADD COLUMN IF NOT EXISTS lag_1_stockout BOOLEAN,
ADD COLUMN IF NOT EXISTS rolling_7_stockout_hours NUMERIC,
ADD COLUMN IF NOT EXISTS rolling_7_stockout_days INTEGER;
""")

conn.commit()
print("PASS: Columns created.")

# ------------------------------------------------------------
# Generate features
# ------------------------------------------------------------
print("\nGenerating stockout history features...")

cur.execute("""
WITH stock_features AS (

    SELECT
        store_id,
        product_id,
        dt,

        LAG(stockout_flag,1) OVER(
            PARTITION BY store_id, product_id
            ORDER BY dt
        ) AS lag_stockout,

        SUM(total_stockout_hours) OVER(
            PARTITION BY store_id, product_id
            ORDER BY dt
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS rolling_hours,

        SUM(
            CASE
                WHEN stockout_flag THEN 1
                ELSE 0
            END
        ) OVER(
            PARTITION BY store_id, product_id
            ORDER BY dt
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS rolling_days

    FROM ml.features_daily
)

UPDATE ml.features_daily f

SET
    lag_1_stockout = s.lag_stockout,
    rolling_7_stockout_hours = s.rolling_hours,
    rolling_7_stockout_days = s.rolling_days

FROM stock_features s

WHERE
    f.store_id = s.store_id
    AND f.product_id = s.product_id
    AND f.dt = s.dt;
""")

conn.commit()

print("PASS: Stockout features generated.")

# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------
cur.execute("""
SELECT
    COUNT(*),
    COUNT(lag_1_stockout),
    COUNT(rolling_7_stockout_hours),
    COUNT(rolling_7_stockout_days)
FROM ml.features_daily;
""")

r = cur.fetchone()

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

print(f"Rows                 : {r[0]:,}")
print(f"Lag Stockout         : {r[1]:,}")
print(f"Rolling Stock Hours  : {r[2]:,}")
print(f"Rolling Stock Days   : {r[3]:,}")

cur.execute("""
SELECT
    store_id,
    product_id,
    dt,
    stockout_flag,
    total_stockout_hours,
    lag_1_stockout,
    rolling_7_stockout_hours,
    rolling_7_stockout_days
FROM ml.features_daily
ORDER BY store_id, product_id, dt
LIMIT 10;
""")

print("\nSample Records")
for row in cur.fetchall():
    print(row)

print("\nPASS: STEP 6.5 completed successfully.")

cur.close()
conn.close()

print("Connection closed.")
