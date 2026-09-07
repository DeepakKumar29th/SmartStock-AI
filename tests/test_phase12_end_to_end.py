# ============================================================
# SMARTSTOCK AI — PHASE 12 END-TO-END INTEGRATION TESTS
# tests/test_phase12_end_to_end.py
#
# Covers the complete 15-step project workflow:
# 1. Open Dashboard
# 2. Select Product
# 3. Analyze Product
# 4. Check Expected Demand
# 5. Check Risk
# 6. Open Replenishment
# 7. Review Suggested Reorder
# 8. Approve or Modify Recommendation
# 9. Verify Decision in PostgreSQL
# 10. Check Action History
# 11. Add Operational Inventory Record
# 12. Verify Operational Record in PostgreSQL
# 13. Open AI Inventory Assistant
# 14. Ask Why Product is at Risk
# 15. Verify Answer matches PostgreSQL values
# ============================================================

import sys
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import text

# Add streamlit directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "streamlit"))

from db_connection import get_engine
from data_loader import (
    load_business_kpis,
    load_products_catalog,
    load_stores_catalog,
    load_product_recommendations,
    load_store_product_forecast,
    load_forecast_recommendations,
    save_replenishment_decision,
    load_recent_replenishment_decisions,
    save_inventory_update,
    load_recent_inventory_updates,
)
from ai_assistant import answer_question


@pytest.fixture(scope="session")
def engine():
    return get_engine()


