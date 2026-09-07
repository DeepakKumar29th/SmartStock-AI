# ============================================================
# SMARTSTOCK AI
# STEP 9.5 — CROSS-DATASET INTELLIGENCE VIEW
# ============================================================
#
# Creates analytics.unified_product_intelligence
#
# This view represents the ANALYTICAL INTEGRATION of two
# independent datasets:
#
#   LEFT  SIDE: FreshRetailNet inventory/demand signals
#   RIGHT SIDE: Instacart customer purchase-behavior signals
#
# HOW IT WORKS:
#   FreshRetailNet has products identified by integer product_id.
#   Instacart has products identified by product_name.
#   There is NO valid ID-level join between them.
#
#   Instead, we join at the SIGNAL level:
#   - Both datasets are aggregated independently
#   - Instacart signals are ranked globally (popularity rank, reorder rate)
#   - The view presents FreshRetailNet products alongside the
#     Instacart behavioral context, clearly labeled
#
#   HOW TO READ THE VIEW:
#   "Product [X] from FreshRetailNet has HIGH stockout risk
#   and HIGH replenishment priority.
#   From the Instacart dataset (a complementary grocery source),
#   the most popular products in the [department] category have
#   a high reorder rate, suggesting this product category has
#   strong habitual purchase behavior."
#
# ACADEMIC STATEMENT:
#   The integration is ANALYTICAL, not a literal transaction merge.
#   It demonstrates the SmartStock AI dual-signal architecture.
#   Product IDs from the two datasets are NOT equivalent.
#
# Run from project root:
#   python python/MARKET BASKET/step_9_5_unified_intelligence.py
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
section("SMARTSTOCK AI — STEP 9.5: Cross-Dataset Intelligence View")

