# ============================================================
# SMARTSTOCK AI
# STEP 7.4 - STOCKOUT RISK PREDICTION
# ============================================================

import psycopg2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

DB = get_psycopg2_config()

print("=" * 70)
print("SMARTSTOCK AI - STEP 7.4")
print("Stockout Risk Prediction")
print("=" * 70)

conn = psycopg2.connect(**DB)
cur = conn.cursor()

# ------------------------------------------------------------
# Add stockout risk column
# ------------------------------------------------------------
print("\nAdding risk column...")

cur.execute("""
ALTER TABLE ml.test_dataset
ADD COLUMN IF NOT EXISTS stockout_risk VARCHAR(15);
""")

conn.commit()

print("PASS: Column ready.")

# ------------------------------------------------------------
# Rule-based stockout risk
# ------------------------------------------------------------
print("\nCalculating stockout risk...")

cur.execute("""
UPDATE ml.test_dataset

SET stockout_risk =

CASE

    WHEN rolling_7_stockout_days >= 5
         AND rolling_7_mean >= 1.5
    THEN 'HIGH'

    WHEN rolling_7_stockout_days >= 3
         OR rolling_7_mean >= 1.0
    THEN 'MEDIUM'

    ELSE 'LOW'

END;
""")

conn.commit()

print("PASS: Risk labels generated.")

# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------
cur.execute("""
SELECT
    stockout_risk,
    COUNT(*)
FROM ml.test_dataset
GROUP BY stockout_risk
ORDER BY stockout_risk;
""")

rows = cur.fetchall()

print("\n" + "=" * 70)
print("RISK DISTRIBUTION")
print("=" * 70)

total = 0

for risk, cnt in rows:
    total += cnt
    print(f"{risk:<8} {cnt:,}")

print("-" * 30)
print(f"TOTAL    {total:,}")

# ------------------------------------------------------------
# Sample
# ------------------------------------------------------------
cur.execute("""
SELECT
    store_id,
    product_id,
    dt,
    rolling_7_mean,
    rolling_7_stockout_days,
    stockout_risk

FROM ml.test_dataset

ORDER BY
    rolling_7_stockout_days DESC,
    rolling_7_mean DESC

LIMIT 10;
""")

print("\nTop Risk Examples")
print("-" * 70)

for r in cur.fetchall():
    print(r)

cur.close()
conn.close()

print("\nPASS: STEP 7.4 COMPLETED")
