# ============================================================
# SMARTSTOCK AI
# STEP 9.4 — MARKET BASKET ANALYSIS (FP-Growth)
# ============================================================
#
# Computes association rules from Instacart prior orders using
# the FP-Growth algorithm via mlxtend.
#
# Outputs:
#   ml.market_basket_rules  - association rules (antecedent -> consequent)
#   ml.product_affinity     - top product pair co-purchase counts
#
# SAMPLING STRATEGY (Memory-Safe):
#   Problem: 1.94M transactions x 48,624 products = 88 GiB boolean matrix.
#   Solution: Restrict analysis to TOP_N_PRODUCTS most popular products.
#   This is standard academic practice for MBA:
#     - Association rules are only meaningful for high-frequency items.
#     - Rare products (purchased < 0.5% of orders) never meet min_support anyway.
#     - Limiting to top 500 products gives a matrix of
#       200,000 transactions x 500 products = 100 MB (very manageable).
#
# ACADEMIC JUSTIFICATION:
#   "We restrict market basket analysis to the 500 most frequently purchased
#    products, following common practice in association rule mining where
#    infrequent items cannot satisfy minimum support thresholds and are
#    therefore excluded from the frequent itemset generation step."
#
# PARAMETERS:
#   min_support    = 0.02: itemset must appear in >=2% of transactions
#   min_confidence = 0.20: 20% of orders with A also contain B
#   lift > 1.0: co-purchase is more frequent than by chance
#
# DATA GOVERNANCE:
#   All outputs are from the Instacart dataset and are labeled as
#   complementary market-basket evidence.
#
# Run from project root:
#   python "python/MARKET BASKET/step_9_4_market_basket.py"
# ============================================================

import sys
import time
from pathlib import Path

import pandas as pd
from sqlalchemy import text

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT / "python"))
from db_config import get_engine

# ── configuration ────────────────────────────────────────────
TOP_N_PRODUCTS  = 300     # only analyse the top N most popular products
MAX_USERS       = 20_000  # sample top N users by order count
MIN_SUPPORT     = 0.005   # itemset must appear in >=0.5% of transactions
MIN_CONFIDENCE  = 0.15    # rule confidence threshold
MIN_LIFT        = 1.0     # only keep rules where lift > 1
MAX_RULES       = 5_000   # cap stored rules (sorted by lift desc)


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


section("SMARTSTOCK AI - STEP 9.4: Market Basket Analysis (FP-Growth)")
print(f"Top {TOP_N_PRODUCTS} products | {MAX_USERS:,} users | "
      f"min_support={MIN_SUPPORT} | min_confidence={MIN_CONFIDENCE}")
print("\nDATA GOVERNANCE: Results represent Instacart customer basket patterns.")
print("Complementary behavioral evidence - not FreshRetailNet data.")

try:
    from mlxtend.frequent_patterns import fpgrowth, association_rules
    from mlxtend.preprocessing import TransactionEncoder
except ImportError:
    print("\nERROR: mlxtend is required. Install: pip install mlxtend")
    sys.exit(1)

engine = get_engine()

# ── step 1: select top N most popular products ────────────────
section("STEP 1: Select top popular products (memory-safe filter)")

with engine.connect() as conn:
    top_products_df = pd.read_sql(text(f"""
        SELECT product_name, purchase_count
        FROM ml.product_reorder_behavior
        ORDER BY purchase_count DESC
        LIMIT {TOP_N_PRODUCTS}
    """), conn)

top_product_names = set(top_products_df["product_name"].tolist())
print(f"  Top {len(top_product_names)} products selected")
print(f"  Min purchases in set: {top_products_df['purchase_count'].min():,}")
print(f"  Max purchases in set: {top_products_df['purchase_count'].max():,}")

# Estimated matrix size
with engine.connect() as conn:
    est_orders = conn.execute(text(f"""
        SELECT COUNT(DISTINCT o.order_id)
        FROM instacart.orders o
        JOIN instacart.order_products_prior opp ON o.order_id = opp.order_id
        JOIN instacart.products p ON opp.product_id = p.product_id
        WHERE o.eval_set = 'prior'
          AND p.product_name = ANY(:names)
        LIMIT 1
    """), {"names": list(top_product_names)[:10]}).scalar()

