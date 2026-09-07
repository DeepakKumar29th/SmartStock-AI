"""
SmartStock AI — Test Suite
============================================================
Run with:   pytest tests/ -v
Or:         python -m pytest tests/ -v --tb=short
============================================================
"""

# ============================================================
# tests/test_data_quality.py
# Tests: database connectivity, table existence, row counts,
#        ML table contents, Instacart data quality
# ============================================================

import pytest
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
from dotenv import load_dotenv
import os

# Load env
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")


@pytest.fixture(scope="session")
def engine():
    url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    eng = create_engine(url, pool_pre_ping=True)
    with eng.connect() as conn:
        conn.execute(text("SELECT 1"))
    return eng


# ──────────────────────────────────────────────────────────────
# DATABASE CONNECTIVITY
# ──────────────────────────────────────────────────────────────

class TestDatabaseConnectivity:

    def test_connection_succeeds(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1

    def test_required_schemas_exist(self, engine):
        with engine.connect() as conn:
            schemas = [r[0] for r in conn.execute(text(
                "SELECT schema_name FROM information_schema.schemata"
            )).fetchall()]
        for s in ["core", "ml", "raw"]:
            assert s in schemas, f"Schema '{s}' is missing"

    def test_core_tables_exist(self, engine):
        required = ["core.dim_store", "core.dim_product", "core.fact_daily_sales"]
        with engine.connect() as conn:
            for tbl in required:
                schema, name = tbl.split(".")
                cnt = conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_schema = :s AND table_name = :n
                """), {"s": schema, "n": name}).scalar()
                assert cnt == 1, f"Table {tbl} does not exist"

    def test_ml_tables_exist(self, engine):
        required = [
            "ml.features_daily", "ml.train_dataset", "ml.test_dataset",
            "ml.demand_predictions", "ml.forecast_recommendations",
            "ml.business_kpis", "ml.store_recommendations",
            "ml.product_recommendations", "ml.category_summary",
            "ml.dashboard_top20_products"
        ]
        with engine.connect() as conn:
            for tbl in required:
                schema, name = tbl.split(".")
                cnt = conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_schema = :s AND table_name = :n
                """), {"s": schema, "n": name}).scalar()
                assert cnt == 1, f"Table {tbl} does not exist"


# ──────────────────────────────────────────────────────────────
# FRESHRETAILNET DATA QUALITY
# ──────────────────────────────────────────────────────────────

class TestFreshRetailNetQuality:

    def test_fact_table_row_count(self, engine):
        with engine.connect() as conn:
            cnt = conn.execute(text("SELECT COUNT(*) FROM core.fact_daily_sales")).scalar()
        assert cnt == 4_500_000, f"Expected 4,500,000 rows, got {cnt:,}"

    def test_dim_store_count(self, engine):
        with engine.connect() as conn:
            cnt = conn.execute(text("SELECT COUNT(*) FROM core.dim_store")).scalar()
        assert cnt == 898, f"Expected 898 stores, got {cnt}"

    def test_dim_product_count(self, engine):
        with engine.connect() as conn:
            cnt = conn.execute(text("SELECT COUNT(*) FROM core.dim_product")).scalar()
        assert cnt == 865, f"Expected 865 products, got {cnt}"

    def test_no_negative_sales(self, engine):
        with engine.connect() as conn:
            cnt = conn.execute(text(
                "SELECT COUNT(*) FROM core.fact_daily_sales WHERE sale_amount < 0"
            )).scalar()
        assert cnt == 0, f"Found {cnt} negative sales rows"

    def test_no_missing_values_in_fact(self, engine):
        cols = ["store_id", "product_id", "dt", "sale_amount", "stockout_flag",
                "discount", "holiday_flag", "activity_flag", "precpt",
                "avg_temperature", "avg_humidity", "avg_wind_level"]
        with engine.connect() as conn:
            for col in cols:
                cnt = conn.execute(text(
                    f"SELECT COUNT(*) FROM core.fact_daily_sales WHERE {col} IS NULL"
                )).scalar()
                assert cnt == 0, f"Column {col} has {cnt} NULL values"

    def test_stockout_hours_in_valid_range(self, engine):
        with engine.connect() as conn:
            cnt = conn.execute(text("""
                SELECT COUNT(*) FROM core.fact_daily_sales
                WHERE total_stockout_hours < 0 OR total_stockout_hours > 24
            """)).scalar()
        assert cnt == 0, f"Found {cnt} rows with invalid stockout hours"

    def test_no_orphan_stores(self, engine):
        with engine.connect() as conn:
            cnt = conn.execute(text("""
                SELECT COUNT(*) FROM core.fact_daily_sales f
                LEFT JOIN core.dim_store s ON f.store_id = s.store_id
                WHERE s.store_id IS NULL
            """)).scalar()
        assert cnt == 0, f"Found {cnt} orphan store rows"

    def test_no_orphan_products(self, engine):
        with engine.connect() as conn:
            cnt = conn.execute(text("""
                SELECT COUNT(*) FROM core.fact_daily_sales f
                LEFT JOIN core.dim_product p ON f.product_id = p.product_id
                WHERE p.product_id IS NULL
            """)).scalar()
        assert cnt == 0, f"Found {cnt} orphan product rows"

    def test_date_range(self, engine):
        with engine.connect() as conn:
            min_dt, max_dt = conn.execute(text(
                "SELECT MIN(dt), MAX(dt) FROM core.fact_daily_sales"
            )).fetchone()
        assert str(min_dt) == "2024-03-28", f"Unexpected min date: {min_dt}"
        assert str(max_dt) == "2024-06-25", f"Unexpected max date: {max_dt}"


