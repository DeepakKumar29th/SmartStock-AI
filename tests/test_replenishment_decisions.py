# ============================================================
# SMARTSTOCK AI — Test Suite: Replenishment Decisions & Actions
# tests/test_replenishment_decisions.py
# ============================================================

import pytest
from datetime import date
import sys
from pathlib import Path

# Add project root and streamlit directory
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "streamlit"))

from db_connection import get_engine
from data_loader import (
    save_replenishment_decision,
    load_recent_replenishment_decisions,
    load_replenishment_decision_summary,
    save_alert_action,
    load_alert_actions
)

@pytest.fixture(scope="module")
def engine():
    return get_engine()

def test_save_and_update_replenishment_decision(engine):
    """Test saving a new approval decision and updating it via upsert."""
    today = date.today()
    test_store = 0
    test_prod = 1

    # 1. Save initial approval
    res1 = save_replenishment_decision(
        engine=engine,
        store_id=test_store,
        product_id=test_prod,
        recommended_qty=140.0,
        approved_qty=140.0,
        decision_status="APPROVED",
        notes="Automated test approval",
        decided_by="Test Runner",
        decision_date=today
    )
    assert res1["success"] is True
    assert res1["decision_id"] is not None

    # 2. Modify decision (upsert)
    res2 = save_replenishment_decision(
        engine=engine,
        store_id=test_store,
        product_id=test_prod,
        recommended_qty=140.0,
        approved_qty=160.0,
        decision_status="MODIFIED",
        notes="Automated test modified to 160 units",
        decided_by="Test Runner",
        decision_date=today
    )
    assert res2["success"] is True
    assert res2["is_new"] is False
    assert res2["decision_id"] == res1["decision_id"]

def test_load_recent_replenishment_decisions(engine):
    """Verify loading recent decisions returns expected DataFrame columns."""
    df = load_recent_replenishment_decisions(engine, limit=10)
    assert not df.empty
    expected_cols = [
        "decision_id", "decision_date", "store_id", "product_id",
        "recommended_qty", "approved_qty", "decision_status", "decision_notes"
    ]
    for col in expected_cols:
        assert col in df.columns

def test_load_replenishment_decision_summary(engine):
    """Verify summary KPIs dictionary returns non-negative counts."""
    summary = load_replenishment_decision_summary(engine)
    assert "total_decisions" in summary
    assert "approved_count" in summary
    assert "total_approved_units" in summary
    assert summary["total_decisions"] >= 1
    assert summary["total_approved_units"] > 0

def test_invalid_replenishment_decision_status(engine):
    """Verify rejection of invalid status."""
    res = save_replenishment_decision(
        engine=engine,
        store_id=0,
        product_id=1,
        recommended_qty=50.0,
        approved_qty=50.0,
        decision_status="INVALID_STATUS"
    )
    assert res["success"] is False

def test_save_and_load_alert_action(engine):
    """Verify alert status tracking upsert and retrieval."""
    test_store = 0
    test_prod = 1
    res = save_alert_action(
        engine=engine,
        store_id=test_store,
        product_id=test_prod,
        alert_severity="HIGH",
        action_status="ACKNOWLEDGED",
        notes="Reviewed by automated test"
    )
    assert res["success"] is True

    alerts_df = load_alert_actions(engine)
    assert not alerts_df.empty
    assert "action_status" in alerts_df.columns
    matched = alerts_df[(alerts_df["store_id"] == test_store) & (alerts_df["product_id"] == test_prod)]
    assert not matched.empty
    assert matched.iloc[0]["action_status"] == "ACKNOWLEDGED"