with engine.connect() as conn:

    # ----------------------------------------------------------
    # Create analytics schema if missing
    # ----------------------------------------------------------
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics;"))
    conn.commit()
    print("PASS: analytics schema ready.")

    # ----------------------------------------------------------
    # Instacart department-level behavioral summary
    # (Used as the "market-basket signal" dimension)
    # ----------------------------------------------------------
    conn.execute(text("DROP TABLE IF EXISTS analytics.instacart_dept_signals;"))
    conn.execute(text("""
        CREATE TABLE analytics.instacart_dept_signals AS

        SELECT
            department,
            COUNT(*)                            AS product_count,
            ROUND(AVG(purchase_count)::numeric, 0)  AS avg_purchases,
            ROUND(AVG(reorder_rate_pct)::numeric, 2) AS avg_reorder_rate,
            ROUND(MAX(purchase_count)::numeric, 0)  AS max_purchases,

            -- Department-level reorder signal
            CASE
                WHEN AVG(reorder_rate_pct) >= 55 THEN 'HIGH'
                WHEN AVG(reorder_rate_pct) >= 35 THEN 'MEDIUM'
                ELSE 'LOW'
            END AS dept_reorder_signal,

            -- Top 3 most purchased products in this department (for display)
            STRING_AGG(
                product_name,
                ', '
                ORDER BY purchase_count DESC
            ) FILTER (WHERE popularity_rank <= 3) AS top_products_example

        FROM ml.product_reorder_behavior
        GROUP BY department
        ORDER BY avg_reorder_rate DESC;
    """))
    conn.commit()
    print("PASS: analytics.instacart_dept_signals created.")

    # ----------------------------------------------------------
    # Main unified view
    # FreshRetailNet product risk + Instacart category signal
    # ----------------------------------------------------------
    conn.execute(text("DROP VIEW IF EXISTS analytics.unified_product_intelligence CASCADE;"))
    conn.execute(text("""
        CREATE VIEW analytics.unified_product_intelligence AS

        -- =========================================================
        -- DATA GOVERNANCE NOTE:
        -- This view joins FreshRetailNet product-level inventory risk
        -- with Instacart DEPARTMENT-LEVEL market basket signals.
        -- The join is on: general fresh/produce department categories.
        -- This is an ANALYTICAL APPROXIMATION, not a literal merge.
        -- FreshRetailNet and Instacart product IDs are NOT equivalent.
        -- =========================================================

        SELECT
            -- FreshRetailNet inventory signals
            pr.product_id,
            pr.management_group_id,
            pr.first_category_id,
            pr.second_category_id,
            pr.third_category_id,

            ROUND(pr.total_sales::numeric, 2)       AS total_sales,
            ROUND(pr.predicted_sales::numeric, 2)   AS predicted_sales,
            pr.high_risk_days,
            pr.urgent_reorders,
            ROUND(pr.avg_reorder_qty::numeric, 1)   AS avg_reorder_qty,
            ROUND(pr.high_risk_pct::numeric, 2)     AS high_risk_pct,

            -- Derived inventory risk level
            CASE
                WHEN pr.high_risk_pct >= 50 THEN 'HIGH'
                WHEN pr.high_risk_pct >= 20 THEN 'MEDIUM'
                ELSE 'LOW'
            END AS inventory_risk_level,

            -- Top replenishment priority
            CASE
                WHEN pr.urgent_reorders >= 5 AND pr.high_risk_pct >= 50 THEN 'HIGH'
                WHEN pr.urgent_reorders >= 2 OR pr.high_risk_pct >= 20  THEN 'MEDIUM'
                ELSE 'LOW'
            END AS replenishment_priority,

            -- ── Instacart behavioral signal ────────────────────
            -- Note: mapped by approximated produce/fresh category;
            -- labeled as complementary evidence.
            -- For FreshRetailNet (perishable produce dataset),
            -- we use the Instacart 'produce' department as the
            -- most relevant behavioral proxy.
            ids.avg_reorder_rate            AS instacart_dept_reorder_rate,
            ids.dept_reorder_signal         AS instacart_reorder_signal,
            ids.top_products_example        AS instacart_example_products,

            -- Combined business recommendation
            CASE
                WHEN pr.high_risk_pct >= 50
                     AND ids.dept_reorder_signal = 'HIGH'
                THEN 'URGENT: High inventory risk confirmed by strong customer reorder signal. Prioritize replenishment immediately.'

                WHEN pr.high_risk_pct >= 50
                     AND ids.dept_reorder_signal = 'MEDIUM'
                THEN 'HIGH PRIORITY: High inventory risk. Moderate customer reorder signal from complementary data. Replenishment recommended.'

                WHEN pr.high_risk_pct >= 20
                     AND ids.dept_reorder_signal = 'HIGH'
                THEN 'MEDIUM PRIORITY: Moderate inventory risk. Strong customer purchase signal. Monitor closely and plan replenishment.'

                WHEN pr.urgent_reorders = 0 AND pr.high_risk_pct < 10
                THEN 'LOW PRIORITY: Low inventory risk. Routine monitoring.'

                ELSE 'REVIEW: Mixed signals. Cross-reference store-level data before deciding.'
            END AS business_recommendation,

            -- Source labels for transparency
            'FreshRetailNet-50K'    AS inventory_data_source,
            'Instacart (produce dept proxy)'
                                    AS basket_data_source,
            'Complementary analytical signal — not a literal data merge'
                                    AS integration_note

        FROM ml.product_recommendations pr

        -- Cross-dataset join: use Instacart 'produce' department
        -- as the behavioral proxy for FreshRetailNet perishable SKUs.
        -- This is a deliberate analytical approximation documented here.
        CROSS JOIN (
            SELECT *
            FROM analytics.instacart_dept_signals
            WHERE department = 'produce'
            LIMIT 1
        ) ids

        ORDER BY pr.high_risk_pct DESC, pr.urgent_reorders DESC;
    """))
    conn.commit()
    print("PASS: analytics.unified_product_intelligence view created.")

    # ----------------------------------------------------------
    # Validation
    # ----------------------------------------------------------
    section("Validation")

    cnt = conn.execute(text(
        "SELECT COUNT(*) FROM analytics.unified_product_intelligence"
    )).scalar()
    print(f"  View rows        : {cnt:,} (= {cnt} FreshRetailNet products)")

    print("\n  Top 15 Products by Inventory Risk + Basket Signal:")
    rows = conn.execute(text("""
        SELECT
            product_id,
            high_risk_pct,
            inventory_risk_level,
            replenishment_priority,
            avg_reorder_qty,
            instacart_reorder_signal,
            LEFT(business_recommendation, 60) AS recommendation
        FROM analytics.unified_product_intelligence
        WHERE inventory_risk_level = 'HIGH'
        ORDER BY high_risk_pct DESC
        LIMIT 15
    """)).fetchall()

    print(f"\n  {'ProdID':>6}  {'Risk%':>6}  {'InvRisk':<8}  {'Priority':<8}  {'ReorderQty':>10}  {'BasketSig':<10}  Recommendation")
    print("  " + "-" * 100)
    for r in rows:
        print(f"  {r[0]:>6}  {r[1]:>6}%  {r[2]:<8}  {r[3]:<8}  {r[4]:>10}  {r[5]:<10}  {r[6]}")

    # Instacart dept signals table
    section("Instacart Department Behavioral Signals")
    rows = conn.execute(text("""
        SELECT department, product_count, avg_reorder_rate,
               dept_reorder_signal, top_products_example
        FROM analytics.instacart_dept_signals
        ORDER BY avg_reorder_rate DESC
        LIMIT 15
    """)).fetchall()

    print(f"\n  {'Department':<20}  {'Products':>8}  {'AvgReorder%':>12}  {'Signal':<8}  Top Examples")
    print("  " + "-" * 90)
    for r in rows:
        examples = (r[4] or "")[:50]
        print(f"  {r[0]:<20}  {r[1]:>8,}  {r[2]:>12}%  {r[3]:<8}  {examples}")

print("\n" + "=" * 70)
print("STEP 9.5 COMPLETED SUCCESSFULLY")
print("analytics.unified_product_intelligence is ready.")
print("=" * 70)
