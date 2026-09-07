# ============================================================
# SMARTSTOCK AI
# streamlit/data_loader.py — All Data Loading Functions
# ============================================================

import pandas as pd
from sqlalchemy import text


# ──────────────────────────────────────────────────────────────
# FreshRetailNet / Inventory Layer
# ──────────────────────────────────────────────────────────────

def load_business_kpis(engine) -> dict:
    df = pd.read_sql("SELECT * FROM ml.business_kpis", engine)
    if df.empty:
        raise ValueError("ml.business_kpis table is empty.")
    return df.iloc[0].to_dict()


def load_store_recommendations(engine) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM ml.store_recommendations", engine)


def load_product_recommendations(engine) -> pd.DataFrame:
    return pd.read_sql(
        "SELECT * FROM ml.product_recommendations ORDER BY high_risk_pct DESC",
        engine
    )


def load_category_summary(engine) -> pd.DataFrame:
    return pd.read_sql(
        "SELECT * FROM ml.category_summary ORDER BY urgent_reorders DESC",
        engine
    )


def load_top20_recommendations(engine) -> pd.DataFrame:
    return pd.read_sql(
        "SELECT * FROM ml.dashboard_top20_products ORDER BY predicted_sales DESC",
        engine
    )


def load_forecast_recommendations(
    engine,
    store_id=None,
    product_id=None,
    risk_levels=None,
    priorities=None,
    department_id=None,
    latest_only: bool = False,
    sort_by: str = "recommended_reorder_qty",
    limit: int = 500
) -> pd.DataFrame:
    conditions = []
    params = {}
    if latest_only:
        conditions.append("r.dt = '2024-06-24'")
    if store_id is not None:
        conditions.append("r.store_id = :store_id")
        params["store_id"] = store_id
    if product_id is not None:
        conditions.append("r.product_id = :product_id")
        params["product_id"] = product_id
    if risk_levels:
        conditions.append("r.stockout_risk = ANY(:risks)")
        params["risks"] = risk_levels
    if priorities:
        conditions.append("r.replenishment_priority = ANY(:priorities)")
        params["priorities"] = priorities
    if department_id is not None:
        conditions.append("p.management_group_id = :dept_id")
        params["dept_id"] = department_id

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    if sort_by == "predicted_sales":
        order_clause = "r.predicted_sales DESC"
    elif sort_by == "stockout_risk":
        order_clause = "CASE r.stockout_risk WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END ASC, r.recommended_reorder_qty DESC"
    else:
        order_clause = "r.recommended_reorder_qty DESC"

    sql = f"""
        SELECT r.store_id, r.product_id, r.dt, r.actual_sales, r.predicted_sales,
               r.stockout_risk, r.replenishment_priority, r.recommended_reorder_qty,
               r.risk_explanation, COALESCE(p.management_group_id, 6) AS management_group_id
        FROM ml.forecast_recommendations r
        LEFT JOIN core.dim_product p ON r.product_id = p.product_id
        {where}
        ORDER BY {order_clause}
        LIMIT {limit}
    """
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


def load_risk_summary_counts(engine, store_id: int = None, department_id: int = None) -> dict:
    """Load latest risk summary counts (High, Medium, Low) across the network or filtered by store/department."""
    conditions = ["r.dt = '2024-06-24'"]
    params = {}
    if store_id is not None:
        conditions.append("r.store_id = :store_id")
        params["store_id"] = store_id
    if department_id is not None:
        conditions.append("p.management_group_id = :dept_id")
        params["dept_id"] = department_id

    where = "WHERE " + " AND ".join(conditions)
    join = "LEFT JOIN core.dim_product p ON r.product_id = p.product_id" if department_id is not None else ""
    sql = text(f"""
        SELECT r.stockout_risk, COUNT(1) AS cnt
        FROM ml.forecast_recommendations r
        {join}
        {where}
        GROUP BY r.stockout_risk
    """)
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "TOTAL": 0}
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params=params)
        for _, row in df.iterrows():
            k = str(row["stockout_risk"]).upper()
            c = int(row["cnt"])
            counts[k] = c
            counts["TOTAL"] += c
    return counts


def load_store_product_forecast(engine, store_id: int, product_id: int) -> pd.DataFrame:
    """Load daily actual vs forecasted sales and diagnosis for a specific store and product."""
    sql = text("""
        SELECT dt, actual_sales, predicted_sales, stockout_risk, replenishment_priority, recommended_reorder_qty, risk_explanation
        FROM ml.forecast_recommendations
        WHERE store_id = :store_id AND product_id = :product_id
        ORDER BY dt
    """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"store_id": store_id, "product_id": product_id})


