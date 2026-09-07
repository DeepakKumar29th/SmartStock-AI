from pathlib import Path
import os

import psycopg2
from dotenv import load_dotenv


# ============================================================
# SMARTSTOCK AI
# STEP 4.1 - POSTGRESQL DATA QUALITY BASELINE
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def section(title):
    print("\n" + "=" * 85)
    print(title)
    print("=" * 85)


# ============================================================
# CONNECTION
# ============================================================

section("SMARTSTOCK AI - STEP 4.1")

print("PostgreSQL Data Quality Baseline")

connection = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

cursor = connection.cursor()

print("PASS: PostgreSQL connection successful.")


# ============================================================
# 1. ROW COUNT
# ============================================================

section("1. ROW COUNT")

cursor.execute("""
    SELECT COUNT(*)
    FROM core.fact_daily_sales;
""")

total_rows = cursor.fetchone()[0]

print(f"Fact rows: {total_rows:,}")


# ============================================================
# 2. MISSING VALUES
# ============================================================

section("2. MISSING VALUES")

columns = [
    "store_id",
    "product_id",
    "dt",
    "sale_amount",
    "stock_hour6_22_cnt",
    "total_stockout_hours",
    "stockout_flag",
    "discount",
    "holiday_flag",
    "activity_flag",
    "precpt",
    "avg_temperature",
    "avg_humidity",
    "avg_wind_level"
]

missing_results = []

for column in columns:

    query = f"""
        SELECT COUNT(*)
        FROM core.fact_daily_sales
        WHERE "{column}" IS NULL;
    """

    cursor.execute(query)

    missing_count = cursor.fetchone()[0]

    missing_results.append(
        (column, missing_count)
    )

for column, count in missing_results:

    print(
        f"{column:25s}: {count:,}"
    )

total_missing = sum(
    count for _, count in missing_results
)

print()
print(
    f"TOTAL MISSING VALUES: {total_missing:,}"
)


# ============================================================
# 3. DUPLICATE BUSINESS KEYS
# ============================================================

section("3. DUPLICATE BUSINESS KEYS")

cursor.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT
            store_id,
            product_id,
            dt
        FROM core.fact_daily_sales
        GROUP BY
            store_id,
            product_id,
            dt
        HAVING COUNT(*) > 1
    ) duplicates;
""")

duplicate_groups = cursor.fetchone()[0]

print(
    f"Duplicate key groups: {duplicate_groups:,}"
)

if duplicate_groups == 0:
    print("PASS: No duplicate business keys.")
else:
    print("WARNING: Duplicate business keys found.")


# ============================================================
# 4. SALES VALIDATION
# ============================================================

section("4. SALES VALIDATION")

cursor.execute("""
    SELECT
        COUNT(*) FILTER (
            WHERE sale_amount < 0
        ),
        COUNT(*) FILTER (
            WHERE sale_amount = 0
        ),
        COUNT(*) FILTER (
            WHERE sale_amount > 0
        ),
        MIN(sale_amount),
        MAX(sale_amount)
    FROM core.fact_daily_sales;
""")

negative_sales, zero_sales, positive_sales, min_sales, max_sales = (
    cursor.fetchone()
)

print(f"Negative sales : {negative_sales:,}")
print(f"Zero sales     : {zero_sales:,}")
print(f"Positive sales : {positive_sales:,}")
print(f"Minimum sales  : {min_sales}")
print(f"Maximum sales  : {max_sales}")


# ============================================================
# 5. STOCKOUT HOURS VALIDATION
# ============================================================

section("5. STOCKOUT HOURS VALIDATION")

cursor.execute("""
    SELECT
        COUNT(*)
    FROM core.fact_daily_sales
    WHERE total_stockout_hours < 0
       OR total_stockout_hours > 24;
""")

invalid_stockout_hours = cursor.fetchone()[0]

print(
    f"Invalid stockout-hour rows: "
    f"{invalid_stockout_hours:,}"
)

if invalid_stockout_hours == 0:
    print("PASS: Stockout hours are within 0-24.")
else:
    print("WARNING: Invalid stockout hours found.")


# ============================================================
# 6. STOCKOUT FLAG CONSISTENCY
# ============================================================

section("6. STOCKOUT FLAG CONSISTENCY")

cursor.execute("""
    SELECT COUNT(*)
    FROM core.fact_daily_sales
    WHERE
        (
            total_stockout_hours > 0
            AND stockout_flag = FALSE
        )
        OR
        (
            total_stockout_hours = 0
            AND stockout_flag = TRUE
        );
""")

inconsistent_flags = cursor.fetchone()[0]

print(
    f"Inconsistent stockout flags: "
    f"{inconsistent_flags:,}"
)

if inconsistent_flags == 0:
    print("PASS: Stockout flags are consistent.")
else:
    print("WARNING: Inconsistent stockout flags found.")


# ============================================================
# 7. DISCOUNT VALIDATION
# ============================================================

section("7. DISCOUNT VALIDATION")

cursor.execute("""
    SELECT
        MIN(discount),
        MAX(discount),
        COUNT(*) FILTER (
            WHERE discount < 0
               OR discount > 1.1
        )
    FROM core.fact_daily_sales;
