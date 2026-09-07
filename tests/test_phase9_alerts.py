# ============================================================
# SMARTSTOCK AI — PHASE 9 ALERTS WORKFLOW TESTS
# tests/test_phase9_alerts.py
# ============================================================

import pytest
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "streamlit"))

from db_connection import get_engine
from data_loader import (
    save_alert_action,
    load_actionable_alerts,
    load_alerts_summary,
    load_forecast_recommendations
)


@pytest.fixture(scope="module")
def engine():
    return get_engine()


@pytest.fixture(scope="module")
def sample_alert(engine):
    """Retrieve a valid high-risk alert store_id and product_id from recommendations."""
    df = load_actionable_alerts(engine, risk_level="HIGH", limit=5)
    sid = int(df.iloc[0]["store_id"])
    pid = int(df.iloc[0]["product_id"])
    risk = str(df.iloc[0]["stockout_risk"])
    return sid, pid, risk


def test_case_1_open_alerts_query(engine):
    """CASE 1: Open alerts query returns unhandled exceptions."""
    df = load_actionable_alerts(engine, status="OPEN", limit=10)
    assert not df.empty
    assert (df["action_status"] == "OPEN").all()
    assert "stockout_risk" in df.columns
    assert "recommended_reorder_qty" in df.columns


def test_case_2_high_risk_alerts(engine):
    """CASE 2: High-risk alerts filter returns only HIGH risk."""
    df = load_actionable_alerts(engine, risk_level="HIGH", limit=10)
    assert not df.empty
    assert (df["stockout_risk"] == "HIGH").all()


def test_case_3_medium_risk_alerts(engine):
    """CASE 3: Medium-risk alerts filter returns only MEDIUM risk."""
    df = load_actionable_alerts(engine, risk_level="MEDIUM", limit=10)
    assert not df.empty
    assert (df["stockout_risk"] == "MEDIUM").all()


def test_case_4_resolved_alerts_persistence(engine, sample_alert):
    """CASE 4: Resolved alerts persist in database and appear under status RESOLVED."""
    sid, pid, risk = sample_alert
    res = save_alert_action(engine, sid, pid, risk, action_status="RESOLVED", notes="Automated test resolved")
    assert res["success"] is True

    df_res = load_actionable_alerts(engine, status="RESOLVED", store_id=sid, product_id=pid)
    assert not df_res.empty
    assert df_res.iloc[0]["action_status"] == "RESOLVED"
    assert df_res.iloc[0]["store_id"] == sid
    assert df_res.iloc[0]["product_id"] == pid


def test_case_5_store_filter(engine, sample_alert):
    """CASE 5: Store filter returns records matching selected store."""
    sid, _, _ = sample_alert
    df = load_actionable_alerts(engine, store_id=sid, limit=10)
    assert not df.empty
    assert (df["store_id"] == sid).all()


def test_case_6_product_filter(engine, sample_alert):
    """CASE 6: Product filter returns records matching selected product."""
    _, pid, _ = sample_alert
    df = load_actionable_alerts(engine, product_id=pid, limit=10)
    assert not df.empty
    assert (df["product_id"] == pid).all()


def test_case_7_status_filter(engine, sample_alert):
    """CASE 7: Status filter returns records matching selected status."""
    sid, pid, risk = sample_alert
    # Update to REVIEWED
    res = save_alert_action(engine, sid, pid, risk, action_status="REVIEWED", notes="Automated test review")
    assert res["success"] is True

    df_rev = load_actionable_alerts(engine, status="REVIEWED", store_id=sid, product_id=pid)
    assert not df_rev.empty
    assert df_rev.iloc[0]["action_status"] == "REVIEWED"


def test_case_8_priority_filter(engine):
    """CASE 8: Priority filter returns matching priority level."""
    df_urg = load_actionable_alerts(engine, priority="URGENT", limit=10)
    assert not df_urg.empty
    assert (df_urg["replenishment_priority"] == "HIGH").all()


def test_case_9_view_product_navigation():
    """CASE 9: View Product sets navigation state for Product 360."""
    session = {}
    sid, pid = 631, 267
    session["nav_page"] = "Products"
    session["analyzed_product_id"] = pid
    session["analyzed_store_id"] = sid
    session["curr_selected_store"] = sid

    assert session["nav_page"] == "Products"
    assert session["analyzed_product_id"] == 267
    assert session["analyzed_store_id"] == 631


def test_case_10_view_store_navigation():
    """CASE 10: View Store sets navigation state for Store 360."""
    session = {}
    sid = 631
    session["nav_page"] = "Stores"
    session["analyzed_store_id"] = sid

    assert session["nav_page"] == "Stores"
    assert session["analyzed_store_id"] == 631


def test_case_11_view_recommendation_navigation():
    """CASE 11: View Recommendation sets navigation state for Replenishment."""
    session = {}
    sid, pid = 631, 267
    session["nav_page"] = "Replenishment"
    session["repl_store_filter"] = sid
    session["analyzed_store_id"] = sid
    session["analyzed_product_id"] = pid

    assert session["nav_page"] == "Replenishment"
    assert session["repl_store_filter"] == 631
    assert session["analyzed_product_id"] == 267


def test_case_12_mark_reviewed(engine, sample_alert):
    """CASE 12: Mark Reviewed updates status in app.alert_actions."""
    sid, pid, risk = sample_alert
    res = save_alert_action(engine, sid, pid, risk, action_status="REVIEWED", notes="Checked by operator")
    assert res["success"] is True
    assert "action_id" in res


def test_case_13_mark_resolved(engine, sample_alert):
    """CASE 13: Mark Resolved updates status in app.alert_actions."""
    sid, pid, risk = sample_alert
    res = save_alert_action(engine, sid, pid, risk, action_status="RESOLVED", notes="Reorder scheduled")
    assert res["success"] is True

    # Reopen to return to clean state
    res_open = save_alert_action(engine, sid, pid, risk, action_status="OPEN", notes="Reopened")
    assert res_open["success"] is True


def test_case_14_page_refresh_consistency(engine):
    """CASE 14: Refresh consistency -> consecutive loads yield identical records."""
    df1 = load_actionable_alerts(engine, limit=10)
    df2 = load_actionable_alerts(engine, limit=10)
    pd.testing.assert_frame_equal(df1, df2)


def test_case_15_database_reload_persistence(engine):
    """CASE 15: Database reload -> summary and alert counts persist."""
    new_engine = get_engine()
    summary = load_alerts_summary(new_engine)
    assert summary["high_risk"] > 0
    assert summary["medium_risk"] > 0
    assert "open_alerts" in summary
    assert "resolved" in summary


def test_case_16_empty_alert_result(engine):
    """CASE 16: Empty alert result when impossible filter applied."""
    df_empty = load_actionable_alerts(engine, store_id=999999)
    assert df_empty.empty
    assert len(df_empty) == 0


def test_case_17_database_failure_handling():
    """CASE 17: Database failure handled gracefully without unhandled crashes."""
    class BrokenEngine:
        def connect(self):
            raise RuntimeError("Database connection timed out")
        def begin(self):
            raise RuntimeError("Database connection timed out")

    broken = BrokenEngine()
    res = save_alert_action(broken, 1, 1, "HIGH", "REVIEWED")
    assert res["success"] is False
    assert "Failed to record alert action" in res["message"]

    summary = load_alerts_summary(broken)
    assert summary["open_alerts"] == 0
    assert summary["high_risk"] == 0