def load_daily_sales_trend(engine) -> pd.DataFrame:
    """Aggregate daily sales and stockout rate across all stores."""
    try:
        with engine.connect() as conn:
            exists = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'core' AND table_name = 'daily_sales_trend'
            """)).scalar()
            if exists:
                return pd.read_sql(
                    "SELECT dt, total_sales, observations, stockout_rate_pct FROM core.daily_sales_trend ORDER BY dt",
                    conn
                )
            else:
                return pd.read_sql("""
                    SELECT
                        dt,
                        ROUND(SUM(sale_amount)::numeric, 2)     AS total_sales,
                        COUNT(*)                                  AS observations,
                        ROUND(100.0 * SUM(CASE WHEN stockout_flag THEN 1 ELSE 0 END)
                              / COUNT(*), 2)                     AS stockout_rate_pct
                    FROM core.fact_daily_sales
                    GROUP BY dt
                    ORDER BY dt
                """, conn)
    except Exception:
        return pd.read_sql("""
            SELECT
                dt,
                ROUND(SUM(sale_amount)::numeric, 2)     AS total_sales,
                COUNT(*)                                  AS observations,
                ROUND(100.0 * SUM(CASE WHEN stockout_flag THEN 1 ELSE 0 END)
                      / COUNT(*), 2)                     AS stockout_rate_pct
            FROM core.fact_daily_sales
            GROUP BY dt
            ORDER BY dt
        """, engine)


# ──────────────────────────────────────────────────────────────
# Instacart / Customer Behavior Layer
# ──────────────────────────────────────────────────────────────

def instacart_available(engine) -> bool:
    """Return True if the instacart schema and key tables exist."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'instacart'
                AND table_name = 'products'
            """))
            return result.scalar() > 0
    except Exception:
        return False


def load_instacart_kpis(engine) -> dict:
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM instacart.products)         AS total_products,
                (SELECT COUNT(DISTINCT user_id) FROM instacart.orders) AS total_users,
                (SELECT COUNT(*) FROM instacart.orders)           AS total_orders,
                (SELECT COUNT(*) FROM instacart.order_products_prior
                 WHERE reordered = 1)::float /
                NULLIF((SELECT COUNT(*) FROM instacart.order_products_prior), 0) * 100
                                                                  AS overall_reorder_rate,
                (SELECT COUNT(*) FROM ml.market_basket_rules)     AS total_basket_rules
        """)).fetchone()
    return {
        "total_products":       r[0],
        "total_users":          r[1],
        "total_orders":         r[2],
        "overall_reorder_rate": round(r[3], 2) if r[3] else 0,
        "total_basket_rules":   r[4],
    }


def load_top_products(engine, n: int = 20) -> pd.DataFrame:
    return pd.read_sql(f"""
        SELECT product_id, product_name, department, aisle,
               purchase_count, reorder_rate_pct, reorder_signal, popularity_rank
        FROM ml.product_reorder_behavior
        ORDER BY purchase_count DESC
        LIMIT {n}
    """, engine)


def load_top_reorder_products(engine, n: int = 20, min_purchases: int = 1000) -> pd.DataFrame:
    return pd.read_sql(f"""
        SELECT product_id, product_name, department, aisle,
               purchase_count, reorder_rate_pct, reorder_signal
        FROM ml.product_reorder_behavior
        WHERE purchase_count >= {min_purchases}
        ORDER BY reorder_rate_pct DESC
        LIMIT {n}
    """, engine)


def load_department_summary(engine) -> pd.DataFrame:
    return pd.read_sql("""
        SELECT department,
               COUNT(*)                            AS product_count,
               SUM(purchase_count)                 AS total_purchases,
               ROUND(AVG(reorder_rate_pct)::numeric, 2) AS avg_reorder_rate
        FROM ml.product_reorder_behavior
        GROUP BY department
        ORDER BY total_purchases DESC
    """, engine)


def load_aisle_summary(engine, top_n: int = 20) -> pd.DataFrame:
    return pd.read_sql(f"""
        SELECT aisle,
               COUNT(*)                             AS product_count,
               SUM(purchase_count)                  AS total_purchases,
               ROUND(AVG(reorder_rate_pct)::numeric, 2) AS avg_reorder_rate
        FROM ml.product_reorder_behavior
        GROUP BY aisle
        ORDER BY total_purchases DESC
        LIMIT {top_n}
    """, engine)


