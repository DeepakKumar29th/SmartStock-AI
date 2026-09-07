# ============================================================
# SMARTSTOCK AI
# STEP 9.1 — INSTACART POSTGRESQL SCHEMA + INGESTION
# ============================================================
#
# This script:
#   1. Creates the 'instacart' schema in PostgreSQL
#   2. Loads all 6 Instacart CSV files into raw tables
#   3. Validates row counts, nulls, and referential integrity
#
# Run from the project root:
#   python python/MARKET BASKET/step_9_1_instacart_ingest.py
# ============================================================

import os
import sys
import time
from pathlib import Path

import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text

# ── project-root path resolution ───────────────────────────
_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT / "python"))

from db_config import get_engine, get_psycopg2_config

# ── locate Instacart data ────────────────────────────────────
INSTACART_DIR = Path(
    os.getenv("INSTACART_DATA_DIR", str(_ROOT / "instacart dataset"))
)

FILES = {
    "orders":                  "orders.csv",
    "products":                "products.csv",
    "aisles":                  "aisles.csv",
    "departments":             "departments.csv",
    "order_products_train":    "order_products__train.csv",
    "order_products_prior":    "order_products__prior.csv",
}


def section(title: str):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ── verify all files exist before starting ───────────────────
section("SMARTSTOCK AI — STEP 9.1")
print("Instacart PostgreSQL Ingestion")
print(f"Data directory: {INSTACART_DIR}")

missing = [f for f in FILES.values() if not (INSTACART_DIR / f).exists()]
if missing:
    print(f"\nERROR: Missing files: {missing}")
    sys.exit(1)

print("\nPASS: All 6 Instacart files found.")

# ── create schema ────────────────────────────────────────────
section("STEP 1: Create instacart schema")

cfg = get_psycopg2_config()
conn = psycopg2.connect(**cfg)
cur  = conn.cursor()

cur.execute("CREATE SCHEMA IF NOT EXISTS instacart;")
conn.commit()
print("PASS: instacart schema ready.")

# ── drop + recreate tables ───────────────────────────────────
section("STEP 2: Create tables")

cur.execute("""
DROP TABLE IF EXISTS instacart.order_products_prior CASCADE;
DROP TABLE IF EXISTS instacart.order_products_train CASCADE;
DROP TABLE IF EXISTS instacart.orders              CASCADE;
DROP TABLE IF EXISTS instacart.products            CASCADE;
DROP TABLE IF EXISTS instacart.aisles              CASCADE;
DROP TABLE IF EXISTS instacart.departments         CASCADE;
""")
conn.commit()

cur.execute("""
CREATE TABLE instacart.departments (
    department_id   INTEGER PRIMARY KEY,
    department      VARCHAR(100) NOT NULL
);

CREATE TABLE instacart.aisles (
    aisle_id        INTEGER PRIMARY KEY,
    aisle           VARCHAR(200) NOT NULL
);

CREATE TABLE instacart.products (
    product_id      INTEGER PRIMARY KEY,
    product_name    VARCHAR(500) NOT NULL,
    aisle_id        INTEGER NOT NULL
        REFERENCES instacart.aisles(aisle_id),
    department_id   INTEGER NOT NULL
        REFERENCES instacart.departments(department_id)
);

CREATE TABLE instacart.orders (
    order_id                INTEGER PRIMARY KEY,
    user_id                 INTEGER NOT NULL,
    eval_set                VARCHAR(10) NOT NULL,
    order_number            INTEGER NOT NULL,
    order_dow               SMALLINT NOT NULL,
    order_hour_of_day       SMALLINT NOT NULL,
    days_since_prior_order  NUMERIC(6,1)
);

CREATE TABLE instacart.order_products_train (
    order_id            INTEGER NOT NULL
        REFERENCES instacart.orders(order_id),
    product_id          INTEGER NOT NULL
        REFERENCES instacart.products(product_id),
    add_to_cart_order   SMALLINT NOT NULL,
    reordered           SMALLINT NOT NULL,
    PRIMARY KEY (order_id, product_id)
);

CREATE TABLE instacart.order_products_prior (
    order_id            INTEGER NOT NULL
        REFERENCES instacart.orders(order_id),
    product_id          INTEGER NOT NULL
        REFERENCES instacart.products(product_id),
    add_to_cart_order   SMALLINT NOT NULL,
    reordered           SMALLINT NOT NULL,
    PRIMARY KEY (order_id, product_id)
);
""")
conn.commit()
print("PASS: All 6 tables created.")
cur.close()
conn.close()

# ── load data via SQLAlchemy (chunked for large files) ────────
section("STEP 3: Load data into PostgreSQL")

engine = get_engine()

