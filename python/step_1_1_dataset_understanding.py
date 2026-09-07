from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# SMARTSTOCK AI
# STEP 1.1 - DATASET UNDERSTANDING
# FreshRetailNet-50K
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TRAIN_PATH = PROJECT_ROOT / "data" / "raw" / "freshretail_train.parquet"
EVAL_PATH = PROJECT_ROOT / "data" / "raw" / "freshretail_eval.parquet"

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 180)
pd.set_option("display.max_colwidth", 40)


def section(title):
    print("\n" + "=" * 85)
    print(title)
    print("=" * 85)


# ============================================================
# 1. LOAD DATA
# ============================================================

section("SMARTSTOCK AI - STEP 1.1")
print("FreshRetailNet-50K Dataset Understanding")

print("\nLoading datasets...")

train = pd.read_parquet(TRAIN_PATH)
eval_df = pd.read_parquet(EVAL_PATH)

print("Train loaded successfully.")
print("Eval loaded successfully.")


# ============================================================
# 2. DATASET SIZE
# ============================================================

section("1. DATASET SIZE")

print(f"TRAIN")
print(f"Rows    : {len(train):,}")
print(f"Columns : {len(train.columns)}")

print(f"\nEVAL")
print(f"Rows    : {len(eval_df):,}")
print(f"Columns : {len(eval_df.columns)}")


# ============================================================
# 3. COLUMN INFORMATION
# ============================================================

section("2. COLUMN INFORMATION")

column_info = pd.DataFrame({
    "column": train.columns,
    "dtype": train.dtypes.astype(str).values
})

print(column_info.to_string(index=False))


# ============================================================
# 4. TRAIN / EVAL SCHEMA
# ============================================================

section("3. TRAIN VS EVAL SCHEMA")

if list(train.columns) == list(eval_df.columns):
    print("PASS: Train and Eval columns match exactly.")
else:
    print("WARNING: Train and Eval columns do NOT match.")

    print("\nTrain-only columns:")
    print(set(train.columns) - set(eval_df.columns))

    print("\nEval-only columns:")
    print(set(eval_df.columns) - set(train.columns))


# ============================================================
# 5. MISSING VALUES
# ============================================================

section("4. MISSING VALUES")

train_missing = train.isna().sum()
eval_missing = eval_df.isna().sum()

missing = pd.DataFrame({
    "column": train.columns,
    "train_missing": train_missing.values,
    "eval_missing": eval_missing.values
})

print(missing.to_string(index=False))

print("\nTOTAL MISSING VALUES")
print(f"Train: {train_missing.sum():,}")
print(f"Eval : {eval_missing.sum():,}")


# ============================================================
# 6. SAFE DUPLICATE CHECK
# ============================================================

section("5. DUPLICATE CHECK")


def make_hashable(value):
    """
    Convert list/array-like values into tuples so that
    duplicate detection can safely handle them.
    """

    if isinstance(value, np.ndarray):
        return tuple(value.tolist())

    if isinstance(value, list):
        return tuple(value)

    if isinstance(value, tuple):
        return value

    return value


def safe_duplicate_count(df):
    temp = df.copy()

    for column in temp.columns:
        temp[column] = temp[column].map(make_hashable)

    return temp.duplicated().sum()


print("Checking exact duplicate rows in TRAIN...")
train_duplicates = safe_duplicate_count(train)

print("Checking exact duplicate rows in EVAL...")
eval_duplicates = safe_duplicate_count(eval_df)

print(f"\nTrain duplicate rows: {train_duplicates:,}")
print(f"Eval duplicate rows : {eval_duplicates:,}")


# ============================================================
# 7. UNIQUE BUSINESS ENTITIES
# ============================================================

section("6. UNIQUE BUSINESS ENTITIES")

entity_columns = [
    "city_id",
    "store_id",
    "management_group_id",
    "first_category_id",
    "second_category_id",
    "third_category_id",
    "product_id"
]

for column in entity_columns:

    if column in train.columns:

        print(
            f"{column:<25}: "
            f"{train[column].nunique():,} unique values"
        )


# ============================================================
# 8. DATE ANALYSIS
# ============================================================

section("7. DATE ANALYSIS")

train_dates = pd.to_datetime(train["dt"], errors="coerce")
eval_dates = pd.to_datetime(eval_df["dt"], errors="coerce")

print("TRAIN")
print(f"Minimum date       : {train_dates.min()}")
print(f"Maximum date       : {train_dates.max()}")
print(f"Unique dates       : {train_dates.nunique():,}")
print(f"Invalid dates      : {train_dates.isna().sum():,}")

print("\nEVAL")
print(f"Minimum date       : {eval_dates.min()}")
print(f"Maximum date       : {eval_dates.max()}")
print(f"Unique dates       : {eval_dates.nunique():,}")
print(f"Invalid dates      : {eval_dates.isna().sum():,}")


# ============================================================
# 9. DATE CONTINUITY
# ============================================================

section("8. DATE CONTINUITY")

unique_train_dates = (
    pd.Series(train_dates.dropna().unique())
    .sort_values()
)

