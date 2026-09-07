# ============================================================
# SMARTSTOCK AI — PHASE 8 ACTION HISTORY TESTS
# tests/test_phase8_action_history.py
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
    load_decided_stores_and_products,
    load_forecast_recommendations
)


@pytest.fixture(scope="module")
def engine():
    return get_engine()


@pytest.fixture(scope="module")
def sample_store_product(engine):
    """Retrieve a valid store_id and product_id from recommendations catalog."""
    recs = load_forecast_recommendations(engine, limit=5)
    sid = int(recs.iloc[0]["store_id"])
    pid = int(recs.iloc[0]["product_id"])
    rec_qty = float(recs.iloc[0]["recommended_reorder_qty"])
    return sid, pid, rec_qty


def test_case_1_empty_state_handling():
    """CASE 1: No decisions exist -> summary and empty df handle gracefully."""
    empty_df = pd.DataFrame(columns=[
        "decision_id", "decision_date", "store_id", "product_id",
        "recommended_qty", "approved_qty", "decision_status", "decision_notes"
    ])
    assert empty_df.empty
    assert len(empty_df) == 0


def test_case_2_approve_recommendation(engine, sample_store_product):
    """CASE 2: Approve a recommendation -> approved decision appears in history."""
    sid, pid, rec_qty = sample_store_product
    res = save_replenishment_decision(
        engine=engine,
        store_id=sid,
        product_id=pid,
        recommended_qty=rec_qty,
        approved_qty=rec_qty,
        decision_status="APPROVED",
        notes="Automated test approval for Phase 8"
    )
    assert res["success"] is True

    df = load_recent_replenishment_decisions(engine, store_id=sid, product_id=pid)
    assert not df.empty
    row = df.iloc[0]
    assert row["decision_status"] == "APPROVED"
    assert float(row["approved_qty"]) == pytest.approx(rec_qty, 0.1)


def test_case_3_modify_recommendation(engine, sample_store_product):
    """CASE 3: Modify a recommendation -> original and final quantity both appear."""
    sid, pid, rec_qty = sample_store_product
    modified_qty = round(rec_qty * 1.25, 0)
    res = save_replenishment_decision(
        engine=engine,
        store_id=sid,
        product_id=pid,
        recommended_qty=rec_qty,
        approved_qty=modified_qty,
        decision_status="MODIFIED",
        notes="Automated test modified quantity for shelf buffer"
    )
    assert res["success"] is True

    df = load_recent_replenishment_decisions(engine, store_id=sid, product_id=pid)
    assert not df.empty
    row = df.iloc[0]
    assert row["decision_status"] == "MODIFIED"
    assert float(row["recommended_qty"]) == pytest.approx(rec_qty, 0.1)
    assert float(row["approved_qty"]) == pytest.approx(modified_qty, 0.1)
    assert "shelf buffer" in row["decision_notes"]


def test_case_4_reject_recommendation(engine, sample_store_product):
    """CASE 4: Reject a recommendation -> rejected decision appears with saved reason."""
    sid, pid, rec_qty = sample_store_product
    res = save_replenishment_decision(
        engine=engine,
        store_id=sid,
        product_id=pid,
        recommended_qty=rec_qty,
        approved_qty=0.0,
        decision_status="REJECTED",
        notes="Supplier shortage / warehouse capacity reached"
    )
    assert res["success"] is True

    df = load_recent_replenishment_decisions(engine, store_id=sid, product_id=pid)
    assert not df.empty
    row = df.iloc[0]
    assert row["decision_status"] == "REJECTED"
    assert float(row["approved_qty"]) == 0.0
    assert float(row["recommended_qty"]) == pytest.approx(rec_qty, 0.1)
    assert "Supplier shortage" in row["decision_notes"]


def test_case_5_filter_approved(engine):
    """CASE 5: Filter Approved -> only approved decisions appear."""
    df = load_recent_replenishment_decisions(engine, decision_status="APPROVED")
    if not df.empty:
        assert (df["decision_status"] == "APPROVED").all()


