# ============================================================
# SMARTSTOCK AI
# STEP 6.6 - WEATHER FEATURE ENGINEERING
# ============================================================

import psycopg2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

DB_CONFIG = get_psycopg2_config()

print("=" * 70)
print("SMARTSTOCK AI - STEP 6.6")
print("Weather Feature Engineering")
print("=" * 70)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# ------------------------------------------------------------
# Add weather feature columns
# ------------------------------------------------------------

print("\nAdding weather feature columns...")

cur.execute("""
ALTER TABLE ml.features_daily
ADD COLUMN IF NOT EXISTS rain_category VARCHAR(20),
ADD COLUMN IF NOT EXISTS temperature_category VARCHAR(20),
ADD COLUMN IF NOT EXISTS humidity_level VARCHAR(20);
""")

conn.commit()

print("PASS: Columns created.")

# ------------------------------------------------------------
# Generate weather categories
# ------------------------------------------------------------

print("\nGenerating weather categories...")

cur.execute("""
UPDATE ml.features_daily

SET

rain_category = CASE
    WHEN precpt = 0 THEN 'No Rain'
    WHEN precpt <= 2 THEN 'Light Rain'
    WHEN precpt <= 5 THEN 'Moderate Rain'
    ELSE 'Heavy Rain'
END,

temperature_category = CASE
    WHEN avg_temperature < 18 THEN 'Cool'
    WHEN avg_temperature < 23 THEN 'Moderate'
    WHEN avg_temperature < 27 THEN 'Warm'
    ELSE 'Hot'
END,

humidity_level = CASE
    WHEN avg_humidity < 50 THEN 'Low'
    WHEN avg_humidity < 70 THEN 'Medium'
    ELSE 'High'
END;
""")

conn.commit()

print("PASS: Weather categories generated.")

# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

for title, column in [
    ("Rain Categories", "rain_category"),
    ("Temperature Categories", "temperature_category"),
    ("Humidity Levels", "humidity_level")
]:
    print(f"\n{title}")

    cur.execute(f"""
        SELECT {column}, COUNT(*)
        FROM ml.features_daily
        GROUP BY {column}
        ORDER BY {column};
    """)

    for row in cur.fetchall():
        print(row)

print("\nPASS: STEP 6.6 completed successfully.")

cur.close()
conn.close()

print("Connection closed.")
