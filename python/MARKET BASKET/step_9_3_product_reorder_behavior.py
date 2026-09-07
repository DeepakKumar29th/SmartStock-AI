# ============================================================
# SMARTSTOCK AI
# STEP 9.3 — PRODUCT REORDER BEHAVIOR
# ============================================================
#
# Computes per-product behavioral statistics from Instacart:
#   - purchase_count        : total times the product appears in orders
#   - reorder_count         : times the product was re-ordered
#   - reorder_rate          : reorder_count / purchase_count
#   - unique_users          : distinct users who bought this product
#   - avg_add_to_cart_order : typical position when added to basket
#
# Output table: ml.product_reorder_behavior
#
# IMPORTANT DATA GOVERNANCE NOTE:
#   These statistics come from the Instacart grocery dataset, not from
#   FreshRetailNet. They describe customer purchase patterns in a
#   different grocery retail environment. They cannot be assumed to
#   represent the same customer population as FreshRetailNet.
#   All downstream reports must label this as
#   "complementary market-basket evidence from the Instacart dataset."
#
# Run from project root:
#   python python/MARKET BASKET/step_9_3_product_reorder_behavior.py
# ============================================================

import sys
from pathlib import Path
from sqlalchemy import text

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT / "python"))
from db_config import get_engine


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


engine = get_engine()

section("SMARTSTOCK AI — STEP 9.3: Product Reorder Behavior")
print("Computing per-product statistics from Instacart prior+train orders...")
print("\nDATA GOVERNANCE: These statistics originate from the Instacart dataset")
print("and represent a complementary customer purchase-behavior signal only.")

with engine.connect() as conn:

    # ----------------------------------------------------------
    # Drop + recreate
    # ----------------------------------------------------------
    section("Creating ml.product_reorder_behavior")

    conn.execute(text("DROP TABLE IF EXISTS ml.product_reorder_behavior;"))
    conn.execute(text("""
        CREATE TABLE ml.product_reorder_behavior AS

        WITH combined AS (
            -- Union prior + train to get full purchase history
            SELECT order_id, product_id, add_to_cart_order, reordered
            FROM instacart.order_products_prior
            UNION ALL
            SELECT order_id, product_id, add_to_cart_order, reordered
            FROM instacart.order_products_train
        ),

        order_users AS (
            SELECT order_id, user_id
            FROM instacart.orders
        )

        SELECT
            c.product_id,
            p.product_name,
            a.aisle,
            d.department,

            COUNT(*)                                AS purchase_count,
            SUM(c.reordered)                        AS reorder_count,

            ROUND(
                100.0 * SUM(c.reordered) / COUNT(*),
                2
            )                                       AS reorder_rate_pct,

            COUNT(DISTINCT ou.user_id)              AS unique_users,

            ROUND(
                AVG(c.add_to_cart_order)::numeric, 2
            )                                       AS avg_cart_position,

            -- Popularity rank (1 = most purchased)
            RANK() OVER (ORDER BY COUNT(*) DESC)    AS popularity_rank,

            -- Reorder signal: HIGH / MEDIUM / LOW
            CASE
                WHEN ROUND(100.0 * SUM(c.reordered) / COUNT(*), 2) >= 60 THEN 'HIGH'
                WHEN ROUND(100.0 * SUM(c.reordered) / COUNT(*), 2) >= 35 THEN 'MEDIUM'
                ELSE 'LOW'
            END                                     AS reorder_signal

        FROM combined c
        JOIN instacart.products p   ON c.product_id    = p.product_id
        JOIN instacart.aisles a     ON p.aisle_id       = a.aisle_id
        JOIN instacart.departments d ON p.department_id = d.department_id
        JOIN order_users ou          ON c.order_id      = ou.order_id

        GROUP BY
            c.product_id,
            p.product_name,
            a.aisle,
            d.department

        ORDER BY purchase_count DESC;
    """))
    conn.commit()
    print("PASS: ml.product_reorder_behavior created.")

    # ----------------------------------------------------------
    # Index
    # ----------------------------------------------------------
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_prb_product_id
        ON ml.product_reorder_behavior(product_id);
    """))
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_prb_reorder_signal
        ON ml.product_reorder_behavior(reorder_signal);
    """))
    conn.commit()
    print("PASS: Indexes created.")

    # ----------------------------------------------------------
    # Validation
    # ----------------------------------------------------------
    section("Validation")

    total = conn.execute(text(
        "SELECT COUNT(*) FROM ml.product_reorder_behavior"
    )).scalar()
    print(f"  Total products in table : {total:,}")

    rows = conn.execute(text("""
        SELECT reorder_signal, COUNT(*), ROUND(AVG(reorder_rate_pct),2) AS avg_rate
        FROM ml.product_reorder_behavior
        GROUP BY reorder_signal
        ORDER BY reorder_signal
    """)).fetchall()
    print("\n  Reorder Signal Distribution:")
    for r in rows:
        print(f"    {r[0]:<8} {r[1]:>6,} products  |  avg rate: {r[2]}%")

    section("Top 15 Most Purchased Products (Instacart)")
    rows = conn.execute(text("""
        SELECT
            product_id,
            product_name,
            department,
            aisle,
            purchase_count,
            reorder_rate_pct,
            reorder_signal
        FROM ml.product_reorder_behavior
        ORDER BY purchase_count DESC
        LIMIT 15
    """)).fetchall()
    print(f"\n  {'ID':>6}  {'Product':<45}  {'Dept':<15}  {'Purchases':>9}  {'Reorder%':>9}  {'Signal'}")
    print("  " + "-" * 110)
    for r in rows:
        print(f"  {r[0]:>6}  {r[1][:45]:<45}  {r[3][:15]:<15}  {r[4]:>9,}  {r[5]:>9}%  {r[6]}")

    section("Top 15 Highest Reorder Rate Products (min 1,000 purchases)")
    rows = conn.execute(text("""
        SELECT
            product_id,
            product_name,
            department,
            purchase_count,
            reorder_rate_pct,
            reorder_signal
        FROM ml.product_reorder_behavior
        WHERE purchase_count >= 1000
        ORDER BY reorder_rate_pct DESC
        LIMIT 15
    """)).fetchall()
    print(f"\n  {'ID':>6}  {'Product':<45}  {'Dept':<15}  {'Purchases':>9}  {'Reorder%':>9}")
    print("  " + "-" * 100)
    for r in rows:
        print(f"  {r[0]:>6}  {r[1][:45]:<45}  {r[2][:15]:<15}  {r[3]:>9,}  {r[4]:>9}%")

print("\n" + "=" * 70)
print("STEP 9.3 COMPLETED SUCCESSFULLY")
print("ml.product_reorder_behavior is ready.")
print("=" * 70)
