from pathlib import Path
import pandas as pd


# ============================================================
# SMARTSTOCK AI
# STEP 0.3 - RAW DATASET VERIFICATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TRAIN_PATH = PROJECT_ROOT / "data" / "raw" / "freshretail_train.parquet"
EVAL_PATH = PROJECT_ROOT / "data" / "raw" / "freshretail_eval.parquet"


print("=" * 70)
print("SMARTSTOCK AI - STEP 0.3")
print("RAW DATASET VERIFICATION")
print("=" * 70)


# ------------------------------------------------------------
# 1. Check files
# ------------------------------------------------------------

print("\n1. FILE EXISTENCE")
print("-" * 70)

print(f"Train: {TRAIN_PATH}")
print(f"Exists: {TRAIN_PATH.exists()}")

print(f"\nEval: {EVAL_PATH}")
print(f"Exists: {EVAL_PATH.exists()}")


if not TRAIN_PATH.exists():
    raise FileNotFoundError("Train Parquet file was not found.")

if not EVAL_PATH.exists():
    raise FileNotFoundError("Eval Parquet file was not found.")


# ------------------------------------------------------------
# 2. Read Parquet metadata
# ------------------------------------------------------------

print("\n2. PARQUET FILE INFORMATION")
print("-" * 70)

train_info = pd.read_parquet(TRAIN_PATH)
eval_info = pd.read_parquet(EVAL_PATH)

print("Both Parquet files loaded successfully.")


# ------------------------------------------------------------
# 3. Shape
# ------------------------------------------------------------

print("\n3. DATASET SHAPE")
print("-" * 70)

print(f"Train rows    : {len(train_info):,}")
print(f"Train columns : {len(train_info.columns)}")

print(f"\nEval rows     : {len(eval_info):,}")
print(f"Eval columns  : {len(eval_info.columns)}")


# ------------------------------------------------------------
# 4. Column check
# ------------------------------------------------------------

print("\n4. COLUMN CHECK")
print("-" * 70)

print("Train columns:")

for column in train_info.columns:
    print(f"  - {column}")


print("\nTrain and Eval columns identical:")

if list(train_info.columns) == list(eval_info.columns):
    print("YES")
else:
    print("NO")


# ------------------------------------------------------------
# 5. Basic sample
# ------------------------------------------------------------

print("\n5. FIRST 5 TRAIN ROWS")
print("-" * 70)

print(train_info.head().to_string())


print("\n6. FIRST 5 EVAL ROWS")
print("-" * 70)

print(eval_info.head().to_string())


# ------------------------------------------------------------
# 6. Final verification
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("STEP 0.3 VERIFICATION COMPLETE")
print("=" * 70)

print("""
Both FreshRetailNet-50K Parquet files were successfully read.

Do NOT modify the raw data.

Next:
STEP 1.1 - Dataset Understanding
""")