def load_basket_rules(engine, min_lift: float = 1.5, n: int = 50) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text("""
            SELECT antecedent_product, consequent_product,
                   support, confidence, lift
            FROM ml.market_basket_rules
            WHERE lift >= :min_lift
            ORDER BY lift DESC
            LIMIT :n
        """), conn, params={"min_lift": min_lift, "n": n})


def load_product_associations(engine, product_name: str) -> pd.DataFrame:
    """Return products frequently bought with the given product."""
    with engine.connect() as conn:
        return pd.read_sql(text("""
            SELECT consequent_product AS associated_product,
                   confidence, lift, support
            FROM ml.market_basket_rules
            WHERE LOWER(antecedent_product) = LOWER(:name)
            ORDER BY lift DESC
            LIMIT 10
        """), conn, params={"name": product_name})


# ──────────────────────────────────────────────────────────────
# Cross-Dataset Intelligence Layer
# ──────────────────────────────────────────────────────────────

def load_unified_intelligence(engine, risk_level: str = None, n: int = 100) -> pd.DataFrame:
    sql = """
        SELECT product_id, high_risk_pct, inventory_risk_level,
               replenishment_priority, avg_reorder_qty,
               predicted_sales, urgent_reorders,
               instacart_reorder_signal, instacart_dept_reorder_rate,
               business_recommendation, integration_note
        FROM analytics.unified_product_intelligence
        {where}
        ORDER BY high_risk_pct DESC
        LIMIT {n}
    """
    where = ""
    params = {}
    if risk_level:
        where = "WHERE inventory_risk_level = :risk"
        params["risk"] = risk_level

    with engine.connect() as conn:
        return pd.read_sql(text(sql.format(where=where, n=n)), conn, params=params)


# ──────────────────────────────────────────────────────────────
# Home Page — single bundled loader
# ──────────────────────────────────────────────────────────────

def load_home_overview(engine) -> dict:
    """
    Load everything the Home page needs in one call.
    Returns a dict with keys: kpi, products, stores, urgent_actions, queried_at.
    """
    from datetime import datetime

    kpi = load_business_kpis(engine)
    products = load_product_recommendations(engine)
    stores   = load_store_recommendations(engine)

    # Top 10 urgent actions: HIGH risk + HIGH priority, ordered by reorder qty
    urgent_sql = text("""
        SELECT store_id, product_id,
               ROUND(predicted_sales::numeric, 2)          AS expected_demand,
               ROUND(recommended_reorder_qty::numeric, 0)  AS recommended_reorder,
               stockout_risk,
               replenishment_priority,
               risk_explanation
        FROM ml.forecast_recommendations
        WHERE stockout_risk = 'HIGH'
          AND replenishment_priority = 'HIGH'
        ORDER BY recommended_reorder_qty DESC
        LIMIT 10
    """)
    with engine.connect() as conn:
        urgent = pd.read_sql(urgent_sql, conn)

    return {
        "kpi":            kpi,
        "products":       products,
        "stores":         stores,
        "urgent_actions": urgent,
        "queried_at":     datetime.now(),
    }


# ──────────────────────────────────────────────────────────────
# Operational Inventory Updates Layer
# ──────────────────────────────────────────────────────────────

def load_stores_catalog(engine) -> pd.DataFrame:
    """Return all valid store IDs and city mappings from core.dim_store."""
    return pd.read_sql("""
        SELECT store_id, city_id
        FROM core.dim_store
        ORDER BY store_id ASC
    """, engine)


def load_products_catalog(engine) -> pd.DataFrame:
    """Return all valid product IDs and management groups from core.dim_product."""
    return pd.read_sql("""
        SELECT product_id, management_group_id, first_category_id
        FROM core.dim_product
        ORDER BY product_id ASC
    """, engine)


def check_inventory_update_exists(engine, dt, store_id: int, product_id: int) -> bool:
    """Check if an operational update record already exists for the given date, store, and product."""
    with engine.connect() as conn:
        cnt = conn.execute(text("""
            SELECT COUNT(*) FROM app.inventory_updates
            WHERE dt = :dt AND store_id = :store_id AND product_id = :product_id
        """), {"dt": dt, "store_id": int(store_id), "product_id": int(product_id)}).scalar()
        return bool(cnt and cnt > 0)


