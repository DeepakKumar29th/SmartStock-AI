# ============================================================
# SMARTSTOCK AI — PHASE 7 REPLENISHMENT TESTS
# tests/test_phase7_replenishment.py
# ============================================================

import pytest
import pandas as pd
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "streamlit"))

from db_connection import get_engine
from data_loader import (
    save_replenishment_decision,
    load_recent_replenishment_decisions,
    load_replenishment_decision_summary,
    load_today_decisions,
    load_forecast_recommendations
)


@pytest.fixture(scope="module")
def engine():
    return get_engine()


def test_load_recommendations_default(engine):
    """CASE 1: Open Replenishment - recommendations load."""
    df = load_forecast_recommendations(engine, latest_only=True, limit=20)
    assert not df.empty
    assert len(df) <= 20
    assert "store_id" in df.columns
    assert "product_id" in df.columns
    assert "recommended_reorder_qty" in df.columns
    assert "predicted_sales" in df.columns
    assert "stockout_risk" in df.columns


def test_filter_high_risk_recommendations(engine):
    """CASE 2: Filter High Risk recommendations."""
    df = load_forecast_recommendations(engine, risk_levels=["HIGH"], latest_only=True, limit=20)
    assert not df.empty
    assert (df["stockout_risk"] == "HIGH").all()


def test_approve_workflow(engine):
    """CASE 5: Approve recommendation - saved to database."""
    today = date.today()
    test_sid = 999
    test_pid = 999
    res = save_replenishment_decision(
        engine=engine,
        store_id=test_sid,
        product_id=test_pid,
        recommended_qty=150.0,
        approved_qty=150.0,
        decision_status="APPROVED",
        notes="Automated test approval",
        decision_date=today
    )
    # Note: store 999 / product 999 will violate foreign key constraint to dim_store/dim_product
    # Let's test with a valid store and product from the database
    valid_recs = load_forecast_recommendations(engine, limit=1)
    v_sid = int(valid_recs.iloc[0]["store_id"])
    v_pid = int(valid_recs.iloc[0]["product_id"])
    rec_qty = float(valid_recs.iloc[0]["recommended_reorder_qty"])

    res_valid = save_replenishment_decision(
        engine=engine,
        store_id=v_sid,
        product_id=v_pid,
        recommended_qty=rec_qty,
        approved_qty=rec_qty,
        decision_status="APPROVED",
        notes="Manager standard approval",
        decision_date=today
    )
    assert res_valid["success"] is True
    assert res_valid["decision_id"] is not None


def test_modify_workflow(engine):
    """CASE 6 & 7: Change Quantity - preserves original rec and updates final quantity."""
    today = date.today()
    valid_recs = load_forecast_recommendations(engine, limit=1)
    v_sid = int(valid_recs.iloc[0]["store_id"])
    v_pid = int(valid_recs.iloc[0]["product_id"])
    rec_qty = float(valid_recs.iloc[0]["recommended_reorder_qty"])
    mod_qty = rec_qty + 25.0

    res_mod = save_replenishment_decision(
        engine=engine,
        store_id=v_sid,
        product_id=v_pid,
        recommended_qty=rec_qty,
        approved_qty=mod_qty,
        decision_status="MODIFIED",
        notes="Adjusted for weekend demand",
        decision_date=today
    )
    assert res_mod["success"] is True
    assert res_mod["is_new"] is False  # Upserted today's existing record

    # Check today's decisions
    today_map = load_today_decisions(engine)
    assert (v_sid, v_pid) in today_map
    assert today_map[(v_sid, v_pid)]["status"] == "MODIFIED"
    assert today_map[(v_sid, v_pid)]["recommended_qty"] == round(rec_qty, 2)
    assert today_map[(v_sid, v_pid)]["approved_qty"] == round(mod_qty, 2)


def test_reject_workflow(engine):
    """CASE 8: Reject recommendation - stores approved_qty=0 and REJECTED status."""
    today = date.today()
    # Find another valid store/product
    recs = load_forecast_recommendations(engine, limit=5)
    target = recs.iloc[-1]
    sid = int(target["store_id"])
    pid = int(target["product_id"])
    rec_qty = float(target["recommended_reorder_qty"])

    res_rej = save_replenishment_decision(
        engine=engine,
        store_id=sid,
        product_id=pid,
        recommended_qty=rec_qty,
        approved_qty=0.0,
        decision_status="REJECTED",
        notes="Rejected: Already stocked from internal transfer",
        decision_date=today
    )
    assert res_rej["success"] is True

    today_map = load_today_decisions(engine)
    assert (sid, pid) in today_map
    assert today_map[(sid, pid)]["status"] == "REJECTED"
    assert today_map[(sid, pid)]["approved_qty"] == 0.0


def test_validation_invalid_status(engine):
    """CASE 9: Invalid status is rejected."""
    res = save_replenishment_decision(
        engine=engine,
        store_id=0,
        product_id=1,
        recommended_qty=50.0,
        approved_qty=50.0,
        decision_status="INVALID_STATUS"
    )
    assert res["success"] is False
    assert "Status must be one of" in res["message"]


def test_validation_invalid_inputs(engine):
    """CASE 10: Invalid non-numeric input is rejected."""
    res = save_replenishment_decision(
        engine=engine,
        store_id="invalid",
        product_id=1,
        recommended_qty=50.0,
        approved_qty=50.0
    )
    assert res["success"] is False


def test_load_recent_decisions(engine):
    """CASE 13 & 14: Verify decision history and summary."""
    df_hist = load_recent_replenishment_decisions(engine, limit=10)
    assert not df_hist.empty
    expected_cols = [
        "decision_id", "decision_date", "store_id", "product_id",
        "recommended_qty", "approved_qty", "decision_status", "decision_notes"
    ]
    for col in expected_cols:
        assert col in df_hist.columns

    summary = load_replenishment_decision_summary(engine)
    assert summary["total_decisions"] > 0
    assert "rejected_count" in summary


def test_no_recommendations_empty_result(engine):
    """CASE 15: Filter with non-existent store returns empty dataframe gracefully."""
    df = load_forecast_recommendations(engine, store_id=999999, latest_only=True)
    assert isinstance(df, pd.DataFrame)
    assert df.empty