unique_eval_dates = (
    pd.Series(eval_dates.dropna().unique())
    .sort_values()
)

if len(unique_train_dates) > 1:

    train_gaps = (
        unique_train_dates
        .diff()
        .dropna()
    )

    largest_train_gap = train_gaps.max()

    print(
        f"Largest gap between TRAIN dates: "
        f"{largest_train_gap}"
    )

if len(unique_eval_dates) > 1:

    eval_gaps = (
        unique_eval_dates
        .diff()
        .dropna()
    )

    largest_eval_gap = eval_gaps.max()

    print(
        f"Largest gap between EVAL dates: "
        f"{largest_eval_gap}"
    )


# ============================================================
# 10. SALES ANALYSIS
# ============================================================

section("9. SALES ANALYSIS")

sales = train["sale_amount"]

print("TRAIN sale_amount statistics:")
print(sales.describe().to_string())

zero_sales = (sales == 0).sum()
negative_sales = (sales < 0).sum()
positive_sales = (sales > 0).sum()

print("\nSales classification:")
print(f"Zero sales     : {zero_sales:,}")
print(f"Positive sales : {positive_sales:,}")
print(f"Negative sales : {negative_sales:,}")

print(
    f"\nZero-sales percentage: "
    f"{zero_sales / len(train) * 100:.2f}%"
)


# ============================================================
# 11. STOCK COLUMN STRUCTURE
# ============================================================

section("10. STOCK COLUMN STRUCTURE")

for column in ["hours_sale", "hours_stock_status"]:

    print(f"\nCOLUMN: {column}")
    print(f"Dtype: {train[column].dtype}")

    values = train[column].head(3).tolist()

    for i, value in enumerate(values, start=1):

        print(f"\nSample {i}:")
        print(value)

        if isinstance(value, (list, tuple, np.ndarray)):
            print(f"Length: {len(value)}")


# ============================================================
# 12. STOCK STATUS VALUES
# ============================================================

section("11. STOCK STATUS VALUE INSPECTION")

stock_status = train["hours_stock_status"]

sample_status = stock_status.head(1000)

status_values = set()

for value in sample_status:

    if isinstance(value, (list, tuple, np.ndarray)):

        status_values.update(
            np.asarray(value).flatten().tolist()
        )

print(
    "Unique stock-status values found "
    "in first 1,000 rows:"
)

print(sorted(status_values))


# ============================================================
# 13. WEATHER / CONTEXT VARIABLES
# ============================================================

section("12. CONTEXT VARIABLES")

context_columns = [
    "discount",
    "holiday_flag",
    "activity_flag",
    "precpt",
    "avg_temperature",
    "avg_humidity",
    "avg_wind_level"
]

context_summary = train[context_columns].describe().transpose()

print(context_summary.to_string())


# ============================================================
# 14. TRAIN / EVAL DATE RELATIONSHIP
# ============================================================

section("13. TRAIN / EVAL TIME RELATIONSHIP")

train_max_date = train_dates.max()
eval_min_date = eval_dates.min()

print(f"Last TRAIN date : {train_max_date}")
print(f"First EVAL date : {eval_min_date}")

if eval_min_date > train_max_date:

    print(
        "\nPASS: Evaluation period starts after "
        "the training period."
    )

else:

    print(
        "\nWARNING: Evaluation period overlaps "
        "or precedes training period."
    )


# ============================================================
# 15. SAMPLE DATA
# ============================================================

section("14. SAMPLE RECORD")

print(train.head(3).to_string(index=False))


# ============================================================
# 16. FINAL SUMMARY
# ============================================================

section("15. STEP 1.1 SUMMARY")

print(f"Train rows              : {len(train):,}")
print(f"Eval rows               : {len(eval_df):,}")
print(f"Columns                 : {len(train.columns)}")

print(
    f"Train missing values    : "
    f"{train_missing.sum():,}"
)

print(
    f"Eval missing values     : "
    f"{eval_missing.sum():,}"
)

print(
    f"Train duplicate rows    : "
    f"{train_duplicates:,}"
)

print(
    f"Eval duplicate rows     : "
    f"{eval_duplicates:,}"
)

print(
    f"Train unique stores     : "
    f"{train['store_id'].nunique():,}"
)

print(
    f"Train unique products   : "
    f"{train['product_id'].nunique():,}"
)

print(
    f"Train unique cities     : "
    f"{train['city_id'].nunique():,}"
)

print(
    f"Train unique dates      : "
    f"{train['dt'].nunique():,}"
)

print(
    f"Train date range        : "
    f"{train_dates.min()} → {train_dates.max()}"
)

print(
    f"Eval date range         : "
    f"{eval_dates.min()} → {eval_dates.max()}"
)


section("STEP 1.1 COMPLETE")

print("""
Dataset understanding checks completed.

DO NOT:
- Clean the data
- Modify raw Parquet files
- Create PostgreSQL tables
- Create ML features
- Start forecasting
- Start Power BI

Send the complete terminal output for verification.
""")