""")

min_discount, max_discount, invalid_discount = cursor.fetchone()

print(f"Minimum discount: {min_discount}")
print(f"Maximum discount: {max_discount}")
print(
    f"Invalid discount rows: "
    f"{invalid_discount:,}"
)

if invalid_discount == 0:
    print("PASS: Discount values are within expected range.")
else:
    print("WARNING: Unexpected discount values found.")


# ============================================================
# 8. FLAG VALIDATION
# ============================================================

section("8. FLAG VALIDATION")

cursor.execute("""
    SELECT
        COUNT(*) FILTER (
            WHERE holiday_flag NOT IN (0, 1)
        ),
        COUNT(*) FILTER (
            WHERE activity_flag NOT IN (0, 1)
        )
    FROM core.fact_daily_sales;
""")

invalid_holiday, invalid_activity = cursor.fetchone()

print(
    f"Invalid holiday_flag rows : "
    f"{invalid_holiday:,}"
)

print(
    f"Invalid activity_flag rows: "
    f"{invalid_activity:,}"
)


# ============================================================
# 9. WEATHER / CONTEXT VALIDATION
# ============================================================

section("9. WEATHER / CONTEXT VALIDATION")

cursor.execute("""
    SELECT
        MIN(precpt),
        MAX(precpt),
        MIN(avg_temperature),
        MAX(avg_temperature),
        MIN(avg_humidity),
        MAX(avg_humidity),
        MIN(avg_wind_level),
        MAX(avg_wind_level)
    FROM core.fact_daily_sales;
""")

(
    min_precpt,
    max_precpt,
    min_temp,
    max_temp,
    min_humidity,
    max_humidity,
    min_wind,
    max_wind
) = cursor.fetchone()

print(f"Precipitation : {min_precpt} → {max_precpt}")
print(f"Temperature   : {min_temp} → {max_temp}")
print(f"Humidity      : {min_humidity} → {max_humidity}")
print(f"Wind level    : {min_wind} → {max_wind}")


# ============================================================
# 10. DATE VALIDATION
# ============================================================

section("10. DATE VALIDATION")

cursor.execute("""
    SELECT
        MIN(dt),
        MAX(dt),
        COUNT(DISTINCT dt)
    FROM core.fact_daily_sales;
""")

min_date, max_date, unique_dates = cursor.fetchone()

print(f"Minimum date : {min_date}")
print(f"Maximum date : {max_date}")
print(f"Unique dates : {unique_dates}")


# ============================================================
# 11. FOREIGN KEY INTEGRITY
# ============================================================

section("11. FOREIGN KEY INTEGRITY")

cursor.execute("""
    SELECT COUNT(*)
    FROM core.fact_daily_sales f
    LEFT JOIN core.dim_store s
        ON f.store_id = s.store_id
    WHERE s.store_id IS NULL;
""")

orphan_stores = cursor.fetchone()[0]


cursor.execute("""
    SELECT COUNT(*)
    FROM core.fact_daily_sales f
    LEFT JOIN core.dim_product p
        ON f.product_id = p.product_id
    WHERE p.product_id IS NULL;
""")

orphan_products = cursor.fetchone()[0]

print(f"Orphan store rows   : {orphan_stores:,}")
print(f"Orphan product rows : {orphan_products:,}")


# ============================================================
# 12. ENTITY COUNTS
# ============================================================

section("12. BUSINESS ENTITY COUNTS")

cursor.execute("""
    SELECT
        COUNT(DISTINCT store_id),
        COUNT(DISTINCT product_id)
    FROM core.fact_daily_sales;
""")

stores, products = cursor.fetchone()

print(f"Stores   : {stores:,}")
print(f"Products : {products:,}")


# ============================================================
# FINAL STATUS
# ============================================================

section("STEP 4.1 SUMMARY")

print(f"Total fact rows       : {total_rows:,}")
print(f"Total missing values  : {total_missing:,}")
print(f"Duplicate key groups  : {duplicate_groups:,}")
print(f"Negative sales        : {negative_sales:,}")
print(f"Invalid stockout hrs  : {invalid_stockout_hours:,}")
print(f"Inconsistent flags    : {inconsistent_flags:,}")
print(f"Invalid discounts     : {invalid_discount:,}")
print(f"Invalid holiday flags : {invalid_holiday:,}")
print(f"Invalid activity flags: {invalid_activity:,}")
print(f"Orphan stores         : {orphan_stores:,}")
print(f"Orphan products       : {orphan_products:,}")

print()
print("STEP 4.1 BASELINE COMPLETE")
print("No data was modified.")

cursor.close()
connection.close()