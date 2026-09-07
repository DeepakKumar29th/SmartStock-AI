from pathlib import Path
from io import StringIO
import csv
import os
import time

import pyarrow.parquet as pq
import psycopg2
from dotenv import load_dotenv


# ============================================================
# SMARTSTOCK AI
# STEP 3.2B - FULL TRAIN DATA IMPORT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PARQUET_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "freshretail_train.parquet"
)

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


# ============================================================
# CONFIGURATION
# ============================================================

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

EXPECTED_ROWS = 4_500_000

# Number of Parquet rows processed at a time.
BATCH_SIZE = 50_000


def section(title):
    print("\n" + "=" * 85)
    print(title)
    print("=" * 85)


def postgres_array(values):
    """
    Convert a Python list to a PostgreSQL array literal.

    Example:
    [0.0, 0.1, 0.0]
    becomes:
    {0.0,0.1,0.0}
    """

    if values is None:
        return None

    return "{" + ",".join(
        str(value) for value in values
    ) + "}"


# ============================================================
# 1. START
# ============================================================

section("SMARTSTOCK AI - STEP 3.2B")

print("FULL TRAIN DATA IMPORT")
print()
print(f"Source      : {PARQUET_PATH}")
print(f"Expected    : {EXPECTED_ROWS:,} rows")
print(f"Batch size  : {BATCH_SIZE:,} rows")
print(f"Database    : {DB_NAME}")
print(f"Port        : {DB_PORT}")


# ============================================================
# 2. FILE CHECK
# ============================================================

section("1. PARQUET FILE CHECK")

if not PARQUET_PATH.exists():

    print("ERROR: Training Parquet file not found.")

    raise SystemExit(1)

print("PASS: Training Parquet file exists.")


# ============================================================
# 3. READ PARQUET METADATA
# ============================================================

section("2. PARQUET METADATA")

parquet_file = pq.ParquetFile(PARQUET_PATH)

parquet_rows = parquet_file.metadata.num_rows
row_groups = parquet_file.num_row_groups

print(f"Parquet rows     : {parquet_rows:,}")
print(f"Parquet rowgroups: {row_groups:,}")

if parquet_rows != EXPECTED_ROWS:

    print(
        f"WARNING: Expected {EXPECTED_ROWS:,} rows "
        f"but Parquet reports {parquet_rows:,}."
    )

else:

    print("PASS: Parquet row count matches expected count.")


# ============================================================
# 4. POSTGRESQL CONNECTION
# ============================================================

section("3. POSTGRESQL CONNECTION")

try:

    connection = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10,
    )

    connection.autocommit = False

    cursor = connection.cursor()

    print("PASS: PostgreSQL connection successful.")

except Exception as error:

    print("ERROR: PostgreSQL connection failed.")
    print(error)

    raise SystemExit(1)


# ============================================================
# 5. CLEAR PREVIOUS TEST DATA
# ============================================================

section("4. PREPARE RAW TABLE")

print(
    "Removing the previous 1,000-row import test..."
)

cursor.execute(
    "TRUNCATE TABLE raw.raw_retail_data;"
)

connection.commit()

print("PASS: raw.raw_retail_data is empty.")


# ============================================================
# 6. COPY SQL
# ============================================================

copy_sql = """
COPY raw.raw_retail_data (
    city_id,
    store_id,
    management_group_id,
    first_category_id,
    second_category_id,
    third_category_id,
    product_id,
    dt,
    sale_amount,
    hours_sale,
    stock_hour6_22_cnt,
    hours_stock_status,
    discount,
    holiday_flag,
    activity_flag,
    precpt,
    avg_temperature,
    avg_humidity,
    avg_wind_level
)
FROM STDIN
WITH (
    FORMAT CSV,
    NULL '\\N'
);
"""


# ============================================================
# 7. BATCH IMPORT
# ============================================================

section("5. FULL TRAIN IMPORT")

start_time = time.time()

rows_imported = 0
batch_number = 0

try:

    for batch in parquet_file.iter_batches(
        batch_size=BATCH_SIZE
    ):

        batch_number += 1

        rows = batch.to_pylist()

        buffer = StringIO()

        writer = csv.writer(
            buffer,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\n"
        )

        for row in rows:

            writer.writerow([
                row["city_id"],
                row["store_id"],
                row["management_group_id"],
                row["first_category_id"],
                row["second_category_id"],
                row["third_category_id"],
                row["product_id"],
                row["dt"],
                row["sale_amount"],

                postgres_array(
                    row["hours_sale"]
                ),

                row["stock_hour6_22_cnt"],

                postgres_array(
                    row["hours_stock_status"]
                ),

                row["discount"],
                row["holiday_flag"],
                row["activity_flag"],
                row["precpt"],
                row["avg_temperature"],
                row["avg_humidity"],
                row["avg_wind_level"],
            ])

        buffer.seek(0)

        cursor.copy_expert(
            copy_sql,
            buffer
        )

        connection.commit()

        rows_imported += len(rows)

        elapsed = time.time() - start_time

        rate = (
            rows_imported / elapsed
            if elapsed > 0
            else 0
        )

        percent = (
            rows_imported / EXPECTED_ROWS * 100
        )

        print(
            f"Batch {batch_number:03d} | "
            f"{rows_imported:>9,} / "
            f"{EXPECTED_ROWS:,} rows | "
            f"{percent:6.2f}% | "
            f"{rate:,.0f} rows/sec"
        )


except Exception as error:

    connection.rollback()

    print("\n" + "=" * 85)
    print("IMPORT FAILED")
    print("=" * 85)

    print(error)

    cursor.close()
    connection.close()

    raise SystemExit(1)


# ============================================================
# 8. IMPORT COMPLETION
# ============================================================