def save_inventory_update(
    engine,
    dt,
    store_id: int,
    product_id: int,
    sale_amount: float,
    stock_status: str,
    discount: float = 0.0,
    holiday_flag: int = 0,
    activity_flag: int = 0,
    notes: str = ""
) -> dict:
    """
    Validate and save operational inventory update into app.inventory_updates.
    Uses UPSERT (ON CONFLICT DO UPDATE) so managers can update an existing daily record.
    Returns dict: {'success': bool, 'is_new': bool, 'message': str, 'update_id': int | None}
    """
    if dt is None:
        return {"success": False, "is_new": False, "message": "Reporting date is required.", "update_id": None}

    from datetime import date as _date, datetime as _datetime
    parsed_dt = dt
    if isinstance(parsed_dt, str):
        try:
            parsed_dt = _datetime.strptime(parsed_dt, "%Y-%m-%d").date()
        except Exception:
            pass
    elif hasattr(parsed_dt, "date") and not isinstance(parsed_dt, _date):
        parsed_dt = parsed_dt.date()

    if isinstance(parsed_dt, _date) and parsed_dt > _date.today():
        return {"success": False, "is_new": False, "message": "Reporting date cannot be in the future.", "update_id": None}

    try:
        store_id = int(store_id)
        product_id = int(product_id)
    except (ValueError, TypeError):
        return {"success": False, "is_new": False, "message": "Store ID and Product SKU must be valid integers.", "update_id": None}

    try:
        sale_amount = float(sale_amount)
    except (ValueError, TypeError):
        return {"success": False, "is_new": False, "message": "Sales quantity must be a valid number.", "update_id": None}

    if sale_amount < 0:
        return {"success": False, "is_new": False, "message": "Daily sales quantity cannot be negative.", "update_id": None}

    valid_statuses = ["In Stock", "Low Stock", "Out of Stock"]
    if stock_status not in valid_statuses:
        return {"success": False, "is_new": False, "message": f"Stock status must be one of: {', '.join(valid_statuses)}.", "update_id": None}

    try:
        discount = float(discount)
    except (ValueError, TypeError):
        return {"success": False, "is_new": False, "message": "Discount must be a valid number.", "update_id": None}

    if discount < 0.0 or discount > 100.0:
        return {"success": False, "is_new": False, "message": "Discount percentage must be between 0% and 100%.", "update_id": None}

    holiday_val = 1 if holiday_flag in [1, True, "1", "Yes"] else 0
    activity_val = 1 if activity_flag in [1, True, "1", "Yes"] else 0
    notes_clean = (notes or "").strip()[:500]

    upsert_sql = text("""
        INSERT INTO app.inventory_updates (
            dt, store_id, product_id, sale_amount, stock_status, discount, holiday_flag, activity_flag, notes, updated_at
        ) VALUES (
            :dt, :store_id, :product_id, :sale_amount, :stock_status, :discount, :holiday, :activity, :notes, CURRENT_TIMESTAMP
        )
        ON CONFLICT (dt, store_id, product_id) DO UPDATE SET
            sale_amount = EXCLUDED.sale_amount,
            stock_status = EXCLUDED.stock_status,
            discount = EXCLUDED.discount,
            holiday_flag = EXCLUDED.holiday_flag,
            activity_flag = EXCLUDED.activity_flag,
            notes = EXCLUDED.notes,
            updated_at = CURRENT_TIMESTAMP
        RETURNING update_id, (xmax = 0) AS is_inserted;
    """)

    try:
        with engine.begin() as conn:
            result = conn.execute(upsert_sql, {
                "dt": dt,
                "store_id": store_id,
                "product_id": product_id,
                "sale_amount": round(sale_amount, 2),
                "stock_status": stock_status,
                "discount": round(discount, 2),
                "holiday": holiday_val,
                "activity": activity_val,
                "notes": notes_clean if notes_clean else None,
            }).fetchone()

            update_id = result[0]
            is_new = bool(result[1])
            verb = "recorded" if is_new else "updated"
            return {
                "success": True,
                "is_new": is_new,
                "message": f"Inventory record successfully {verb} (ID #{update_id}) for Store {store_id}, Stock Keeping Unit (SKU) {product_id}.",
                "update_id": update_id
            }
    except Exception as e:
        err_msg = str(e)
        if "foreign key" in err_msg.lower():
            user_msg = "Selected Store ID or Product SKU does not exist in the database catalog."
        elif "check constraint" in err_msg.lower():
            user_msg = "Submitted values violate operational data constraints."
        else:
            user_msg = "Could not save the record. Please check the database connection."
        return {"success": False, "is_new": False, "message": user_msg, "update_id": None}