LOAD_ORDER = [
    # (table_name,                schema,       file_key,                chunk_size)
    ("departments",               "instacart",  "departments",            None),
    ("aisles",                    "instacart",  "aisles",                 None),
    ("products",                  "instacart",  "products",               None),
    ("orders",                    "instacart",  "orders",                 50_000),
    ("order_products_train",      "instacart",  "order_products_train",   100_000),
    ("order_products_prior",      "instacart",  "order_products_prior",   200_000),
]

DTYPE_OVERRIDES = {
    "orders": {
        "order_id":               int,
        "user_id":                int,
        "eval_set":               str,
        "order_number":           int,
        "order_dow":              int,
        "order_hour_of_day":      int,
        "days_since_prior_order": float,
    },
    "order_products_train": {
        "order_id":           int,
        "product_id":         int,
        "add_to_cart_order":  int,
        "reordered":          int,
    },
    "order_products_prior": {
        "order_id":           int,
        "product_id":         int,
        "add_to_cart_order":  int,
        "reordered":          int,
    },
}

for (table, schema, file_key, chunk_size) in LOAD_ORDER:
    fpath = INSTACART_DIR / FILES[file_key]
    print(f"\nLoading {schema}.{table} from {FILES[file_key]} ...")
    t0 = time.time()
    dtypes = DTYPE_OVERRIDES.get(file_key, None)

    if chunk_size is None:
        # Small file — load all at once
        df = pd.read_csv(fpath, dtype=dtypes)
        df.to_sql(table, engine, schema=schema, if_exists="append", index=False)
        print(f"  Rows loaded : {len(df):,}  ({time.time()-t0:.1f}s)")
    else:
        # Large file — chunked
        total = 0
        for chunk in pd.read_csv(fpath, dtype=dtypes, chunksize=chunk_size):
            chunk.to_sql(table, engine, schema=schema, if_exists="append", index=False)
            total += len(chunk)
            print(f"  ... {total:,} rows", end="\r")
        print(f"  Rows loaded : {total:,}  ({time.time()-t0:.1f}s)    ")

print("\nPASS: All files loaded.")

# ── add indexes for query performance ─────────────────────────
section("STEP 4: Create indexes")

with engine.connect() as conn:
    stmts = [
        "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON instacart.orders(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_orders_eval_set ON instacart.orders(eval_set);",
        "CREATE INDEX IF NOT EXISTS idx_opp_product_id  ON instacart.order_products_prior(product_id);",
        "CREATE INDEX IF NOT EXISTS idx_opp_order_id    ON instacart.order_products_prior(order_id);",
        "CREATE INDEX IF NOT EXISTS idx_opt_product_id  ON instacart.order_products_train(product_id);",
        "CREATE INDEX IF NOT EXISTS idx_products_aisle  ON instacart.products(aisle_id);",
        "CREATE INDEX IF NOT EXISTS idx_products_dept   ON instacart.products(department_id);",
    ]
    for s in stmts:
        conn.execute(text(s))
    conn.commit()
    print("PASS: Indexes created.")

# ── validation ────────────────────────────────────────────────
section("STEP 5: Validation")

EXPECTED = {
    "instacart.departments":          21,
    "instacart.aisles":               134,
    "instacart.products":             49_688,
    "instacart.orders":               3_421_083,
    "instacart.order_products_train": 1_384_617,
    "instacart.order_products_prior": 32_434_489,
}

all_pass = True

with engine.connect() as conn:
    for table_full, expected in EXPECTED.items():
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_full}"))
        actual = result.scalar()
        status = "PASS" if actual == expected else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  {status}  {table_full}: {actual:,} rows (expected {expected:,})")

    # Null check on days_since_prior_order (206,209 expected — first-order users)
    result = conn.execute(
        text("SELECT COUNT(*) FROM instacart.orders WHERE days_since_prior_order IS NULL")
    )
    null_days = result.scalar()
    print(f"\n  days_since_prior_order NULLs : {null_days:,}  (expected ~206,209 — first orders)")

    # Referential integrity check: all order_products reference existing products
    result = conn.execute(text("""
        SELECT COUNT(*) FROM instacart.order_products_prior opp
        LEFT JOIN instacart.products p ON opp.product_id = p.product_id
        WHERE p.product_id IS NULL
    """))
    orphan_products = result.scalar()
    print(f"  Orphan product references    : {orphan_products:,}  (expected 0)")

print()
if all_pass and orphan_products == 0:
    print("=" * 70)
    print("STEP 9.1 COMPLETED SUCCESSFULLY")
    print("All Instacart data is loaded and validated in PostgreSQL.")
    print("=" * 70)
else:
    print("WARNING: Some validation checks failed. Review output above.")
