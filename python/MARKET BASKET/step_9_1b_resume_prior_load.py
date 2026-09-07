"""
SmartStock AI - Resume partial prior load (conflict-safe)
Uses row position offset so we never re-insert already-loaded rows.
"""
import sys, time
from pathlib import Path
import pandas as pd
from sqlalchemy import text

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT / "python"))
from db_config import get_engine

PRIOR_FILE = _ROOT / "instacart dataset" / "order_products__prior.csv"
CHUNK_SIZE = 200_000
engine = get_engine()

with engine.connect() as conn:
    current = conn.execute(text(
        "SELECT COUNT(*) FROM instacart.order_products_prior"
    )).scalar()

print(f"Currently in DB: {current:,} rows  (file has 32,434,489)")
skip_rows = current      # skip rows already loaded
if skip_rows >= 32_434_489:
    print("Already fully loaded — nothing to do.")
    sys.exit(0)

print(f"Skipping first {skip_rows:,} rows, loading the rest...")
DTYPES = {"order_id": int, "product_id": int, "add_to_cart_order": int, "reordered": int}

total_added = 0
t0 = time.time()
rows_skipped = 0

for chunk in pd.read_csv(PRIOR_FILE, dtype=DTYPES, chunksize=CHUNK_SIZE):
    if rows_skipped + len(chunk) <= skip_rows:
        rows_skipped += len(chunk)
        continue
    elif rows_skipped < skip_rows:
        # partial overlap — trim the already-loaded portion
        trim = skip_rows - rows_skipped
        chunk = chunk.iloc[trim:]
        rows_skipped = skip_rows

    # Use ON CONFLICT DO NOTHING via raw SQL for safety
    records = chunk.to_dict(orient="records")
    with engine.connect() as conn:
        for rec in records:
            conn.execute(text("""
                INSERT INTO instacart.order_products_prior
                    (order_id, product_id, add_to_cart_order, reordered)
                VALUES (:order_id, :product_id, :add_to_cart_order, :reordered)
                ON CONFLICT DO NOTHING
            """), rec)
        conn.commit()

    total_added += len(chunk)
    print(f"  Inserted {total_added:,} new rows ...", end="\r")

with engine.connect() as conn:
    final = conn.execute(text(
        "SELECT COUNT(*) FROM instacart.order_products_prior"
    )).scalar()

print(f"\nRows added this run  : {total_added:,}")
print(f"Final row count      : {final:,}  (expected 32,434,489)")
print(f"Coverage             : {final / 32_434_489 * 100:.1f}%")
print(f"Time                 : {time.time()-t0:.1f}s")