def load_recent_inventory_updates(engine, limit: int = 10) -> pd.DataFrame:
    """Fetch the latest operational records submitted by managers."""
    sql = text("""
        SELECT
            u.update_id,
            u.dt,
            u.store_id,
            s.city_id,
            u.product_id,
            p.management_group_id,
            u.sale_amount,
            u.stock_status,
            u.discount,
            u.holiday_flag,
            u.activity_flag,
            u.notes,
            u.created_at,
            u.updated_at
        FROM app.inventory_updates u
        LEFT JOIN core.dim_store s ON u.store_id = s.store_id
        LEFT JOIN core.dim_product p ON u.product_id = p.product_id
        ORDER BY COALESCE(u.updated_at, u.created_at) DESC, u.update_id DESC
        LIMIT :limit
    """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"limit": limit})


def load_inventory_update_summary(engine) -> dict:
    """Return aggregate KPIs for operational inventory updates."""
    sql = text("""
        SELECT
            COUNT(*) AS total_records,
            COUNT(DISTINCT store_id) AS stores_covered,
            COUNT(DISTINCT product_id) AS products_covered,
            COALESCE(SUM(sale_amount), 0) AS total_sales_recorded,
            COUNT(*) FILTER (WHERE stock_status = 'Out of Stock') AS out_of_stock_count,
            COUNT(*) FILTER (WHERE stock_status = 'Low Stock') AS low_stock_count,
            COUNT(*) FILTER (WHERE stock_status = 'In Stock') AS in_stock_count
        FROM app.inventory_updates
    """)
    with engine.connect() as conn:
        row = conn.execute(sql).fetchone()
        if not row:
            return {
                "total_records": 0, "stores_covered": 0, "products_covered": 0,
                "total_sales_recorded": 0.0, "out_of_stock_count": 0,
                "low_stock_count": 0, "in_stock_count": 0
            }
        return {
            "total_records": int(row[0] or 0),
            "stores_covered": int(row[1] or 0),
            "products_covered": int(row[2] or 0),
            "total_sales_recorded": float(row[3] or 0.0),
            "out_of_stock_count": int(row[4] or 0),
            "low_stock_count": int(row[5] or 0),
            "in_stock_count": int(row[6] or 0),
        }


# ──────────────────────────────────────────────────────────────
# Operational Decisions & Actions Layer
# ──────────────────────────────────────────────────────────────

def save_replenishment_decision(
    engine,
    store_id: int,
    product_id: int,
    recommended_qty: float,
    approved_qty: float,
    decision_status: str = "APPROVED",
    notes: str = "",
    decided_by: str = "Store Operations",
    decision_date=None
) -> dict:
    """
    Save or update manager replenishment decision in app.replenishment_decisions.
    decision_status must be one of: 'APPROVED', 'MODIFIED', 'DEFERRED'
    """
    from datetime import date
    if decision_date is None:
        decision_date = date.today()

    try:
        store_id = int(store_id)
        product_id = int(product_id)
        recommended_qty = max(0.0, float(recommended_qty))
        approved_qty = max(0.0, float(approved_qty))
    except (ValueError, TypeError):
        return {"success": False, "message": "Invalid store ID, product ID, or quantity.", "decision_id": None}

    valid_statuses = ["APPROVED", "MODIFIED", "REJECTED", "DEFERRED"]
    decision_status = decision_status.strip().upper()
    if decision_status not in valid_statuses:
        return {"success": False, "message": f"Status must be one of: {', '.join(valid_statuses)}.", "decision_id": None}

    notes_clean = (notes or "").strip()[:500]

    upsert_sql = text("""
        INSERT INTO app.replenishment_decisions (
            store_id, product_id, decision_date, recommended_qty, approved_qty,
            decision_status, decision_notes, decided_by, updated_at
        ) VALUES (
            :store_id, :product_id, :decision_date, :recommended_qty, :approved_qty,
            :decision_status, :decision_notes, :decided_by, CURRENT_TIMESTAMP
        )
        ON CONFLICT (decision_date, store_id, product_id) DO UPDATE SET
            approved_qty = EXCLUDED.approved_qty,
            decision_status = EXCLUDED.decision_status,
            decision_notes = EXCLUDED.decision_notes,
            decided_by = EXCLUDED.decided_by,
            updated_at = CURRENT_TIMESTAMP
        RETURNING decision_id, (xmax = 0) AS is_inserted;
    """)

    try:
        with engine.begin() as conn:
            result = conn.execute(upsert_sql, {
                "store_id": store_id,
                "product_id": product_id,
                "decision_date": decision_date,
                "recommended_qty": round(recommended_qty, 2),
                "approved_qty": round(approved_qty, 2),
                "decision_status": decision_status,
                "decision_notes": notes_clean if notes_clean else None,
                "decided_by": decided_by.strip() or "Store Operations"
            }).fetchone()

            decision_id = result[0]
            is_new = bool(result[1])
            verb = "recorded" if is_new else "updated"
            return {
                "success": True,
                "is_new": is_new,
                "message": f"Replenishment decision successfully {verb} (ID #{decision_id}) for Store {store_id}, SKU {product_id} [{decision_status}: {approved_qty:,.0f} units].",
                "decision_id": decision_id
            }
    except Exception as e:
        return {"success": False, "message": f"Database operation failed: {e}", "decision_id": None}