# ──────────────────────────────────────────────────────────────
# ML PIPELINE
# ──────────────────────────────────────────────────────────────

class TestMLPipeline:

    def test_features_daily_row_count(self, engine):
        with engine.connect() as conn:
            cnt = conn.execute(text("SELECT COUNT(*) FROM ml.features_daily")).scalar()
        assert cnt == 4_500_000, f"Expected 4,500,000 feature rows, got {cnt:,}"

    def test_features_daily_has_required_columns(self, engine):
        required_cols = [
            "store_id", "product_id", "dt", "sale_amount",
            "lag_1_sales", "lag_3_sales", "lag_7_sales",
            "rolling_3_mean", "rolling_7_mean", "rolling_7_std",
            "target_next_day_sales", "stockout_flag"
        ]
        with engine.connect() as conn:
            cols = [r[0] for r in conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'ml' AND table_name = 'features_daily'
            """)).fetchall()]
        for col in required_cols:
            assert col in cols, f"Column '{col}' missing from ml.features_daily"

    def test_forecast_recommendations_count(self, engine):
        with engine.connect() as conn:
            cnt = conn.execute(text(
                "SELECT COUNT(*) FROM ml.forecast_recommendations"
            )).scalar()
        assert cnt == 300_000, f"Expected 300,000 forecast rows, got {cnt:,}"

    def test_business_kpis_populated(self, engine):
        with engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM ml.business_kpis")).fetchone()
        assert row is not None
        assert row[0] == 300_000  # total_predictions


# ──────────────────────────────────────────────────────────────
# REPLENISHMENT LOGIC
# ──────────────────────────────────────────────────────────────

class TestReplenishmentLogic:

    def test_risk_values_are_valid(self, engine):
        with engine.connect() as conn:
            invalid = conn.execute(text("""
                SELECT COUNT(*) FROM ml.forecast_recommendations
                WHERE stockout_risk NOT IN ('HIGH', 'MEDIUM', 'LOW')
            """)).scalar()
        assert invalid == 0, f"Found {invalid} rows with invalid stockout_risk values"

    def test_priority_values_are_valid(self, engine):
        with engine.connect() as conn:
            invalid = conn.execute(text("""
                SELECT COUNT(*) FROM ml.forecast_recommendations
                WHERE replenishment_priority NOT IN ('HIGH', 'MEDIUM', 'LOW')
            """)).scalar()
        assert invalid == 0, f"Found {invalid} rows with invalid priority values"

    def test_reorder_qty_is_positive(self, engine):
        with engine.connect() as conn:
            invalid = conn.execute(text("""
                SELECT COUNT(*) FROM ml.forecast_recommendations
                WHERE recommended_reorder_qty <= 0
            """)).scalar()
        assert invalid == 0, f"Found {invalid} rows with non-positive reorder qty"

    def test_high_priority_requires_high_risk(self, engine):
        """HIGH priority should only occur when risk is HIGH or MEDIUM."""
        with engine.connect() as conn:
            invalid = conn.execute(text("""
                SELECT COUNT(*) FROM ml.forecast_recommendations
                WHERE replenishment_priority = 'HIGH'
                AND stockout_risk = 'LOW'
            """)).scalar()
        assert invalid == 0, \
            f"Found {invalid} HIGH-priority rows with LOW stockout risk (logic error)"


# ──────────────────────────────────────────────────────────────
# INSTACART (skip if not loaded)
# ──────────────────────────────────────────────────────────────

def _instacart_loaded(engine) -> bool:
    try:
        with engine.connect() as conn:
            cnt = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'instacart' AND table_name = 'products'
            """)).scalar()
            return cnt > 0
    except Exception:
        return False