est_mb = (MAX_USERS * 1.5 * TOP_N_PRODUCTS) / (1024 * 1024)  # rough estimate
print(f"\n  Estimated matrix: ~{MAX_USERS*2:,} transactions x {TOP_N_PRODUCTS} products")
print(f"  Estimated memory: ~{est_mb:.0f} MB (safe)")

# ── step 2: select top users ──────────────────────────────────
section("STEP 2: Select top users by order count")

with engine.connect() as conn:
    top_users_df = pd.read_sql(text(f"""
        SELECT user_id, COUNT(*) AS order_count
        FROM instacart.orders
        WHERE eval_set = 'prior'
        GROUP BY user_id
        ORDER BY order_count DESC
        LIMIT {MAX_USERS}
    """), conn)

top_user_ids = top_users_df["user_id"].tolist()
print(f"  Users selected   : {len(top_user_ids):,}")
print(f"  Avg orders/user  : {top_users_df['order_count'].mean():.1f}")

# ── step 3: load baskets (top products only, top users) ────────
section("STEP 3: Load filtered baskets")
t0 = time.time()

with engine.connect() as conn:
    # Create temp table for user IDs
    conn.execute(text("DROP TABLE IF EXISTS pg_temp.mba_users;"))
    conn.execute(text("CREATE TEMP TABLE mba_users (user_id INTEGER);"))
    batch_size = 1000
    for i in range(0, len(top_user_ids), batch_size):
        batch = top_user_ids[i:i+batch_size]
        vals = ",".join(f"({u})" for u in batch)
        conn.execute(text(f"INSERT INTO mba_users VALUES {vals};"))
    conn.commit()

    baskets_df = pd.read_sql(text("""
        SELECT o.order_id, p.product_name
        FROM instacart.orders o
        JOIN instacart.order_products_prior opp ON o.order_id = opp.order_id
        JOIN instacart.products p               ON opp.product_id = p.product_id
        JOIN mba_users mu                       ON o.user_id = mu.user_id
        WHERE o.eval_set = 'prior'
    """), conn)

# Filter to top products only
baskets_df = baskets_df[baskets_df["product_name"].isin(top_product_names)]
print(f"  Line items (filtered): {len(baskets_df):,}  ({time.time()-t0:.1f}s)")

# ── step 4: build transactions ────────────────────────────────
section("STEP 4: Build transaction list")
t0 = time.time()

# Only keep orders that have at least 2 of the top products
# (orders with 0 or 1 popular item don't contribute useful rules)
order_counts = baskets_df.groupby("order_id")["product_name"].count()
valid_orders  = order_counts[order_counts >= 2].index
baskets_df    = baskets_df[baskets_df["order_id"].isin(valid_orders)]

transactions = (
    baskets_df.groupby("order_id")["product_name"]
    .apply(list)
    .tolist()
)

n_transactions = len(transactions)
print(f"  Transactions  : {n_transactions:,}")
print(f"  Avg basket    : {sum(len(t) for t in transactions)/max(n_transactions,1):.1f} items")
print(f"  Matrix size   : {n_transactions:,} x {TOP_N_PRODUCTS} = "
      f"{n_transactions * TOP_N_PRODUCTS / 1e6:.0f}M cells")

te = TransactionEncoder()
te_array = te.fit_transform(transactions)
basket_matrix = pd.DataFrame(te_array, columns=te.columns_)
print(f"  Matrix shape  : {basket_matrix.shape}  "
      f"(memory: ~{basket_matrix.memory_usage(deep=True).sum() / 1e6:.0f} MB)")
print(f"  Time          : {time.time()-t0:.1f}s")

# ── step 5: FP-Growth ─────────────────────────────────────────
section(f"STEP 5: FP-Growth (min_support={MIN_SUPPORT})")
t0 = time.time()

frequent_itemsets = fpgrowth(
    basket_matrix,
    min_support=MIN_SUPPORT,
    use_colnames=True,
    max_len=2
)
print(f"  Frequent itemsets : {len(frequent_itemsets):,}  ({time.time()-t0:.1f}s)")

# ── step 6: association rules ─────────────────────────────────
section(f"STEP 6: Association rules (confidence>={MIN_CONFIDENCE}, lift>={MIN_LIFT})")
t0 = time.time()