def load_recent_replenishment_decisions(
    engine,
    limit: int = 100,
    store_id: int = None,
    product_id: int = None,
    decision_status: str = None,
    days: int = None,
    sort_asc: bool = False
) -> pd.DataFrame:
    """Fetch manager replenishment decisions with catalog dimensions and optional filters."""
    conditions = ["1=1"]
    params = {"limit": limit}

    if store_id is not None:
        conditions.append("d.store_id = :store_id")
        params["store_id"] = int(store_id)

    if product_id is not None:
        conditions.append("d.product_id = :product_id")
        params["product_id"] = int(product_id)

    if decision_status and str(decision_status).strip() and str(decision_status).strip().upper() not in ["ALL", "ALL DECISIONS"]:
        conditions.append("d.decision_status = :decision_status")
        params["decision_status"] = str(decision_status).strip().upper()

    if days is not None:
        if days == 0:
            conditions.append("d.decision_date = CURRENT_DATE")
        else:
            conditions.append("d.decision_date >= CURRENT_DATE - (:days * INTERVAL '1 day')")
            params["days"] = int(days)

    where_clause = " AND ".join(conditions)
    sort_dir = "ASC" if sort_asc else "DESC"

    sql = text(f"""
        SELECT
            d.decision_id,
            d.decision_date,
            d.store_id,
            s.city_id,
            d.product_id,
            p.management_group_id,
            d.recommended_qty,
            d.approved_qty,
            d.decision_status,
            d.decision_notes,
            d.decided_by,
            d.created_at,
            d.updated_at
        FROM app.replenishment_decisions d
        LEFT JOIN core.dim_store s ON d.store_id = s.store_id
        LEFT JOIN core.dim_product p ON d.product_id = p.product_id
        WHERE {where_clause}
        ORDER BY d.updated_at {sort_dir}, d.decision_id {sort_dir}
        LIMIT :limit
    """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=params)


def load_decided_stores_and_products(engine) -> tuple[list[int], list[int]]:
    """Return sorted lists of distinct store_ids and product_ids present in replenishment decisions."""
    try:
        sql_s = text("SELECT DISTINCT store_id FROM app.replenishment_decisions ORDER BY store_id")
        sql_p = text("SELECT DISTINCT product_id FROM app.replenishment_decisions ORDER BY product_id")
        with engine.connect() as conn:
            stores = [int(r[0]) for r in conn.execute(sql_s).fetchall()]
            products = [int(r[0]) for r in conn.execute(sql_p).fetchall()]
        return stores, products
    except Exception:
        return [], []


def load_replenishment_decision_summary(engine) -> dict:
    """Return aggregate statistics for replenishment decisions."""
    sql = text("""
        SELECT
            COUNT(*) AS total_decisions,
            COUNT(*) FILTER (WHERE decision_status = 'APPROVED') AS approved_count,
            COUNT(*) FILTER (WHERE decision_status = 'MODIFIED') AS modified_count,
            COUNT(*) FILTER (WHERE decision_status = 'REJECTED') AS rejected_count,
            COUNT(*) FILTER (WHERE decision_status = 'DEFERRED') AS deferred_count,
            COALESCE(SUM(approved_qty), 0) AS total_approved_units,
            COUNT(DISTINCT store_id) AS stores_covered,
            COUNT(DISTINCT product_id) AS products_covered
        FROM app.replenishment_decisions
    """)
    with engine.connect() as conn:
        row = conn.execute(sql).fetchone()
        if not row:
            return {
                "total_decisions": 0, "approved_count": 0, "modified_count": 0,
                "rejected_count": 0, "deferred_count": 0, "total_approved_units": 0.0,
                "stores_covered": 0, "products_covered": 0
            }
        return {
            "total_decisions": int(row[0] or 0),
            "approved_count": int(row[1] or 0),
            "modified_count": int(row[2] or 0),
            "rejected_count": int(row[3] or 0),
            "deferred_count": int(row[4] or 0),
            "total_approved_units": float(row[5] or 0.0),
            "stores_covered": int(row[6] or 0),
            "products_covered": int(row[7] or 0),
        }


