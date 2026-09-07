# ============================================================
# SMARTSTOCK AI
# STEP 7.1 - TRAIN / TEST SPLIT
# ============================================================

import psycopg2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

# ------------------------------------------------------------
# PostgreSQL Configuration
# ------------------------------------------------------------
DB_CONFIG = get_psycopg2_config()

print("=" * 70)
print("SMARTSTOCK AI - STEP 7.1")
print("Train / Test Split")
print("=" * 70)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# ------------------------------------------------------------
# Create ML schema
# ------------------------------------------------------------
print("\nCreating ML schema...")

cur.execute("""
CREATE SCHEMA IF NOT EXISTS ml;
""")

conn.commit()

print("PASS: ML schema ready.")

# ------------------------------------------------------------
# Remove previous tables
# ------------------------------------------------------------
print("\nRemoving previous train/test tables...")

cur.execute("""
DROP TABLE IF EXISTS ml.train_dataset;
DROP TABLE IF EXISTS ml.test_dataset;
""")

conn.commit()

print("PASS: Previous tables removed.")

# ------------------------------------------------------------
# Train Dataset
# Train = 28 Mar -> 18 Jun
# ------------------------------------------------------------
print("\nCreating training dataset...")

cur.execute("""
CREATE TABLE ml.train_dataset AS

SELECT *

FROM ml.features_daily

WHERE dt <= DATE '2024-06-18'
  AND target_next_day_sales IS NOT NULL;
""")

conn.commit()

print("PASS: Training table created.")

# ------------------------------------------------------------
# Test Dataset
# Test = 19 Jun -> 24 Jun
# ------------------------------------------------------------
print("\nCreating testing dataset...")

cur.execute("""
CREATE TABLE ml.test_dataset AS

SELECT *

FROM ml.features_daily

WHERE dt BETWEEN DATE '2024-06-19'
            AND DATE '2024-06-24'
  AND target_next_day_sales IS NOT NULL;
""")

conn.commit()

print("PASS: Testing table created.")

# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------
cur.execute("""
SELECT COUNT(*) FROM ml.train_dataset;
""")
train_rows = cur.fetchone()[0]

cur.execute("""
SELECT COUNT(*) FROM ml.test_dataset;
""")
test_rows = cur.fetchone()[0]

cur.execute("""
SELECT MIN(dt), MAX(dt) FROM ml.train_dataset;
""")
train_min, train_max = cur.fetchone()

cur.execute("""
SELECT MIN(dt), MAX(dt) FROM ml.test_dataset;
""")
test_min, test_max = cur.fetchone()

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

print(f"Train Rows : {train_rows:,}")
print(f"Test Rows  : {test_rows:,}")

print(f"\nTrain Period : {train_min} → {train_max}")
print(f"Test Period  : {test_min} → {test_max}")

total = train_rows + test_rows

print(f"\nTotal ML Rows : {total:,}")

train_pct = train_rows / total * 100
test_pct = test_rows / total * 100

print(f"Train % : {train_pct:.2f}%")
print(f"Test %  : {test_pct:.2f}%")

print("\nPASS: Time-based split completed successfully.")

cur.close()
conn.close()

print("Connection closed.")