class TestInstacartQuality:

    def test_instacart_available(self, engine):
        if not _instacart_loaded(engine):
            pytest.skip("Instacart data not yet loaded — run step_9_1 first")

    def test_instacart_departments_count(self, engine):
        if not _instacart_loaded(engine):
            pytest.skip("Instacart not loaded")
        with engine.connect() as conn:
            cnt = conn.execute(text("SELECT COUNT(*) FROM instacart.departments")).scalar()
        assert cnt == 21

    def test_instacart_products_count(self, engine):
        if not _instacart_loaded(engine):
            pytest.skip("Instacart not loaded")
        with engine.connect() as conn:
            cnt = conn.execute(text("SELECT COUNT(*) FROM instacart.products")).scalar()
        assert cnt == 49_688

    def test_instacart_orders_count(self, engine):
        if not _instacart_loaded(engine):
            pytest.skip("Instacart not loaded")
        with engine.connect() as conn:
            cnt = conn.execute(text("SELECT COUNT(*) FROM instacart.orders")).scalar()
        assert cnt == 3_421_083

    def test_instacart_prior_count(self, engine):
        if not _instacart_loaded(engine):
            pytest.skip("Instacart not loaded")
        with engine.connect() as conn:
            cnt = conn.execute(text(
                "SELECT COUNT(*) FROM instacart.order_products_prior"
            )).scalar()
        assert cnt == 32_434_489

    def test_reordered_flag_valid(self, engine):
        if not _instacart_loaded(engine):
            pytest.skip("Instacart not loaded")
        with engine.connect() as conn:
            invalid = conn.execute(text("""
                SELECT COUNT(*) FROM instacart.order_products_prior
                WHERE reordered NOT IN (0, 1)
            """)).scalar()
        assert invalid == 0

    def test_no_orphan_products_in_prior(self, engine):
        if not _instacart_loaded(engine):
            pytest.skip("Instacart not loaded")
        with engine.connect() as conn:
            orphans = conn.execute(text("""
                SELECT COUNT(*) FROM instacart.order_products_prior opp
                LEFT JOIN instacart.products p ON opp.product_id = p.product_id
                WHERE p.product_id IS NULL
            """)).scalar()
        assert orphans == 0


# ──────────────────────────────────────────────────────────────
# MARKET BASKET RULES
# ──────────────────────────────────────────────────────────────

