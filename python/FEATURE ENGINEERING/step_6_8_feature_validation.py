# ============================================================
# SMARTSTOCK AI
# STEP 6.8 - FINAL FEATURE VALIDATION & EXPORT
# ============================================================

import os
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db_config import get_psycopg2_config

# ------------------------------------------------------------
# PostgreSQL
# ------------------------------------------------------------
DB_CONFIG = get_psycopg2_config()

OUTPUT_FILE = r"data\processed\ml_features.parquet"

print("=" * 70)
print("SMARTSTOCK AI - STEP 6.8")
print("Final Feature Validation & Export")
print("=" * 70)

# ------------------------------------------------------------
# Connections
# ------------------------------------------------------------
conn = psycopg2.connect(**DB_CONFIG)

engine = create_engine(
    f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
)

cur = conn.cursor()

# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------
print("\nRunning validation...")

cur.execute("""
SELECT
    COUNT(*) AS rows,
    COUNT(DISTINCT (store_id, product_id)) AS pairs,
    COUNT(lag_1_sales),
    COUNT(rolling_7_mean),
    COUNT(target_next_day_sales)
FROM ml.features_daily;
""")

rows, pairs, lag1, rolling7, target = cur.fetchone()

print("\n" + "=" * 70)
print("FEATURE VALIDATION")
print("=" * 70)

print(f"Rows                  : {rows:,}")
print(f"Store-Product Pairs   : {pairs:,}")
print(f"Lag1 Values           : {lag1:,}")
print(f"Rolling7 Values       : {rolling7:,}")
print(f"Target Values         : {target:,}")

# ------------------------------------------------------------
# Export in chunks (Memory Safe)
# ------------------------------------------------------------
print("\nExporting Parquet...")

import pyarrow as pa
import pyarrow.parquet as pq

os.makedirs("data/processed", exist_ok=True)

query = """
SELECT *
FROM ml.features_daily
ORDER BY store_id, product_id, dt;
"""

chunksize = 100000
writer = None
total_rows = 0

for chunk in pd.read_sql(query, engine, chunksize=chunksize):
    table = pa.Table.from_pandas(chunk)

    if writer is None:
        writer = pq.ParquetWriter(
            OUTPUT_FILE,
            table.schema,
            compression="snappy"
        )

    writer.write_table(table)
    total_rows += len(chunk)
    print(f"Exported: {total_rows:,} rows")

if writer:
    writer.close()

print("\nPASS: Parquet exported.")
print(f"File: {OUTPUT_FILE}")
print(f"Rows: {total_rows:,}")
