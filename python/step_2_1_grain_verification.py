from pathlib import Path
import pandas as pd


# ============================================================
# SMARTSTOCK AI
# STEP 2.1 - DATA GRAIN & RELATIONSHIP VERIFICATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TRAIN_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "freshretail_train.parquet"
)


def section(title):
    print("\n" + "=" * 85)
    print(title)
    print("=" * 85)


# ============================================================
# 1. LOAD REQUIRED COLUMNS ONLY
# ============================================================

section("SMARTSTOCK AI - STEP 2.1")

print("Loading required columns...")

columns = [
    "city_id",
    "store_id",
    "management_group_id",
    "first_category_id",
    "second_category_id",
    "third_category_id",
    "product_id",
    "dt"
]

df = pd.read_parquet(
    TRAIN_PATH,
    columns=columns
)

print(f"Rows loaded: {len(df):,}")


# ============================================================
# 2. EXPECTED GRAIN
# ============================================================

section("1. EXPECTED DATA GRAIN")

print("""
Expected grain:

ONE ROW
=
ONE STORE
+
ONE PRODUCT
+
ONE DATE

Candidate business key:

(store_id, product_id, dt)
""")


# ============================================================
# 3. COMPOSITE KEY DUPLICATES
# ============================================================

section("2. STORE + PRODUCT + DATE UNIQUENESS")

key_columns = [
    "store_id",
    "product_id",
    "dt"
]

duplicate_key_count = (
    df.duplicated(
        subset=key_columns,
        keep=False
    ).sum()
)

duplicate_key_groups = (
    df.groupby(key_columns, sort=False)
      .size()
)

duplicate_key_groups = duplicate_key_groups[
    duplicate_key_groups > 1
]

print(
    f"Rows involved in duplicate keys: "
    f"{duplicate_key_count:,}"
)

print(
    f"Duplicate key groups: "
    f"{len(duplicate_key_groups):,}"
)

if len(duplicate_key_groups) == 0:

    print(
        "\nPASS: store_id + product_id + dt "
        "uniquely identifies each row."
    )

else:

    print(
        "\nWARNING: Candidate key is NOT unique."
    )

    print("\nFirst duplicate groups:")

    print(
        duplicate_key_groups
        .head(10)
        .to_string()
    )


# ============================================================
# 4. STORE → CITY RELATIONSHIP
# ============================================================

section("3. STORE → CITY RELATIONSHIP")

store_city_counts = (
    df.groupby("store_id")["city_id"]
      .nunique()
)

multi_city_stores = store_city_counts[
    store_city_counts > 1
]

print(
    f"Total stores: "
    f"{df['store_id'].nunique():,}"
)

print(
    f"Stores belonging to multiple cities: "
    f"{len(multi_city_stores):,}"
)

if len(multi_city_stores) == 0:

    print(
        "\nPASS: Every store maps to exactly one city."
    )

else:

    print(
        "\nWARNING: Some stores map to multiple cities."
    )

    print(
        multi_city_stores
        .head(10)
        .to_string()
    )


# ============================================================
# 5. PRODUCT → HIERARCHY RELATIONSHIP
# ============================================================

section("4. PRODUCT → CATEGORY HIERARCHY")

product_hierarchy_columns = [
    "management_group_id",
    "first_category_id",
    "second_category_id",
    "third_category_id"
]

product_hierarchy_counts = (
    df.groupby("product_id")[
        product_hierarchy_columns
    ]
    .nunique()
)

hierarchy_problems = (
    product_hierarchy_counts > 1
).any(axis=1)

problem_products = product_hierarchy_counts[
    hierarchy_problems
]

print(
    f"Total products: "
    f"{df['product_id'].nunique():,}"
)

print(
    f"Products with inconsistent category hierarchy: "
    f"{len(problem_products):,}"
)

if len(problem_products) == 0:

    print(
        "\nPASS: Every product has a consistent "
        "category hierarchy."
    )

else:

    print(
        "\nWARNING: Some products have inconsistent "
        "category hierarchy."
    )

    print(
        problem_products
        .head(10)
        .to_string()
    )


# ============================================================
# 6. STORE-PRODUCT COVERAGE
# ============================================================

section("5. STORE-PRODUCT COVERAGE")

store_product_pairs = (
    df[
        ["store_id", "product_id"]
    ]
    .drop_duplicates()
)

print(
    f"Unique store-product combinations: "
    f"{len(store_product_pairs):,}"
)

print(
    f"Average dates per store-product combination: "
    f"{len(df) / len(store_product_pairs):.2f}"
)


# ============================================================
# 7. ROWS PER STORE-PRODUCT
# ============================================================

section("6. DATES PER STORE-PRODUCT")

dates_per_pair = (
    df.groupby(
        ["store_id", "product_id"]
    )["dt"]
    .nunique()
)

print(
    dates_per_pair.describe()
    .to_string()
)

print(
    f"\nMinimum dates for a store-product pair: "
    f"{dates_per_pair.min()}"
)

print(
    f"Maximum dates for a store-product pair: "
    f"{dates_per_pair.max()}"
)


# ============================================================
# 8. DATE ORDER CHECK
# ============================================================

section("7. DATE ORDER CHECK")

min_date = pd.to_datetime(df["dt"]).min()
max_date = pd.to_datetime(df["dt"]).max()

print(f"Minimum training date: {min_date}")
print(f"Maximum training date: {max_date}")


# ============================================================
# 9. FINAL DATABASE DESIGN DECISION
# ============================================================

section("8. DATABASE DESIGN DECISION")

if (
    duplicate_key_count == 0
    and len(multi_city_stores) == 0
    and len(problem_products) == 0
):

    print("""
PASS

The dataset supports the following core design:

DIM_STORE
    store_id → city_id

DIM_PRODUCT
    product_id → product hierarchy

FACT_DAILY_SALES
    store_id + product_id + dt
    = unique daily observation
""")

else:

    print("""
WARNING

One or more relationship assumptions failed.

DO NOT create the final database schema yet.
We need to investigate the failed relationship first.
""")


# ============================================================
# 10. FINAL STATUS
# ============================================================

section("STEP 2.1 COMPLETE")

print("""
Data grain and relationship verification completed.

DO NOT:
- Create PostgreSQL tables
- Import data
- Add primary keys
- Create foreign keys

Send the complete terminal output for verification.
""")