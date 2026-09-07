# ============================================================
# SMARTSTOCK AI
# STEP 6.2 - CALENDAR FEATURE ENGINEERING
# ============================================================

import psycopg2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

# -----------------------------
# PostgreSQL Connection
# -----------------------------
DB_CONFIG = get_psycopg2_config()

print("=" * 70)
print("SMARTSTOCK AI - STEP 6.2")
print("Calendar Feature Engineering")
print("=" * 70)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# ============================================================
# Add Calendar Columns
# ============================================================

print("\nAdding calendar columns...")

cur.execute("""
ALTER TABLE ml.features_daily
ADD COLUMN IF NOT EXISTS day_of_week INTEGER,
ADD COLUMN IF NOT EXISTS week_of_year INTEGER,
ADD COLUMN IF NOT EXISTS month INTEGER,
ADD COLUMN IF NOT EXISTS is_weekend BOOLEAN;
""")

conn.commit()

print("PASS: Columns created.")

# ============================================================
# Populate Features
# ============================================================

print("\nPopulating calendar features...")

cur.execute("""
UPDATE ml.features_daily
SET
    day_of_week = EXTRACT(ISODOW FROM dt),
    week_of_year = EXTRACT(WEEK FROM dt),
    month = EXTRACT(MONTH FROM dt),
    is_weekend = CASE
                    WHEN EXTRACT(ISODOW FROM dt) IN (6,7)
                    THEN TRUE
                    ELSE FALSE
                 END;
""")

conn.commit()

print("PASS: Calendar features populated.")

# ============================================================
# Validation
# ============================================================

cur.execute("""
SELECT
    COUNT(*),
    MIN(day_of_week),
    MAX(day_of_week),
    MIN(week_of_year),
    MAX(week_of_year),
    MIN(month),
    MAX(month)
FROM ml.features_daily;
""")

result = cur.fetchone()

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

print(f"Rows          : {result[0]:,}")
print(f"Day of Week   : {result[1]} → {result[2]}")
print(f"Week of Year  : {result[3]} → {result[4]}")
print(f"Month         : {result[5]} → {result[6]}")

cur.execute("""
SELECT
    is_weekend,
    COUNT(*)
FROM ml.features_daily
GROUP BY is_weekend
ORDER BY is_weekend;
""")

print("\nWeekend Distribution")
for row in cur.fetchall():
    print(row)

print("\nPASS: STEP 6.2 completed successfully.")

cur.close()
conn.close()
print("Connection closed.")
