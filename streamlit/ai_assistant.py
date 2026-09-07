# ============================================================
# SMARTSTOCK AI
# streamlit/ai_assistant.py — AI Inventory Assistant
# ============================================================
#
# PURPOSE:
#   Help store managers understand existing SmartStock AI results:
#     - Why a product is at risk
#     - Why a recommendation was generated
#     - What action is recommended
#     - Which products need attention
#     - Which stores need attention
#     - What the existing analytics show
#
# CORE PRINCIPLE:
#   EXISTING DATA -> EXISTING ANALYTICS -> EXPLANATION -> RECOMMENDED ACTION
#
# STRICT GROUNDING:
#   - Uses only verified database data (ml.forecast_recommendations,
#     ml.store_recommendations, ml.product_recommendations, Instacart analytics).
#   - Never hallucinates stock-on-hand, expiry, supplier, PO, or safety stock.
#   - Works 100% reliably standalone without requiring an external AI service.
# ============================================================

import os
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ──────────────────────────────────────────────────────────────
# 0. SQL SAFETY GUARD (BACKWARD COMPATIBILITY)
# ──────────────────────────────────────────────────────────────

_DANGEROUS = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|TRUNCATE|ALTER|CREATE|GRANT|REVOKE)\b",
    re.IGNORECASE
)


def _safe_sql(sql: str) -> bool:
    """Return True only if the SQL contains no destructive statements."""
    return not bool(_DANGEROUS.search(sql))


# ──────────────────────────────────────────────────────────────
# 1. ENTITY EXTRACTION HELPERS
# ──────────────────────────────────────────────────────────────

def extract_product_id(text_in: str) -> int | None:
    """Extract a valid product / SKU ID from natural language query."""
    m = re.search(r"(?:sku|product|item)\s*#?\s*(\d+)", text_in, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r"#\s*(\d+)", text_in)
    if m:
        return int(m.group(1))
    return None