class TestPhase12EndToEndWorkflow:
    TEST_STORE = 631
    TEST_SKU = 267

    # STEP 1: Open Dashboard
    def test_step_01_open_dashboard(self, engine):
        kpis = load_business_kpis(engine)
        assert isinstance(kpis, dict)
        assert "total_predictions" in kpis
        assert "high_risk_products" in kpis
        assert "total_stores" in kpis
        assert kpis["total_stores"] > 0
        assert kpis["total_actual_sales"] > 0

    # STEP 2: Select Product
    def test_step_02_select_product(self, engine):
        products_df = load_products_catalog(engine)
        assert not products_df.empty
        assert "product_id" in products_df.columns
        assert self.TEST_SKU in products_df["product_id"].values

        stores_df = load_stores_catalog(engine)
        assert not stores_df.empty
        assert "store_id" in stores_df.columns
        assert self.TEST_STORE in stores_df["store_id"].values

    # STEP 3: Analyze Product
    def test_step_03_analyze_product(self, engine):
        product_recs = load_product_recommendations(engine)
        assert not product_recs.empty
        match = product_recs[product_recs["product_id"] == self.TEST_SKU]
        assert not match.empty
        assert int(match.iloc[0]["product_id"]) == self.TEST_SKU

        forecast_df = load_store_product_forecast(engine, self.TEST_STORE, self.TEST_SKU)
        assert not forecast_df.empty
        assert "predicted_sales" in forecast_df.columns
        assert "stockout_risk" in forecast_df.columns

    # STEP 4: Check Expected Demand
    def test_step_04_check_expected_demand(self, engine):
        forecast_df = load_store_product_forecast(engine, self.TEST_STORE, self.TEST_SKU)
        latest = forecast_df.iloc[-1]
        pred_sales = float(latest["predicted_sales"])
        assert pred_sales >= 0.0

    # STEP 5: Check Risk
    def test_step_05_check_risk(self, engine):
        forecast_df = load_store_product_forecast(engine, self.TEST_STORE, self.TEST_SKU)
        latest = forecast_df.iloc[-1]
        assert latest["stockout_risk"] in ["HIGH", "MEDIUM", "LOW"]
        assert len(str(latest["risk_explanation"]).strip()) > 0

    # STEP 6: Open Replenishment
    def test_step_06_open_replenishment(self, engine):
        repl_df = load_forecast_recommendations(
            engine,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            latest_only=True,
            limit=10,
        )
        assert not repl_df.empty
        assert int(repl_df.iloc[0]["product_id"]) == self.TEST_SKU
        assert int(repl_df.iloc[0]["store_id"]) == self.TEST_STORE

    # STEP 7: Review Suggested Reorder
    def test_step_07_review_suggested_reorder(self, engine):
        repl_df = load_forecast_recommendations(
            engine,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            latest_only=True,
            limit=10,
        )
        reorder_qty = float(repl_df.iloc[0]["recommended_reorder_qty"])
        assert reorder_qty > 0.0

    # STEP 8: Approve or Modify a recommendation
    def test_step_08_approve_decision(self, engine):
        repl_df = load_forecast_recommendations(
            engine,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            latest_only=True,
            limit=10,
        )
        orig_qty = float(repl_df.iloc[0]["recommended_reorder_qty"])
        result = save_replenishment_decision(
            engine=engine,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            recommended_qty=orig_qty,
            approved_qty=orig_qty,
            decision_status="APPROVED",
            notes="Phase 12 End-to-End verified workflow decision",
            decided_by="Operations Lead",
            decision_date=date.today(),
        )
        assert result["success"] is True

    # STEP 9: Verify the decision is stored in PostgreSQL
    def test_step_09_verify_decision_in_postgres(self, engine):
        with engine.connect() as conn:
            row = conn.execute(
                text("""
                    SELECT decision_status, approved_qty, decision_notes, decision_date
                    FROM app.replenishment_decisions
                    WHERE store_id = :s AND product_id = :p
                    ORDER BY decision_date DESC, updated_at DESC LIMIT 1
                """),
                {"s": self.TEST_STORE, "p": self.TEST_SKU},
            ).fetchone()
            assert row is not None
            assert row[0] == "APPROVED"
            assert float(row[1]) > 0
            assert "Phase 12" in str(row[2])

    # STEP 10: Check Action History
    def test_step_10_check_action_history(self, engine):
        history_df = load_recent_replenishment_decisions(
            engine,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            limit=10,
        )
        assert not history_df.empty
        assert int(history_df.iloc[0]["store_id"]) == self.TEST_STORE
        assert int(history_df.iloc[0]["product_id"]) == self.TEST_SKU
        assert history_df.iloc[0]["decision_status"] == "APPROVED"

    # STEP 11: Add an operational inventory update record
    def test_step_11_add_inventory_record(self, engine):
        today = date.today()
        result = save_inventory_update(
            engine=engine,
            dt=today,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            sale_amount=38.0,
            stock_status="Low Stock",
            discount=5.0,
            holiday_flag=0,
            activity_flag=1,
            notes="Phase 12 verified daily intake record",
        )
        assert result["success"] is True

    # STEP 12: Verify the record is stored in PostgreSQL
    def test_step_12_verify_inventory_record_in_postgres(self, engine):
        with engine.connect() as conn:
            row = conn.execute(
                text("""
                    SELECT stock_status, sale_amount, notes
                    FROM app.inventory_updates
                    WHERE store_id = :s AND product_id = :p AND dt = :dt
                """),
                {"s": self.TEST_STORE, "p": self.TEST_SKU, "dt": date.today()},
            ).fetchone()
            assert row is not None
            assert row[0] == "Low Stock"
            assert float(row[1]) == 38.0
            assert "Phase 12 verified" in str(row[2])

    # STEP 13: Open AI Inventory Assistant
    def test_step_13_open_ai_assistant(self, engine):
        ans = answer_question(engine, "What can you explain?")
        assert isinstance(ans, dict)
        assert len(ans.get("answer", "")) > 50

    # STEP 14: Ask why the product is at risk
    def test_step_14_ask_why_product_at_risk(self, engine):
        q = f"Why is SKU {self.TEST_SKU} at Store {self.TEST_STORE} at high risk?"
        ans = answer_question(engine, q)
        answer_text = ans.get("answer", "")
        assert str(self.TEST_SKU) in answer_text
        assert str(self.TEST_STORE) in answer_text

    # STEP 15: Verify the answer matches PostgreSQL values
    def test_step_15_verify_answer_matches_database(self, engine):
        q = f"Why is SKU {self.TEST_SKU} at Store {self.TEST_STORE} at high risk?"
        ans = answer_question(engine, q)

        # Fetch actual value from PostgreSQL
        with engine.connect() as conn:
            db_row = conn.execute(
                text("""
                    SELECT recommended_reorder_qty, predicted_sales, stockout_risk
                    FROM ml.forecast_recommendations
                    WHERE store_id = :s AND product_id = :p
                    ORDER BY dt DESC LIMIT 1
                """),
                {"s": self.TEST_STORE, "p": self.TEST_SKU},
            ).fetchone()

        assert db_row is not None
        rec_qty = float(db_row[0])
        pred_sales = float(db_row[1])
        risk_lvl = str(db_row[2])

        # Verify assistant response contains the database values
        answer_text = ans.get("answer", "")
        assert str(int(round(rec_qty))) in answer_text
        assert risk_lvl.upper() in answer_text.upper()