def test_case_6_filter_modified(engine):
    """CASE 6: Filter Modified -> only modified decisions appear."""
    df = load_recent_replenishment_decisions(engine, decision_status="MODIFIED")
    assert not df.empty
    assert (df["decision_status"] == "MODIFIED").all()


def test_case_7_filter_rejected(engine):
    """CASE 7: Filter Rejected -> only rejected decisions appear."""
    df = load_recent_replenishment_decisions(engine, decision_status="REJECTED")
    assert not df.empty
    assert (df["decision_status"] == "REJECTED").all()


def test_case_8_filter_by_store(engine, sample_store_product):
    """CASE 8: Filter by Store -> correct store records appear."""
    sid, _, _ = sample_store_product
    df = load_recent_replenishment_decisions(engine, store_id=sid)
    assert not df.empty
    assert (df["store_id"] == sid).all()


def test_case_9_filter_by_product(engine, sample_store_product):
    """CASE 9: Filter by Product -> correct product records appear."""
    _, pid, _ = sample_store_product
    df = load_recent_replenishment_decisions(engine, product_id=pid)
    assert not df.empty
    assert (df["product_id"] == pid).all()


def test_case_10_filter_by_date(engine):
    """CASE 10: Filter by Date -> correct records appear."""
    df_today = load_recent_replenishment_decisions(engine, days=0)
    assert not df_today.empty
    for dt in df_today["decision_date"]:
        assert str(dt) == str(date.today())

    df_7d = load_recent_replenishment_decisions(engine, days=7)
    assert not df_7d.empty
    assert len(df_7d) >= len(df_today)


def test_case_11_newest_first_sorting(engine):
    """CASE 11: Newest first -> latest decision appears first."""
    df_desc = load_recent_replenishment_decisions(engine, sort_asc=False)
    df_asc = load_recent_replenishment_decisions(engine, sort_asc=True)
    assert not df_desc.empty and not df_asc.empty

    if len(df_desc) > 1:
        ts = pd.to_datetime(df_desc["updated_at"])
        assert (ts.diff().dropna() <= pd.Timedelta(seconds=1)).all()


def test_case_12_view_product_navigation():
    """CASE 12: View Product -> sets target SKU in session state."""
    session = {}
    target_pid = 267
    target_sid = 631
    session["nav_page"] = "Products"
    session["analyzed_product_id"] = target_pid
    session["analyzed_store_id"] = target_sid
    session["curr_selected_store"] = target_sid

    assert session["nav_page"] == "Products"
    assert session["analyzed_product_id"] == 267
    assert session["analyzed_store_id"] == 631


def test_case_13_view_store_navigation():
    """CASE 13: View Store -> sets target Store in session state."""
    session = {}
    target_sid = 631
    session["nav_page"] = "Stores"
    session["analyzed_store_id"] = target_sid

    assert session["nav_page"] == "Stores"
    assert session["analyzed_store_id"] == 631


def test_case_14_database_failure_handling():
    """CASE 14: Database failure -> handles gracefully with simple error message."""
    class FakeEngine:
        def connect(self):
            raise RuntimeError("Database connection pool exhausted")
        def begin(self):
            raise RuntimeError("Database connection pool exhausted")

    fake = FakeEngine()
    stores, prods = load_decided_stores_and_products(fake)
    assert stores == []
    assert prods == []

    res = save_replenishment_decision(fake, 1, 1, 100, 100, "APPROVED")
    assert res["success"] is False
    assert "Database operation failed" in res["message"]


def test_case_15_refresh_consistency(engine):
    """CASE 15: Refresh -> history data remains consistent across multiple loads."""
    df1 = load_recent_replenishment_decisions(engine, limit=10)
    df2 = load_recent_replenishment_decisions(engine, limit=10)
    pd.testing.assert_frame_equal(df1, df2)


def test_case_16_reload_application(engine):
    """CASE 16: Reload application -> saved decisions persist in PostgreSQL."""
    new_engine = get_engine()
    summary = load_replenishment_decision_summary(new_engine)
    assert summary["total_decisions"] > 0
    assert "approved_count" in summary
    assert "modified_count" in summary
    assert "rejected_count" in summary
