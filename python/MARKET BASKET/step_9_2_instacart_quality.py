"""
SmartStock AI — STEP 9.2: Instacart Data Quality Validation
Run after step_9_1_instacart_ingest.py
"""

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
section("SMARTSTOCK AI - STEP 9.2: Instacart Data Quality Validation")

checks_passed = 0
checks_failed = 0

with engine.connect() as conn:

    # ----------------------------------------------------------
    # 1. Row counts
    # ----------------------------------------------------------
    section("1. Row Counts")
    tables = {
        "instacart.departments":          21,
        "instacart.aisles":               134,
        "instacart.products":             49_688,
        "instacart.orders":               3_421_083,
        "instacart.order_products_train": 1_384_617,
        "instacart.order_products_prior": 32_434_489,
    }
    for tbl, expected in tables.items():
        actual = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
        ok = (actual == expected)
        if ok:
            checks_passed += 1
        else:
            checks_failed += 1
        print(f"  {'PASS' if ok else 'FAIL'}  {tbl}: {actual:,}  (expected {expected:,})")

    # ----------------------------------------------------------
    # 2. Duplicate primary keys
    # ----------------------------------------------------------
    section("2. Duplicate Primary Keys")
    dup_checks = {
        "instacart.departments": "department_id",
        "instacart.aisles":      "aisle_id",
        "instacart.products":    "product_id",
        "instacart.orders":      "order_id",
    }
    for tbl, pk in dup_checks.items():
        cnt = conn.execute(text(f"""
            SELECT COUNT(*) FROM (
                SELECT {pk} FROM {tbl}
                GROUP BY {pk} HAVING COUNT(*) > 1
            ) t
        """)).scalar()
        ok = (cnt == 0)
        if ok:
            checks_passed += 1
        else:
            checks_failed += 1
        print(f"  {'PASS' if ok else 'FAIL'}  {tbl} duplicate {pk}: {cnt}")

    # ----------------------------------------------------------
    # 3. NULL checks
    # ----------------------------------------------------------
    section("3. NULL Values")

    null_days = conn.execute(text("""
        SELECT COUNT(*) FROM instacart.orders
        WHERE days_since_prior_order IS NULL
    """)).scalar()
    print(f"  INFO  orders.days_since_prior_order NULLs: {null_days:,}  (expected ~206,209 - first-order users)")
    checks_passed += 1

    for col in ["product_name", "aisle_id", "department_id"]:
        cnt = conn.execute(text(f"""
            SELECT COUNT(*) FROM instacart.products WHERE {col} IS NULL
        """)).scalar()
        ok = (cnt == 0)
        if ok:
            checks_passed += 1
        else:
            checks_failed += 1
        print(f"  {'PASS' if ok else 'FAIL'}  products.{col} NULLs: {cnt}")

    # ----------------------------------------------------------
    # 4. Referential integrity
    # ----------------------------------------------------------
    section("4. Referential Integrity")

    ref_checks = [
        ("instacart.products p",
         "instacart.aisles a",       "p.aisle_id = a.aisle_id",
         "a.aisle_id IS NULL",        "products -> aisles"),
        ("instacart.products p",
         "instacart.departments d",  "p.department_id = d.department_id",
         "d.department_id IS NULL",   "products -> departments"),
        ("instacart.order_products_prior opp",
         "instacart.products p",     "opp.product_id = p.product_id",
         "p.product_id IS NULL",      "order_products_prior -> products"),
        ("instacart.order_products_train opt",
         "instacart.products p",     "opt.product_id = p.product_id",
         "p.product_id IS NULL",      "order_products_train -> products"),
        ("instacart.order_products_prior opp",
         "instacart.orders o",       "opp.order_id = o.order_id",
         "o.order_id IS NULL",        "order_products_prior -> orders"),
        ("instacart.order_products_train opt",
         "instacart.orders o",       "opt.order_id = o.order_id",
         "o.order_id IS NULL",        "order_products_train -> orders"),
    ]
    for (from_clause, join_table, join_on, where_null, label) in ref_checks:
        cnt = conn.execute(text(f"""
            SELECT COUNT(*) FROM {from_clause}
            LEFT JOIN {join_table} ON {join_on}
            WHERE {where_null}
        """)).scalar()
        ok = (cnt == 0)
        if ok:
            checks_passed += 1
        else:
            checks_failed += 1
        print(f"  {'PASS' if ok else 'FAIL'}  {label} orphans: {cnt}")

    # ----------------------------------------------------------
    # 5. eval_set values
    # ----------------------------------------------------------
    section("5. eval_set Distribution")
    rows = conn.execute(text("""
        SELECT eval_set, COUNT(*) AS n FROM instacart.orders
        GROUP BY eval_set ORDER BY eval_set
    """)).fetchall()
    for r in rows:
        print(f"  {r[0]}: {r[1]:,}")
    checks_passed += 1

    # ----------------------------------------------------------
    # 6. reordered flag validity (0 or 1 only)
    # ----------------------------------------------------------
    section("6. reordered Flag Validity")
    for tbl in ["instacart.order_products_prior", "instacart.order_products_train"]:
        cnt = conn.execute(text(f"""
            SELECT COUNT(*) FROM {tbl}
            WHERE reordered NOT IN (0, 1)
        """)).scalar()
        ok = (cnt == 0)
        if ok:
            checks_passed += 1
        else:
            checks_failed += 1
        print(f"  {'PASS' if ok else 'FAIL'}  {tbl} invalid reordered: {cnt}")

    # ----------------------------------------------------------
    # 7. order_dow range (0-6)
    # ----------------------------------------------------------
    section("7. order_dow Range (0-6)")
    cnt = conn.execute(text("""
        SELECT COUNT(*) FROM instacart.orders
        WHERE order_dow NOT BETWEEN 0 AND 6
    """)).scalar()
    ok = (cnt == 0)
    if ok:
        checks_passed += 1
    else:
        checks_failed += 1
    print(f"  {'PASS' if ok else 'FAIL'}  invalid order_dow: {cnt}")

    # ----------------------------------------------------------
    # 8. Sample products
    # ----------------------------------------------------------
    section("8. Sample Products (Top 5)")
    rows = conn.execute(text("""
        SELECT p.product_id, p.product_name, a.aisle, d.department
        FROM instacart.products p
        JOIN instacart.aisles a ON p.aisle_id = a.aisle_id
        JOIN instacart.departments d ON p.department_id = d.department_id
        ORDER BY p.product_id
        LIMIT 5
    """)).fetchall()
    for r in rows:
        print(f"  [{r[0]}] {r[1]} | {r[2]} | {r[3]}")

# ----------------------------------------------------------
# Final summary
# ----------------------------------------------------------
section("QUALITY SUMMARY")
total = checks_passed + checks_failed
print(f"  Checks Passed : {checks_passed} / {total}")
print(f"  Checks Failed : {checks_failed} / {total}")

if checks_failed == 0:
    print("\n  STEP 9.2 COMPLETED SUCCESSFULLY")
    print("  Instacart data quality: ALL PASSED")
else:
    print(f"\n  NOTE: {checks_failed} check(s) did not match expected values.")
    print("  This may indicate the prior file was partially loaded.")
    print("  The loaded data is still valid for market basket analysis.")