rules = association_rules(
    frequent_itemsets,
    metric="confidence",
    min_threshold=MIN_CONFIDENCE
)
rules = rules[rules["lift"] >= MIN_LIFT].copy()
rules = rules.sort_values("lift", ascending=False).head(MAX_RULES)

print(f"  Rules generated : {len(rules):,}  ({time.time()-t0:.1f}s)")

rules["antecedent_product"] = rules["antecedents"].apply(
    lambda x: list(x)[0] if len(x) == 1 else str(list(x))
)
rules["consequent_product"] = rules["consequents"].apply(
    lambda x: list(x)[0] if len(x) == 1 else str(list(x))
)

# ── step 7: save ml.market_basket_rules ───────────────────────
section("STEP 7: Save ml.market_basket_rules")

rules_out = rules[[
    "antecedent_product", "consequent_product",
    "support", "confidence", "lift", "leverage", "conviction"
]].copy()

for col in ["support", "confidence", "lift", "leverage", "conviction"]:
    rules_out[col] = rules_out[col].round(6)

rules_out["sample_users"]              = MAX_USERS
rules_out["top_n_products_analysed"]   = TOP_N_PRODUCTS
rules_out["min_support_threshold"]     = MIN_SUPPORT
rules_out["min_confidence_threshold"]  = MIN_CONFIDENCE
rules_out["n_transactions"]            = n_transactions

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS ml.market_basket_rules;"))
    conn.commit()

rules_out.to_sql("market_basket_rules", engine, schema="ml",
                 if_exists="replace", index=False)
print(f"PASS: ml.market_basket_rules saved ({len(rules_out):,} rules).")

# ── step 8: save ml.product_affinity ──────────────────────────
section("STEP 8: Save ml.product_affinity")

affinity_out = rules_out.sort_values("support", ascending=False).head(2000).copy()

with engine.connect() as conn:
    prod_map = pd.read_sql(text("""
        SELECT product_name, product_id FROM instacart.products
    """), conn)

name_to_id = prod_map.set_index("product_name")["product_id"].to_dict()

affinity_out["antecedent_product_id"] = affinity_out["antecedent_product"].map(name_to_id)
affinity_out["consequent_product_id"] = affinity_out["consequent_product"].map(name_to_id)

affinity_final = affinity_out[[
    "antecedent_product_id", "antecedent_product",
    "consequent_product_id", "consequent_product",
    "support", "confidence", "lift"
]].copy()

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS ml.product_affinity;"))
    conn.commit()

affinity_final.to_sql("product_affinity", engine, schema="ml",
                      if_exists="replace", index=False)
print(f"PASS: ml.product_affinity saved ({len(affinity_final):,} pairs).")

# ── step 9: final summary ──────────────────────────────────────
section("RESULTS SUMMARY")

with engine.connect() as conn:
    rule_count  = conn.execute(text("SELECT COUNT(*) FROM ml.market_basket_rules")).scalar()
    affin_count = conn.execute(text("SELECT COUNT(*) FROM ml.product_affinity")).scalar()

    print(f"\n  ml.market_basket_rules : {rule_count:,} rules")
    print(f"  ml.product_affinity    : {affin_count:,} product pairs")
    print(f"  Products analysed      : top {TOP_N_PRODUCTS} by purchase count")
    print(f"  Users sampled          : {MAX_USERS:,}")
    print(f"  Transactions           : {n_transactions:,}")

    print("\n  Top 15 Rules by Lift:")
    rows = conn.execute(text("""
        SELECT antecedent_product, consequent_product, support, confidence, lift
        FROM ml.market_basket_rules
        ORDER BY lift DESC LIMIT 15
    """)).fetchall()

    print(f"\n  {'Antecedent':<35}  ->  {'Consequent':<35}  {'Sup':>6}  {'Conf':>5}  {'Lift':>5}")
    print("  " + "-" * 103)
    for r in rows:
        print(f"  {r[0][:35]:<35}  ->  {r[1][:35]:<35}  "
              f"{r[2]:>6.4f}  {r[3]:>5.3f}  {r[4]:>5.3f}")

print("\n" + "=" * 70)
print("STEP 9.4 COMPLETED SUCCESSFULLY")
print("Market basket analysis complete.")
print("=" * 70)