class TestMarketBasketRules:

    def _rules_available(self, engine) -> bool:
        try:
            with engine.connect() as conn:
                cnt = conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_schema = 'ml' AND table_name = 'market_basket_rules'
                """)).scalar()
                return cnt > 0
        except Exception:
            return False

    def test_rules_table_exists(self, engine):
        if not self._rules_available(engine):
            pytest.skip("ml.market_basket_rules not yet created")
        with engine.connect() as conn:
            cnt = conn.execute(text("SELECT COUNT(*) FROM ml.market_basket_rules")).scalar()
        assert cnt > 0, "market_basket_rules is empty"

    def test_support_in_valid_range(self, engine):
        if not self._rules_available(engine):
            pytest.skip("ml.market_basket_rules not yet created")
        with engine.connect() as conn:
            invalid = conn.execute(text("""
                SELECT COUNT(*) FROM ml.market_basket_rules
                WHERE support < 0 OR support > 1
            """)).scalar()
        assert invalid == 0, f"Found {invalid} rules with support outside [0,1]"

    def test_confidence_in_valid_range(self, engine):
        if not self._rules_available(engine):
            pytest.skip("ml.market_basket_rules not yet created")
        with engine.connect() as conn:
            invalid = conn.execute(text("""
                SELECT COUNT(*) FROM ml.market_basket_rules
                WHERE confidence < 0 OR confidence > 1
            """)).scalar()
        assert invalid == 0, f"Found {invalid} rules with confidence outside [0,1]"

    def test_lift_is_positive(self, engine):
        if not self._rules_available(engine):
            pytest.skip("ml.market_basket_rules not yet created")
        with engine.connect() as conn:
            invalid = conn.execute(text("""
                SELECT COUNT(*) FROM ml.market_basket_rules
                WHERE lift <= 0
            """)).scalar()
        assert invalid == 0, f"Found {invalid} rules with lift <= 0"

    def test_no_self_association(self, engine):
        if not self._rules_available(engine):
            pytest.skip("ml.market_basket_rules not yet created")
        with engine.connect() as conn:
            self_rules = conn.execute(text("""
                SELECT COUNT(*) FROM ml.market_basket_rules
                WHERE antecedent_product = consequent_product
            """)).scalar()
        assert self_rules == 0, f"Found {self_rules} self-association rules (A → A)"


# ──────────────────────────────────────────────────────────────
# AI ASSISTANT SAFETY
# ──────────────────────────────────────────────────────────────

class TestAIAssistantSafety:

    def test_sql_safety_guard_blocks_dangerous(self):
        import sys
        sys.path.insert(0, str(_ROOT / "streamlit"))
        from ai_assistant import _safe_sql

        dangerous = [
            "DROP TABLE ml.business_kpis",
            "DELETE FROM core.fact_daily_sales",
            "UPDATE ml.features_daily SET sale_amount = 0",
            "INSERT INTO ml.business_kpis VALUES (1)",
            "TRUNCATE ml.forecast_recommendations",
        ]
        for sql in dangerous:
            assert not _safe_sql(sql), f"Dangerous SQL was not blocked: {sql}"

    def test_sql_safety_guard_allows_select(self):
        import sys
        sys.path.insert(0, str(_ROOT / "streamlit"))
        from ai_assistant import _safe_sql

        safe = [
            "SELECT * FROM ml.business_kpis",
            "SELECT product_id FROM ml.product_recommendations ORDER BY high_risk_pct DESC LIMIT 10",
        ]
        for sql in safe:
            assert _safe_sql(sql), f"Safe SQL was incorrectly blocked: {sql}"

    def test_intent_detection_high_risk(self):
        import sys
        sys.path.insert(0, str(_ROOT / "streamlit"))
        from ai_assistant import detect_intent

        key, _ = detect_intent("Which products have the highest stockout risk?")
        assert key == "high_risk_products"

    def test_intent_detection_stores(self):
        import sys
        sys.path.insert(0, str(_ROOT / "streamlit"))
        from ai_assistant import detect_intent

        key, _ = detect_intent("Which stores need urgent replenishment?")
        assert key == "high_priority_stores"

    def test_intent_detection_basket(self):
        import sys
        sys.path.insert(0, str(_ROOT / "streamlit"))
        from ai_assistant import detect_intent

        key, _ = detect_intent("What products are frequently bought together?")
        assert key == "basket_associations"

    def test_intent_detection_product_id(self):
        import sys
        sys.path.insert(0, str(_ROOT / "streamlit"))
        from ai_assistant import detect_intent

        key, params = detect_intent("Why is product 267 high risk?")
        assert params.get("product_id") == 267