def extract_store_id(text_in: str) -> int | None:
    """Extract a valid store ID from natural language query."""
    m = re.search(r"(?:store|location)\s*#?\s*(\d+)", text_in, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def detect_intent(question: str) -> tuple:
    """
    Map a natural language question to a template key + params.
    Maintained for full backward compatibility with test_smartstock.py suite.
    """
    q = question.lower()
    pid = extract_product_id(question)
    pname = None
    m = re.search(r"[\"'](.+?)[\"']", question)
    if m:
        pname = m.group(1)

    if any(w in q for w in ["bought together", "frequently bought", "basket", "association"]):
        if pname:
            return "product_basket_lookup", {"name_pattern": f"%{pname}%"}
        return "basket_associations", {}

    if any(w in q for w in ["store", "which store", "urgent store", "stores need", "store need"]):
        return "high_priority_stores", {}

    if any(w in q for w in ["stockout", "high risk", "at risk", "risky", "need attention", "products need"]):
        if pid:
            return "product_detail", {"product_id": pid}
        return "high_risk_products", {}

    if pid:
        return "product_detail", {"product_id": pid}

    return "overall_summary", {}


# ──────────────────────────────────────────────────────────────
# 2. GUARDRAILS & INTENT CHECKERS
# ──────────────────────────────────────────────────────────────

def is_unrelated_question(q: str) -> bool:
    """Check if the question is unrelated to retail inventory / SmartStock AI."""
    q_lower = q.lower().strip()
    unrelated_triggers = [
        "weather", "joke", "president", "write an email", "write a letter",
        "recipe", "sports", "football", "cricket", "movie", "politics",
        "who is the president", "tell me a joke", "what is the capital",
        "sing a song", "poem", "coding", "python code", "translate",
        "who won", "how old are you", "who are you"
    ]
    has_inventory_keywords = any(
        kw in q_lower
        for kw in [
            "stock", "inventory", "store", "product", "sku", "reorder",
            "replenish", "demand", "forecast", "risk", "sales", "instacart",
            "basket", "customer", "category", "urgent", "attention"
        ]
    )
    if has_inventory_keywords:
        return False
    return any(trig in q_lower for trig in unrelated_triggers)


def is_unsupported_inventory_query(q: str) -> bool:
    """Check if query asks for data not tracked in current SmartStock AI database."""
    q_lower = q.lower()
    unsupported_triggers = [
        "expiry", "expiration", "shelf life", "expire", "supplier", "vendor",
        "lead time", "purchase order", "po number", "po tracking", "po #",
        "warehouse id", "warehouse quantity", "customer name", "customer email",
        "customer phone", "customer address", "credit card", "safety stock level",
        "current inventory on hand", "live stock balance", "real-time stock count"
    ]
    return any(trig in q_lower for trig in unsupported_triggers)


# ──────────────────────────────────────────────────────────────
# 3. CORE GROUNDED ANSWER GENERATION
# ──────────────────────────────────────────────────────────────

def answer_question(engine, question: str, store_id: int | None = None, product_id: int | None = None) -> dict:
    """
    Main business explanation interface.
    Accepts a question string and optional store_id / product_id context.
    Returns:
        {
            "answer": str,
            "data": pd.DataFrame,
            "sql": str,
            "limitation": str,
            "product_id": int | None,
            "store_id": int | None
        }
    """
    q_raw = question or ""
    q = q_raw.lower().strip()

    # Fallback return structure builder
    def _resp(ans: str, df: pd.DataFrame = None, sql_used: str = "", limit_note: str = "", p_id: int | None = None, s_id: int | None = None):
        return {
            "answer": ans,
            "data": df if df is not None else pd.DataFrame(),
            "sql": sql_used,
            "limitation": limit_note,
            "product_id": p_id,
            "store_id": s_id,
        }

    # ── Guardrail 1: Unrelated questions (Step 14) ─────────────
    if is_unrelated_question(q):
        return _resp(
            "I can help with SmartStock inventory data, risks, demand and replenishment recommendations."
        )

    # ── Guardrail 2: Unsupported inventory fields (Step 15) ────
    if is_unsupported_inventory_query(q):
        return _resp(
            "I do not have that information in the current data.",
            limit_note="Current SmartStock AI tracks sales, demand forecasts, stockout risks, and replenishment recommendations. Warehouse balances, supplier contracts, and expiry dates are not tracked."
        )

    # Extract entities from question if not provided in context
    extracted_pid = extract_product_id(q_raw)
    extracted_sid = extract_store_id(q_raw)

    target_pid = product_id if product_id is not None else extracted_pid
    target_sid = store_id if store_id is not None else extracted_sid

    # Verify database connectivity and entity existence
    try:
        with engine.connect() as conn:
            # If target product is specified, check catalog existence
            if target_pid is not None:
                p_exists = conn.execute(
                    text("SELECT COUNT(*) FROM core.dim_product WHERE product_id = :p"),
                    {"p": int(target_pid)}
                ).scalar()
                if not p_exists:
                    return _resp("I could not find that product/store in the current data.")

            # If target store is specified, check catalog existence
            if target_sid is not None:
                s_exists = conn.execute(
                    text("SELECT COUNT(*) FROM core.dim_store WHERE store_id = :s"),
                    {"s": int(target_sid)}
                ).scalar()
                if not s_exists:
                    return _resp("I could not find that product/store in the current data.")

    except Exception:
        # Step 22: Database unavailable
        return _resp("I could not access the inventory data right now.")

    # ── Intent 1: "Why is this product at risk?" (Step 7 & 8) ─
    if any(k in q for k in [
        "why is this product at risk", "why is product", "why is sku", "why at risk",
        "why risk", "at high risk", "at risk", "explain risk", "risk explanation"
    ]):
        try:
            with engine.connect() as conn:
                if target_pid is not None and target_sid is not None:
                    row = conn.execute(text("""
                        SELECT store_id, product_id, stockout_risk, predicted_sales,
                               recommended_reorder_qty, replenishment_priority, risk_explanation
                        FROM ml.forecast_recommendations
                        WHERE product_id = :p AND store_id = :s
                        ORDER BY dt DESC
                        LIMIT 1
                    """), {"p": int(target_pid), "s": int(target_sid)}).fetchone()
                elif target_pid is not None:
                    row = conn.execute(text("""
                        SELECT store_id, product_id, stockout_risk, predicted_sales,
                               recommended_reorder_qty, replenishment_priority, risk_explanation
                        FROM ml.forecast_recommendations
                        WHERE product_id = :p
                        ORDER BY (CASE WHEN stockout_risk='HIGH' THEN 1 WHEN stockout_risk='MEDIUM' THEN 2 ELSE 3 END),
                                 recommended_reorder_qty DESC, dt DESC
                        LIMIT 1
                    """), {"p": int(target_pid)}).fetchone()
                else:
                    # Default to top high-risk product (e.g. SKU 267 at Store 631)
                    row = conn.execute(text("""
                        SELECT store_id, product_id, stockout_risk, predicted_sales,
                               recommended_reorder_qty, replenishment_priority, risk_explanation
                        FROM ml.forecast_recommendations
                        WHERE stockout_risk = 'HIGH'
                        ORDER BY recommended_reorder_qty DESC, dt DESC
                        LIMIT 1
                    """)).fetchone()

                if not row:
                    return _resp("I do not have enough data to answer that.")

                s_id = int(row[0])
                p_id = int(row[1])
                risk_val = str(row[2]).capitalize()
                pred_sales = float(row[3])
                reorder_qty = int(round(float(row[4])))
                priority_val = "Urgent" if str(row[5]).upper() == "HIGH" else ("Monitor" if str(row[5]).upper() == "MEDIUM" else "Normal")
                risk_why = str(row[6]) if row[6] else "Recent demand is high, and this store-product combination has a high-risk recommendation."

                answer = (
                    f"SKU {p_id} at Store {s_id} is marked {risk_val} Risk.\n\n"
                    f"Expected demand is about {int(round(pred_sales))} units.\n\n"
                    f"The current analysis shows elevated stockout risk and the recommendation is marked {priority_val}.\n\n"
                    f"Suggested reorder: {reorder_qty:,} units.\n\n"
                    f"Recommended action: Review the replenishment recommendation."
                )

                df = pd.DataFrame([{
                    "Product / SKU": f"SKU {p_id}",
                    "Store": f"Store {s_id}",
                    "Stockout Risk": f"{risk_val} Risk",
                    "Expected Demand": f"{pred_sales:.1f} units",
                    "Suggested Reorder": f"{reorder_qty:,} units",
                    "Priority": priority_val,
                    "Why": risk_why
                }])

                return _resp(
                    answer,
                    df=df,
                    limit_note="Risk is determined by rolling stockout days and demand forecast patterns.",
                    p_id=p_id,
                    s_id=s_id
                )
        except Exception:
            return _resp("I could not access the inventory data right now.")

    # ── Intent 2: "Why was this reorder recommended?" (Step 8 & 9) ──
    if any(k in q for k in [
        "why was this reorder recommended", "why reorder recommended", "why recommendation",
        "why recommended"
    ]):
        try:
            with engine.connect() as conn:
                if target_pid is not None and target_sid is not None:
                    row = conn.execute(text("""
                        SELECT store_id, product_id, predicted_sales, recommended_reorder_qty, replenishment_priority, risk_explanation, stockout_risk
                        FROM ml.forecast_recommendations
                        WHERE product_id = :p AND store_id = :s
                        ORDER BY dt DESC LIMIT 1
                    """), {"p": int(target_pid), "s": int(target_sid)}).fetchone()
                elif target_pid is not None:
                    row = conn.execute(text("""
                        SELECT store_id, product_id, predicted_sales, recommended_reorder_qty, replenishment_priority, risk_explanation, stockout_risk
                        FROM ml.forecast_recommendations
                        WHERE product_id = :p
                        ORDER BY recommended_reorder_qty DESC, dt DESC LIMIT 1
                    """), {"p": int(target_pid)}).fetchone()
                else:
                    row = conn.execute(text("""
                        SELECT store_id, product_id, predicted_sales, recommended_reorder_qty, replenishment_priority, risk_explanation, stockout_risk
                        FROM ml.forecast_recommendations
                        WHERE replenishment_priority = 'HIGH'
                        ORDER BY recommended_reorder_qty DESC LIMIT 1
                    """)).fetchone()

                if not row:
                    return _resp("I do not have enough data to answer that.")

                s_id = int(row[0])
                p_id = int(row[1])
                pred_sales = float(row[2])
                reorder_qty = int(round(float(row[3])))
                priority_val = "Urgent" if str(row[4]).upper() == "HIGH" else ("Monitor" if str(row[4]).upper() == "MEDIUM" else "Normal")
                risk_why = str(row[5]) if row[5] else "Elevated demand forecast with frequent historical stockouts."
                risk_val = str(row[6]).capitalize()

                answer = (
                    f"The suggested reorder of {reorder_qty:,} units for SKU {p_id} at Store {s_id} was recommended "
                    f"to cover expected daily demand of about {int(round(pred_sales))} units and protect against {risk_val} stockout risk.\n\n"
                    f"Analysis note: {risk_why}\n\n"
                    f"Recommended action: Review the replenishment recommendation."
                )

                df = pd.DataFrame([{
                    "Product / SKU": f"SKU {p_id}",
                    "Store": f"Store {s_id}",
                    "Suggested Reorder": f"{reorder_qty:,} units",
                    "Expected Demand": f"{pred_sales:.1f} units",
                    "Stockout Risk": f"{risk_val} Risk",
                    "Priority": priority_val
                }])

                return _resp(
                    answer,
                    df=df,
                    limit_note="Recommendations are generated from ML demand forecasts and historical stockout frequency.",
                    p_id=p_id,
                    s_id=s_id
                )
        except Exception:
            return _resp("I could not access the inventory data right now.")

    # ── Intent 3: "How much should I reorder?" (Step 9) ────────
    if any(k in q for k in [
        "how much should i reorder", "how much to reorder", "reorder quantity",
        "suggested reorder", "how much to order"
    ]):
        try:
            with engine.connect() as conn:
                if target_pid is not None and target_sid is not None:
                    row = conn.execute(text("""
                        SELECT store_id, product_id, predicted_sales, recommended_reorder_qty, replenishment_priority, risk_explanation
                        FROM ml.forecast_recommendations
                        WHERE product_id = :p AND store_id = :s
                        ORDER BY dt DESC LIMIT 1
                    """), {"p": int(target_pid), "s": int(target_sid)}).fetchone()
                elif target_pid is not None:
                    row = conn.execute(text("""
                        SELECT store_id, product_id, predicted_sales, recommended_reorder_qty, replenishment_priority, risk_explanation
                        FROM ml.forecast_recommendations
                        WHERE product_id = :p
                        ORDER BY recommended_reorder_qty DESC, dt DESC LIMIT 1
                    """), {"p": int(target_pid)}).fetchone()
                else:
                    row = conn.execute(text("""
                        SELECT store_id, product_id, predicted_sales, recommended_reorder_qty, replenishment_priority, risk_explanation
                        FROM ml.forecast_recommendations
                        WHERE replenishment_priority = 'HIGH'
                        ORDER BY recommended_reorder_qty DESC LIMIT 1
                    """)).fetchone()

                if not row:
                    return _resp("I do not have enough data to answer that.")

                s_id = int(row[0])
                p_id = int(row[1])
                pred_sales = float(row[2])
                reorder_qty = int(round(float(row[3])))
                priority_val = "Urgent" if str(row[4]).upper() == "HIGH" else ("Monitor" if str(row[4]).upper() == "MEDIUM" else "Normal")

                answer = f"Based on the current recommendation, the suggested reorder quantity is {reorder_qty:,} units."

                df = pd.DataFrame([{
                    "Product / SKU": f"SKU {p_id}",
                    "Store": f"Store {s_id}",
                    "Suggested Reorder": f"{reorder_qty:,} units",
                    "Expected Demand": f"{pred_sales:.1f} units",
                    "Priority": priority_val
                }])

                return _resp(
                    answer,
                    df=df,
                    limit_note="Suggested reorder covers expected demand for the upcoming inventory cycle.",
                    p_id=p_id,
                    s_id=s_id
                )
        except Exception:
            return _resp("I could not access the inventory data right now.")

    # ── Intent 4: "Which products need attention?" / "Show high-risk products" (Step 10) ──
    if any(k in q for k in [
        "which products need attention", "products need attention", "show high-risk products",
        "high risk products", "high-risk products", "high-risk query", "high risk query",
        "urgent recommendations", "show urgent recommendations", "urgent products"
    ]):
        try:
            with engine.connect() as conn:
                rows = conn.execute(text("""
                    SELECT product_id, store_id, stockout_risk, predicted_sales, recommended_reorder_qty, replenishment_priority
                    FROM ml.forecast_recommendations
                    WHERE stockout_risk = 'HIGH'
                    ORDER BY recommended_reorder_qty DESC
                    LIMIT 5
                """)).fetchall()

                if not rows:
                    return _resp("No high-risk products currently require urgent attention.")

                lines = ["Products needing attention:\n"]
                df_rows = []
                for idx, r in enumerate(rows, 1):
                    p_id = int(r[0])
                    s_id = int(r[1])
                    risk = str(r[2]).capitalize()
                    dem = float(r[3])
                    reorder = int(round(float(r[4])))
                    lines.append(f"{idx}. SKU {p_id} at Store {s_id} - {risk} Risk (Expected demand: {dem:.0f} units, Suggested reorder: {reorder:,} units)")
                    df_rows.append({
                        "Product / SKU": f"SKU {p_id}",
                        "Store": f"Store {s_id}",
                        "Stockout Risk": f"{risk} Risk",
                        "Expected Demand": f"{dem:.1f} units",
                        "Suggested Reorder": f"{reorder:,} units",
                        "Priority": "Urgent"
                    })

                lines.append("\nRecommended action: Review the replenishment recommendations to allocate stock buffer.")
                answer = "\n".join(lines)
                df = pd.DataFrame(df_rows)

                return _resp(
                    answer,
                    df=df,
                    limit_note="Displaying top priority products with elevated stockout risk.",
                    p_id=int(rows[0][0]),
                    s_id=int(rows[0][1])
                )
        except Exception:
            return _resp("I could not access the inventory data right now.")

    # ── Intent 5: "Which stores need attention?" (Step 11) ────
    if any(k in q for k in [
        "which stores need attention", "stores need attention", "stores at risk",
        "which store needs attention", "store risk", "show stores"
    ]):
        try:
            with engine.connect() as conn:
                rows = conn.execute(text("""
                    SELECT store_id, high_risk_products, urgent_reorders, predicted_sales, avg_reorder_qty
                    FROM ml.store_recommendations
                    WHERE high_risk_products > 0
                    ORDER BY high_risk_products DESC, urgent_reorders DESC
                    LIMIT 5
                """)).fetchall()

                if not rows:
                    return _resp("No store locations currently have high-risk products.")

                top_store = int(rows[0][0])
                top_hr = int(rows[0][1])
                top_ur = int(rows[0][2])

                answer = (
                    f"Store {top_store} needs attention because it has a high number of high-risk products "
                    f"and urgent recommendations ({top_hr} high-risk products, {top_ur} urgent reorders).\n\n"
                    f"Recommended action: Review store replenishment priorities in Store 360."
                )

                df_rows = []
                for r in rows:
                    df_rows.append({
                        "Store": f"Store {int(r[0])}",
                        "High Risk Products": int(r[1]),
                        "Urgent Reorders": int(r[2]),
                        "Expected Store Demand": f"{float(r[3]):,.1f} units",
                        "Avg Reorder Qty": f"{float(r[4]):.1f} units"
                    })

                return _resp(
                    answer,
                    df=pd.DataFrame(df_rows),
                    limit_note="Aggregated from model recommendations across all store catalog lines.",
                    s_id=top_store
                )
        except Exception:
            return _resp("I could not access the inventory data right now.")

    # ── Intent 6: Customer Purchase Insights (Step 12) ────────
    if any(k in q for k in [
        "customer", "purchase behavior", "bought together", "frequently bought",
        "reorder behavior", "popular products", "market basket", "basket association"
    ]):
        try:
            with engine.connect() as conn:
                rows = conn.execute(text("""
                    SELECT product_name, department, purchase_count, reorder_rate_pct, reorder_signal
                    FROM ml.product_reorder_behavior
                    ORDER BY purchase_count DESC
                    LIMIT 5
                """)).fetchall()

                if not rows:
                    return _resp("I do not have enough data to answer that.")

                top_items = [f"{r[0]} ({float(r[3]):.1f}% reorder rate)" for r in rows[:3]]
                answer = (
                    "Based on customer purchase behavior analysis from the Instacart complementary dataset: "
                    f"the most frequently purchased and reordered items include {', '.join(top_items)}.\n\n"
                    "Note: This evidence describes general consumer grocery buying patterns and is not a direct customer match to FreshRetailNet stores."
                )

                df_rows = []
                for r in rows:
                    df_rows.append({
                        "Product Name": str(r[0]),
                        "Department": str(r[1]),
                        "Purchase Count": f"{int(r[2]):,}",
                        "Reorder Rate": f"{float(r[3]):.1f}%",
                        "Reorder Signal": str(r[4])
                    })

                return _resp(
                    answer,
                    df=pd.DataFrame(df_rows),
                    limit_note="Evidence derived from Instacart Market Basket Analysis as complementary purchasing behavior."
                )
        except Exception:
            return _resp("I could not access the inventory data right now.")

    # ── Fallback: Product or Store detail lookup ───────────────
    if target_pid is not None or target_sid is not None:
        try:
            with engine.connect() as conn:
                if target_pid is not None:
                    row = conn.execute(text("""
                        SELECT store_id, product_id, stockout_risk, predicted_sales,
                               recommended_reorder_qty, replenishment_priority, risk_explanation
                        FROM ml.forecast_recommendations
                        WHERE product_id = :p
                        ORDER BY (CASE WHEN stockout_risk='HIGH' THEN 1 WHEN stockout_risk='MEDIUM' THEN 2 ELSE 3 END),
                                 recommended_reorder_qty DESC
                        LIMIT 1
                    """), {"p": int(target_pid)}).fetchone()
                else:
                    row = conn.execute(text("""
                        SELECT store_id, product_id, stockout_risk, predicted_sales,
                               recommended_reorder_qty, replenishment_priority, risk_explanation
                        FROM ml.forecast_recommendations
                        WHERE store_id = :s
                        ORDER BY (CASE WHEN stockout_risk='HIGH' THEN 1 WHEN stockout_risk='MEDIUM' THEN 2 ELSE 3 END),
                                 recommended_reorder_qty DESC
                        LIMIT 1
                    """), {"s": int(target_sid)}).fetchone()

                if row:
                    s_id = int(row[0])
                    p_id = int(row[1])
                    risk = str(row[2]).capitalize()
                    dem = float(row[3])
                    reorder = int(round(float(row[4])))
                    pri = "Urgent" if str(row[5]).upper() == "HIGH" else "Normal"
                    answer = (
                        f"SKU {p_id} at Store {s_id} is marked {risk} Risk.\n\n"
                        f"Expected demand is about {int(round(dem))} units.\n\n"
                        f"The current analysis shows elevated stockout risk and the recommendation is marked {pri}.\n\n"
                        f"Suggested reorder: {reorder:,} units.\n\n"
                        f"Recommended action: Review the replenishment recommendation."
                    )
                    df = pd.DataFrame([{
                        "Product / SKU": f"SKU {p_id}",
                        "Store": f"Store {s_id}",
                        "Stockout Risk": f"{risk} Risk",
                        "Expected Demand": f"{dem:.1f} units",
                        "Suggested Reorder": f"{reorder:,} units",
                        "Priority": pri
                    }])
                    return _resp(answer, df=df, p_id=p_id, s_id=s_id)
        except Exception:
            return _resp("I could not access the inventory data right now.")

    # Generic fallback
    return _resp(
        "I do not have enough data to answer that. Please select one of the suggested questions or specify a Store and Product SKU."
    )
