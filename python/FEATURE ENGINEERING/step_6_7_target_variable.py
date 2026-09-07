# ============================================================
# SMARTSTOCK AI
# STEP 6.7 - TARGET VARIABLE (NEXT DAY DEMAND)
# ============================================================

import psycopg2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

DB_CONFIG = get_psycopg2_config()

print("=" * 70)
print("SMARTSTOCK AI - STEP 6.7")
print("Target Variable Engineering")
print("=" * 70)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# ------------------------------------------------------------
# Add target column
# ------------------------------------------------------------

print("\nAdding target column...")

cur.execute("""
ALTER TABLE ml.features_daily
ADD COLUMN IF NOT EXISTS target_next_day_sales NUMERIC;
""")

conn.commit()

print("PASS: Target column created.")

# ------------------------------------------------------------
# Generate target variable
# ------------------------------------------------------------

print("\nGenerating next-day demand target...")

cur.execute("""
WITH target_values AS (

    SELECT
        store_id,
        product_id,
        dt,

        LEAD(sale_amount,1) OVER(
            PARTITION BY store_id, product_id
            ORDER BY dt
        ) AS next_day_sales

    FROM ml.features_daily
)

UPDATE ml.features_daily f

SET
    target_next_day_sales = t.next_day_sales

FROM target_values t

WHERE
    f.store_id = t.store_id
    AND f.product_id = t.product_id
    AND f.dt = t.dt;
""")

conn.commit()

print("PASS: Target values generated.")

# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

cur.execute("""
SELECT
    COUNT(*) AS rows,
    COUNT(target_next_day_sales) AS populated_targets
FROM ml.features_daily;
""")

rows, targets = cur.fetchone()

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

print(f"Rows               : {rows:,}")
print(f"Target Populated   : {targets:,}")

cur.execute("""
SELECT
    store_id,
    product_id,
    dt,
    sale_amount,
    target_next_day_sales
FROM ml.features_daily
ORDER BY store_id, product_id, dt
LIMIT 10;
""")

print("\nSample Records")
for row in cur.fetchall():
    print(row)

print("\nPASS: STEP 6.7 completed successfully.")

cur.close()
conn.close()

print("Connection closed.")
