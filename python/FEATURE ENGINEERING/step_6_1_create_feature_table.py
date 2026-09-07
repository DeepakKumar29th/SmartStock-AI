# ============================================================
# SMARTSTOCK AI
# STEP 6.1 - CREATE ML FEATURE TABLE
# ============================================================

import psycopg2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

# =========================
# PostgreSQL Connection
# =========================
DB_CONFIG = get_psycopg2_config()

print("=" * 70)
print("SMARTSTOCK AI - STEP 6.1")
print("Create ML Feature Table")
print("=" * 70)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

print("\nCreating ML schema...")

cur.execute("""
CREATE SCHEMA IF NOT EXISTS ml;
""")

print("PASS: Schema ready.")

# ============================================================
# Drop existing table
# ============================================================

cur.execute("""
DROP TABLE IF EXISTS ml.features_daily;
""")

# ============================================================
# Create feature table
# ============================================================

print("\nCreating feature table...")

cur.execute("""
CREATE TABLE ml.features_daily AS

SELECT
    store_id,
    product_id,
    dt,

    sale_amount,

    stock_hour6_22_cnt,
    total_stockout_hours,
    stockout_flag,

    discount,
    holiday_flag,
    activity_flag,

    precpt,
    avg_temperature,
    avg_humidity,
    avg_wind_level

FROM core.fact_daily_sales

ORDER BY
    store_id,
    product_id,
    dt;
""")

conn.commit()

print("PASS: Feature table created.")

# ============================================================
# Validation
# ============================================================

cur.execute("""
SELECT COUNT(*) FROM ml.features_daily;
""")
rows = cur.fetchone()[0]

cur.execute("""
SELECT COUNT(DISTINCT (store_id, product_id)) FROM ml.features_daily;
""")
pairs = cur.fetchone()[0]

cur.execute("""
SELECT MIN(dt), MAX(dt) FROM ml.features_daily;
""")
mindate, maxdate = cur.fetchone()

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

print(f"Rows                : {rows:,}")
print(f"Store-Product Pairs : {pairs:,}")
print(f"Date Range          : {mindate} → {maxdate}")

print("\nExpected:")
print("Rows                : 4,500,000")
print("Store-Product Pairs : 50,000")
print("Date Range          : 2024-03-28 → 2024-06-25")

if rows == 4500000 and pairs == 50000:
    print("\nPASS: STEP 6.1 completed successfully.")
else:
    print("\nFAIL: Validation mismatch.")

cur.close()
conn.close()

print("\nConnection closed.")