def load_today_decisions(engine) -> dict:
    """Fetch user replenishment decisions made today, keyed by (store_id, product_id)."""
    sql = text("""
        SELECT store_id, product_id, decision_status, recommended_qty, approved_qty, decision_notes, updated_at
        FROM app.replenishment_decisions
        WHERE decision_date = CURRENT_DATE
    """)
    lookup = {}
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)
        for _, r in df.iterrows():
            lookup[(int(r['store_id']), int(r['product_id']))] = {
                "status": str(r['decision_status']).upper(),
                "recommended_qty": float(r['recommended_qty']),
                "approved_qty": float(r['approved_qty']),
                "notes": str(r['decision_notes'] or ""),
                "updated_at": r['updated_at']
            }
    return lookup


def save_alert_action(
    engine,
    store_id: int,
    product_id: int,
    alert_severity: str,
    action_status: str = "REVIEWED",
    notes: str = ""
) -> dict:
    """
    Record or update operational status of an inventory exception alert.
    action_status must be one of: 'OPEN', 'REVIEWED', 'ACKNOWLEDGED', 'RESOLVED'
    """
    valid_statuses = ["OPEN", "REVIEWED", "ACKNOWLEDGED", "RESOLVED"]
    action_status = action_status.strip().upper()
    if action_status not in valid_statuses:
        return {"success": False, "message": f"Status must be one of: {', '.join(valid_statuses)}."}

    sql = text("""
        INSERT INTO app.alert_actions (
            store_id, product_id, alert_severity, action_status, resolution_notes, updated_at
        ) VALUES (
            :store_id, :product_id, :alert_severity, :action_status, :notes, CURRENT_TIMESTAMP
        )
        ON CONFLICT (store_id, product_id) DO UPDATE SET
            alert_severity = EXCLUDED.alert_severity,
            action_status = EXCLUDED.action_status,
            resolution_notes = EXCLUDED.resolution_notes,
            updated_at = CURRENT_TIMESTAMP
        RETURNING action_id;
    """)

    try:
        with engine.begin() as conn:
            result = conn.execute(sql, {
                "store_id": int(store_id),
                "product_id": int(product_id),
                "alert_severity": alert_severity,
                "action_status": action_status,
                "notes": (notes or "").strip()[:500] or None
            }).fetchone()
            return {"success": True, "action_id": result[0], "message": f"Alert status updated to {action_status} for Store {store_id}, SKU {product_id}."}
    except Exception as e:
        return {"success": False, "action_id": None, "message": f"Failed to record alert action: {e}"}


def load_alert_actions(engine) -> pd.DataFrame:
    """Fetch tracked exception alert actions."""
    sql = text("""
        SELECT action_id, store_id, product_id, alert_severity, action_status, resolution_notes, updated_at
        FROM app.alert_actions
        ORDER BY updated_at DESC
    """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)


def load_actionable_alerts(
    engine,
    status: str = None,
    risk_level: str = None,
    priority: str = None,
    store_id: int = None,
    product_id: int = None,
    limit: int = 200
) -> pd.DataFrame:
    """Fetch actionable alerts from ml.forecast_recommendations joined with app.alert_actions."""
    conditions = []
    params = {"limit": limit}

    if risk_level and risk_level.upper() in ["HIGH", "MEDIUM", "LOW"]:
        conditions.append("r.stockout_risk = :risk_level")
        params["risk_level"] = risk_level.upper()
    else:
        conditions.append("r.stockout_risk IN ('HIGH', 'MEDIUM')")

    if status and status.upper() not in ["ALL", "ALL STATUSES"]:
        st_upper = status.upper()
        if st_upper == "OPEN":
            conditions.append("COALESCE(a.action_status, 'OPEN') = 'OPEN'")
        elif st_upper in ["REVIEWED", "ACKNOWLEDGED"]:
            conditions.append("COALESCE(a.action_status, 'OPEN') IN ('REVIEWED', 'ACKNOWLEDGED')")
        elif st_upper == "RESOLVED":
            conditions.append("COALESCE(a.action_status, 'OPEN') = 'RESOLVED'")

    if priority and priority.upper() not in ["ALL", "ALL PRIORITIES"]:
        pri_map = {
            "URGENT": "HIGH", "MONITOR": "MEDIUM", "NORMAL": "LOW",
            "HIGH": "HIGH", "MEDIUM": "MEDIUM", "LOW": "LOW"
        }
        matched_pri = pri_map.get(priority.upper())
        if matched_pri:
            conditions.append("r.replenishment_priority = :priority")
            params["priority"] = matched_pri

    if store_id is not None:
        conditions.append("r.store_id = :store_id")
        params["store_id"] = int(store_id)

    if product_id is not None:
        conditions.append("r.product_id = :product_id")
        params["product_id"] = int(product_id)

    where_clause = " AND ".join(conditions)

    sql = text(f"""
        SELECT
            r.dt,
            r.store_id,
            r.product_id,
            r.actual_sales,
            r.predicted_sales,
            r.stockout_risk,
            r.replenishment_priority,
            r.recommended_reorder_qty,
            r.risk_explanation,
            COALESCE(a.action_status, 'OPEN') AS action_status,
            a.resolution_notes,
            a.updated_at AS action_updated_at
        FROM ml.forecast_recommendations r
        LEFT JOIN app.alert_actions a ON r.store_id = a.store_id AND r.product_id = a.product_id
        WHERE {where_clause}
        ORDER BY
            CASE WHEN COALESCE(a.action_status, 'OPEN') = 'OPEN' THEN 1
                 WHEN COALESCE(a.action_status, 'OPEN') IN ('REVIEWED', 'ACKNOWLEDGED') THEN 2
                 ELSE 3 END ASC,
            CASE r.stockout_risk WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END ASC,
            r.recommended_reorder_qty DESC,
            r.dt DESC,
            r.store_id ASC,
            r.product_id ASC
        LIMIT :limit;
    """)

    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=params)


