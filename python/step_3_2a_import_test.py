from pathlib import Path
from io import StringIO
import csv
import os

import pyarrow.parquet as pq
import psycopg2
from dotenv import load_dotenv


# ============================================================
# SMARTSTOCK AI
# STEP 3.2A - 1,000 ROW IMPORT TEST
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


DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

TEST_ROWS = 1000


def section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


# ============================================================
# 1. CONFIGURATION
# ============================================================

section("SMARTSTOCK AI - STEP 3.2A")
print("PostgreSQL Import Test")

print(f"Parquet file : {PARQUET_PATH}")
print(f"Test rows    : {TEST_ROWS}")
print(f"Database     : {DB_NAME}")
print(f"Port         : {DB_PORT}")


# ============================================================
# 2. CHECK FILE
# ============================================================

section("1. CHECK PARQUET FILE")

if not PARQUET_PATH.exists():
    print("ERROR: Parquet file not found.")
    raise SystemExit(1)

print("PASS: Parquet file exists.")


# ============================================================
# 3. READ 1,000 ROWS WITH PYARROW
# ============================================================

section("2. READ TEST BATCH")

table = pq.read_table(
    PARQUET_PATH
)

table = table.slice(
    0,
    TEST_ROWS
)

rows = table.to_pylist()

print(f"Rows read from Parquet: {len(rows):,}")

if len(rows) != TEST_ROWS:
    print("ERROR: Expected exactly 1,000 rows.")
    raise SystemExit(1)

print("PASS: Exactly 1,000 rows loaded.")


# ============================================================
# 4. CONNECT TO POSTGRESQL
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

    print("PASS: PostgreSQL connection successful.")

except Exception as error:

    print("ERROR: PostgreSQL connection failed.")
    print(error)
    raise SystemExit(1)


# ============================================================
# 5. CLEAR TEST TABLE
# ============================================================

section("4. PREPARE RAW TABLE")

cursor = connection.cursor()

print("Clearing raw.raw_retail_data...")

cursor.execute(
    "TRUNCATE TABLE raw.raw_retail_data;"
)

connection.commit()

print("PASS: Raw table is empty before test import.")


# ============================================================
# 6. CONVERT ROWS TO POSTGRESQL COPY FORMAT
# ============================================================

section("5. PREPARE COPY DATA")


def postgres_array(values):
    """
    Convert Python list to PostgreSQL array literal.

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

print("PASS: COPY data prepared.")


# ============================================================
# 7. BULK INSERT
# ============================================================

section("6. BULK INSERT")

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

try:

    cursor.copy_expert(
        copy_sql,
        buffer
    )

    connection.commit()

    print("PASS: COPY completed successfully.")

except Exception as error:

    connection.rollback()

    print("ERROR: COPY failed.")
    print(error)

    cursor.close()
    connection.close()

    raise SystemExit(1)


# ============================================================
# 8. ROW COUNT VERIFICATION
# ============================================================

section("7. ROW COUNT VERIFICATION")

cursor.execute(
    """
    SELECT COUNT(*)
    FROM raw.raw_retail_data;
    """
)

row_count = cursor.fetchone()[0]

print(f"Rows in PostgreSQL: {row_count:,}")

if row_count == TEST_ROWS:

    print(
        "PASS: PostgreSQL contains exactly 1,000 rows."
    )

else:

    print(
        "FAIL: PostgreSQL row count does not match."
    )

    cursor.close()
    connection.close()

    raise SystemExit(1)


# ============================================================
# 9. ARRAY LENGTH VERIFICATION
# ============================================================

section("8. ARRAY VERIFICATION")

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

total_rows, valid_sales, valid_status = cursor.fetchone()

print(f"Total rows              : {total_rows:,}")
print(f"24-value hours_sale     : {valid_sales:,}")
print(f"24-value stock_status   : {valid_status:,}")

if (
    total_rows == TEST_ROWS
    and valid_sales == TEST_ROWS
    and valid_status == TEST_ROWS
):

    print("PASS: All arrays contain exactly 24 values.")

else:

    print("FAIL: Array validation failed.")

    cursor.close()
    connection.close()

    raise SystemExit(1)


# ============================================================
# 10. STOCK STATUS VALUE CHECK
# ============================================================

section("9. STOCK STATUS VALUE VERIFICATION")

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
    f"Rows with invalid stock-status values: "
    f"{invalid_status_rows:,}"
)

if invalid_status_rows == 0:

    print("PASS: Stock status contains only 0 and 1.")

else:

    print("FAIL: Invalid stock-status values found.")


# ============================================================
# 11. SAMPLE DATABASE RECORD
# ============================================================

section("10. DATABASE SAMPLE")

cursor.execute(
    """
    SELECT
        city_id,
        store_id,
        product_id,
        dt,
        sale_amount,
        stock_hour6_22_cnt,
        cardinality(hours_sale) AS sales_hours,
        cardinality(hours_stock_status) AS stock_hours
    FROM raw.raw_retail_data
    ORDER BY dt, store_id, product_id
    LIMIT 3;
    """
)

sample_rows = cursor.fetchall()

for sample in sample_rows:
    print(sample)


# ============================================================
# 12. FINAL STATUS
# ============================================================

cursor.close()
connection.close()

section("STEP 3.2A STATUS")

if (
    row_count == TEST_ROWS
    and valid_sales == TEST_ROWS
    and valid_status == TEST_ROWS
    and invalid_status_rows == 0
):

    print("""
PASS

The 1,000-row Parquet → PostgreSQL import pipeline works.

The raw PostgreSQL table correctly preserves:
- Daily records
- Hourly sales arrays
- Hourly stock-status arrays
- Stockout count
- Context variables

The full import can now be performed using the validated pipeline.
""")

else:

    print("""
FAIL

The import test did not pass.
Do not perform the full dataset import yet.
""")