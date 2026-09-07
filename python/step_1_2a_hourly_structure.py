from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# SMARTSTOCK AI
# STEP 1.2A - HOURLY STOCK & SALES STRUCTURE VERIFICATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TRAIN_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "freshretail_train.parquet"
)

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 180)


def section(title):
    print("\n" + "=" * 85)
    print(title)
    print("=" * 85)


# ============================================================
# 1. LOAD DATA
# ============================================================

section("SMARTSTOCK AI - STEP 1.2A")

print("Loading training dataset...")

df = pd.read_parquet(TRAIN_PATH)

print(f"Loaded {len(df):,} rows.")


# ============================================================
# 2. ARRAY LENGTH CHECK
# ============================================================

section("1. ARRAY LENGTH CHECK")


def array_length(value):

    if isinstance(value, (list, tuple, np.ndarray)):
        return len(value)

    return None


hours_sale_lengths = df["hours_sale"].map(array_length)
stock_status_lengths = df["hours_stock_status"].map(array_length)

print("hours_sale array lengths:")
print(hours_sale_lengths.value_counts().sort_index().to_string())

print("\nhours_stock_status array lengths:")
print(stock_status_lengths.value_counts().sort_index().to_string())

print("\nInvalid hours_sale lengths:")
print((hours_sale_lengths != 24).sum())

print("\nInvalid hours_stock_status lengths:")
print((stock_status_lengths != 24).sum())


# ============================================================
# 3. STOCK STATUS VALUES
# ============================================================

section("2. STOCK STATUS VALUE CHECK")

unique_status_values = set()

for value in df["hours_stock_status"].head(10000):

    array = np.asarray(value)

    unique_status_values.update(array.tolist())

print("Unique values found in first 10,000 rows:")

print(sorted(unique_status_values))

invalid_status_count = 0

for value in df["hours_stock_status"].head(10000):

    array = np.asarray(value)

    if not np.isin(array, [0, 1]).all():
        invalid_status_count += 1

print(
    f"\nRows containing values other than 0/1 "
    f"in first 10,000 rows: {invalid_status_count}"
)


# ============================================================
# 4. SAMPLE HOURLY RECORDS
# ============================================================

section("3. SAMPLE HOURLY RECORDS")

sample = df.head(10)

for index, row in sample.iterrows():

    sales = np.asarray(row["hours_sale"], dtype=float)
    status = np.asarray(row["hours_stock_status"], dtype=int)

    print("\n" + "-" * 80)

    print(f"Row index       : {index}")
    print(f"Date            : {row['dt']}")
    print(f"Store           : {row['store_id']}")
    print(f"Product         : {row['product_id']}")

    print(f"Daily sale_amount: {row['sale_amount']}")
    print(f"Sum hourly sales : {sales.sum():.4f}")

    print(
        f"stock_hour6_22_cnt: "
        f"{row['stock_hour6_22_cnt']}"
    )

    print(
        f"Total stockout hours "
        f"(sum of status): {status.sum()}"
    )

    print("\nHourly stock status:")

    for hour, value in enumerate(status):

        print(f"{hour:02d}:00 -> {value}", end="    ")

        if (hour + 1) % 6 == 0:
            print()


# ============================================================
# 5. CHECK STOCKOUT COUNT RELATIONSHIP
# ============================================================

section("4. STOCKOUT COUNT RELATIONSHIP")

# The official dataset defines stock_hour6_22_cnt as the number
# of out-of-stock hours between 06:00 and 22:00.
#
# Python slicing [6:22] represents:
# 06:00, 07:00, ..., 21:00
#
# This gives 16 hourly positions.
#
# We test this relationship directly.

sample_size = min(10000, len(df))

stockout_matches = 0
stockout_mismatches = 0

examples = []

for _, row in df.head(sample_size).iterrows():

    status = np.asarray(
        row["hours_stock_status"],
        dtype=int
    )

    expected_count = status[6:22].sum()

    actual_count = int(
        row["stock_hour6_22_cnt"]
    )

    if expected_count == actual_count:

        stockout_matches += 1

    else:

        stockout_mismatches += 1

        if len(examples) < 5:

            examples.append({
                "date": row["dt"],
                "store_id": row["store_id"],
                "product_id": row["product_id"],
                "actual": actual_count,
                "calculated": int(expected_count),
                "status": status.tolist()
            })


print(
    f"Rows tested: {sample_size:,}"
)

print(
    f"Matches: {stockout_matches:,}"
)

print(
    f"Mismatches: {stockout_mismatches:,}"
)

if examples:

    print("\nFirst mismatch examples:")

    for example in examples:

        print(example)


# ============================================================
# 6. DAILY SALES VS HOURLY SALES
# ============================================================

section("5. DAILY SALES VS HOURLY SALES")

sales_differences = []

for _, row in df.head(10000).iterrows():

    hourly_sales = np.asarray(
        row["hours_sale"],
        dtype=float
    )

    daily_sales = float(row["sale_amount"])

    hourly_sum = hourly_sales.sum()

    sales_differences.append(
        abs(daily_sales - hourly_sum)
    )

sales_differences = np.asarray(
    sales_differences
)

print(
    f"Rows tested: {len(sales_differences):,}"
)

print(
    f"Maximum absolute difference: "
    f"{sales_differences.max():.10f}"
)

print(
    f"Mean absolute difference: "
    f"{sales_differences.mean():.10f}"
)

print(
    f"Rows with exact match: "
    f"{(sales_differences == 0).sum():,}"
)


# ============================================================
# 7. HOURLY POSITION INSPECTION
# ============================================================

section("6. HOURLY POSITION MAP")

print(
    """
We have 24 positions in each hourly array.

The positions are indexed below:

Position     Assumed clock hour
--------------------------------
0            00:00
1            01:00
2            02:00
3            03:00
4            04:00
5            05:00
6            06:00
7            07:00
8            08:00
9            09:00
10           10:00
11           11:00
12           12:00
13           13:00
14           14:00
15           15:00
16           16:00
17           17:00
18           18:00
19           19:00
20           20:00
21           21:00
22           22:00
23           23:00
"""
)

print(
    "IMPORTANT: The exact interpretation of the "
    "hour positions will be validated using the "
    "stock_hour6_22_cnt relationship above."
)


# ============================================================
# 8. STOCKOUT SUMMARY
# ============================================================

section("7. STOCKOUT SUMMARY")

sample_status_counts = []

for value in df["hours_stock_status"].head(10000):

    status = np.asarray(value, dtype=int)

    sample_status_counts.append(status.sum())

sample_status_counts = np.asarray(
    sample_status_counts
)

print(
    f"Rows analysed: {len(sample_status_counts):,}"
)

print(
    f"Rows with at least one stockout hour: "
    f"{(sample_status_counts > 0).sum():,}"
)

print(
    f"Rows with zero stockout hours: "
    f"{(sample_status_counts == 0).sum():,}"
)

print(
    f"Maximum stockout hours in one day: "
    f"{sample_status_counts.max():,}"
)

print(
    f"Average stockout hours per row: "
    f"{sample_status_counts.mean():.2f}"
)


# ============================================================
# 9. FINAL STATUS
# ============================================================

section("STEP 1.2A STATUS")

print(
    """
Hourly structure verification completed.

DO NOT:
- Modify the raw dataset
- Create database tables
- Flatten the arrays permanently
- Create ML features
- Start forecasting

Send the COMPLETE terminal output.

We will use the results to finalize Step 1.2.
"""
)