def load_alerts_summary(engine) -> dict:
    """Return summary KPI metrics for the Alerts page calculated from real database records."""
    try:
        with engine.connect() as conn:
            kpi_row = conn.execute(text("""
                SELECT high_risk_products, medium_risk_products
                FROM ml.business_kpis
                LIMIT 1;
            """)).fetchone()
            high_cnt = int(kpi_row[0]) if kpi_row else 0
            med_cnt = int(kpi_row[1]) if kpi_row else 0

            resolved_cnt = conn.execute(text("""
                SELECT COUNT(*)
                FROM app.alert_actions
                WHERE action_status = 'RESOLVED';
            """)).scalar() or 0

            reviewed_cnt = conn.execute(text("""
                SELECT COUNT(*)
                FROM app.alert_actions
                WHERE action_status IN ('REVIEWED', 'ACKNOWLEDGED');
            """)).scalar() or 0

            open_cnt = max(0, (high_cnt + med_cnt) - resolved_cnt - reviewed_cnt)

            return {
                "open_alerts": open_cnt,
                "high_risk": high_cnt,
                "medium_risk": med_cnt,
                "resolved": resolved_cnt,
                "reviewed": reviewed_cnt
            }
    except Exception:
        return {
            "open_alerts": 0,
            "high_risk": 0,
            "medium_risk": 0,
            "resolved": 0,
            "reviewed": 0
        }


def load_product_forecast_trend(engine, product_id: int) -> pd.DataFrame:
    """Aggregate daily actual sales and forecasted demand for a specific product across all stores."""
    sql = text("""
        SELECT dt,
               ROUND(SUM(actual_sales)::numeric, 1) AS actual_sales,
               ROUND(SUM(predicted_sales)::numeric, 1) AS predicted_sales,
               ROUND(SUM(recommended_reorder_qty)::numeric, 0) AS recommended_reorder_qty
        FROM ml.forecast_recommendations
        WHERE product_id = :product_id
        GROUP BY dt
        ORDER BY dt
    """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"product_id": int(product_id)})


def load_stores_for_product(engine, product_id: int) -> list:
    """Get sorted list of active store IDs carrying a specific product."""
    sql = text("""
        SELECT DISTINCT store_id
        FROM ml.forecast_recommendations
        WHERE product_id = :product_id
        ORDER BY store_id
    """)
    with engine.connect() as conn:
        res = pd.read_sql(sql, conn, params={"product_id": int(product_id)})
        return [int(s) for s in res["store_id"].tolist()]


def load_store_forecast_trend(engine, store_id: int) -> pd.DataFrame:
    """Aggregate daily actual sales and predicted demand for a specific store."""
    sql = text("""
        SELECT dt,
               ROUND(SUM(actual_sales)::numeric, 1) AS actual_sales,
               ROUND(SUM(predicted_sales)::numeric, 1) AS predicted_sales,
               ROUND(SUM(recommended_reorder_qty)::numeric, 0) AS recommended_reorder_qty
        FROM ml.forecast_recommendations
        WHERE store_id = :store_id
        GROUP BY dt
        ORDER BY dt
    """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"store_id": int(store_id)})