elapsed = time.time() - start_time

print("\nImport completed.")

print(
    f"Rows processed by Python : {rows_imported:,}"
)

print(
    f"Elapsed time             : {elapsed / 60:.2f} minutes"
)


# ============================================================
# 9. DATABASE ROW COUNT
# ============================================================

section("6. DATABASE ROW COUNT")

cursor.execute(
    """
    SELECT COUNT(*)
    FROM raw.raw_retail_data;
    """
)

database_rows = cursor.fetchone()[0]

print(
    f"Rows in PostgreSQL: {database_rows:,}"
)

if database_rows == EXPECTED_ROWS:

    print(
        "PASS: PostgreSQL contains exactly "
        "4,500,000 training rows."
    )

else:

    print(
        "FAIL: PostgreSQL row count does not match."
    )

    cursor.close()
    connection.close()

    raise SystemExit(1)


# ============================================================
# 10. DATE RANGE
# ============================================================

section("7. DATE RANGE VERIFICATION")

cursor.execute(
    """
    SELECT
        MIN(dt),
        MAX(dt),
        COUNT(DISTINCT dt)
    FROM raw.raw_retail_data;
    """
)

min_date, max_date, unique_dates = cursor.fetchone()

print(f"Minimum date : {min_date}")
print(f"Maximum date : {max_date}")
print(f"Unique dates : {unique_dates}")

if (
    str(min_date) == "2024-03-28"
    and str(max_date) == "2024-06-25"
    and unique_dates == 90
):

    print("PASS: Training date range is correct.")

else:

    print("WARNING: Training date range differs from expected.")


# ============================================================
# 11. BUSINESS ENTITY COUNTS
# ============================================================

section("8. BUSINESS ENTITY VERIFICATION")

cursor.execute(
    """
    SELECT
        COUNT(DISTINCT city_id),
        COUNT(DISTINCT store_id),
        COUNT(DISTINCT product_id)
    FROM raw.raw_retail_data;
    """
)

cities, stores, products = cursor.fetchone()

print(f"Cities   : {cities}")
print(f"Stores   : {stores}")
print(f"Products : {products}")

if (
    cities == 18
    and stores == 898
    and products == 865
):

    print(
        "PASS: Business entity counts match "
        "Step 1.1 verification."
    )

else:

    print(
        "WARNING: Business entity counts differ."
    )


# ============================================================
# 12. ARRAY VERIFICATION
# ============================================================

section("9. ARRAY VERIFICATION")

cursor.execute(
    """
    SELECT
        COUNT(*) AS total_rows,

        COUNT(*) FILTER (
            WHERE cardinality(hours_sale) = 24
        ) AS valid_hours_sale,

        COUNT(*) FILTER (
            WHERE cardinality(hours_stock_status) = 24
        ) AS valid_stock_status

    FROM raw.raw_retail_data;
    """
)

(
    total_rows,
    valid_hours_sale,
    valid_stock_status
) = cursor.fetchone()

print(
    f"Total rows            : {total_rows:,}"
)

print(
    f"24-value hours_sale   : {valid_hours_sale:,}"
)

print(
    f"24-value stock_status : {valid_stock_status:,}"
)

if (
    total_rows == EXPECTED_ROWS
    and valid_hours_sale == EXPECTED_ROWS
    and valid_stock_status == EXPECTED_ROWS
):

    print(
        "PASS: All training rows contain "
        "24-value hourly arrays."
    )

else:

    print(
        "FAIL: Array validation failed."
    )

    cursor.close()
    connection.close()

    raise SystemExit(1)


# ============================================================
# 13. STOCK STATUS VALIDATION
# ============================================================

section("10. STOCK STATUS VALUE VERIFICATION")

cursor.execute(
    """
    SELECT COUNT(*)
    FROM raw.raw_retail_data
    WHERE EXISTS (
        SELECT 1
        FROM unnest(hours_stock_status) AS value
        WHERE value NOT IN (0, 1)
    );
    """
)

invalid_status_rows = cursor.fetchone()[0]

print(
    f"Rows with invalid stock status values: "
    f"{invalid_status_rows:,}"
)

if invalid_status_rows == 0:

    print(
        "PASS: All stock-status values are 0 or 1."
    )

else:

    print(
        "FAIL: Invalid stock-status values found."
    )

    cursor.close()
    connection.close()

    raise SystemExit(1)


# ============================================================
# 14. FINAL DATABASE SAMPLE
# ============================================================

section("11. FINAL DATABASE SAMPLE")

cursor.execute(
    """
    SELECT
        city_id,
        store_id,
        product_id,
        dt,
        sale_amount,
        stock_hour6_22_cnt,
        cardinality(hours_sale),
        cardinality(hours_stock_status)
    FROM raw.raw_retail_data
    ORDER BY dt, store_id, product_id
    LIMIT 5;
    """
)

for row in cursor.fetchall():

    print(row)


# ============================================================
# 15. CLOSE CONNECTION
# ============================================================

cursor.close()
connection.close()


# ============================================================
# FINAL STATUS
# ============================================================

section("STEP 3.2B STATUS")

if (
    database_rows == EXPECTED_ROWS
    and unique_dates == 90
    and cities == 18
    and stores == 898
    and products == 865
    and valid_hours_sale == EXPECTED_ROWS
    and valid_stock_status == EXPECTED_ROWS
    and invalid_status_rows == 0
):

    print("""
PASS

FULL TRAIN DATA IMPORT SUCCESSFUL.

4,500,000 training records are now stored
in:

raw.raw_retail_data

The raw Parquet source was not modified.
""")

else:

    print("""
WARNING

The import completed, but one or more
verification checks did not match expectations.

DO NOT proceed until the result is reviewed.
""")