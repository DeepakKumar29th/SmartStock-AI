# ============================================================
# SMARTSTOCK AI — PHASE 6 INVENTORY RISK TESTS
# tests/test_phase6_inventory_risk.py
# ============================================================

import pytest
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "streamlit"))

from db_connection import get_engine
from data_loader import (
    load_forecast_recommendations,
    load_risk_summary_counts
)


@pytest.fixture(scope="module")
def engine():
    return get_engine()


def test_risk_summary_counts_network(engine):
    """Verify network-wide risk summary counts for latest observation date."""
    counts = load_risk_summary_counts(engine)
    assert isinstance(counts, dict)
    assert "HIGH" in counts
    assert "MEDIUM" in counts
    assert "LOW" in counts
    assert "TOTAL" in counts
    assert counts["TOTAL"] == 50000
    assert counts["HIGH"] > 0
    assert counts["MEDIUM"] > 0
    assert counts["LOW"] > 0


def test_risk_summary_counts_store_and_dept(engine):
    """Verify store-specific and department-specific risk counts."""
    counts_store = load_risk_summary_counts(engine, store_id=631)
    assert counts_store["TOTAL"] > 0
    assert counts_store["HIGH"] + counts_store["MEDIUM"] + counts_store["LOW"] == counts_store["TOTAL"]

    counts_dept = load_risk_summary_counts(engine, department_id=2)
    assert counts_dept["TOTAL"] > 0


def test_filter_high_risk_default(engine):
    """CASE 2: Filter High Risk records."""
    df = load_forecast_recommendations(engine, risk_levels=["HIGH"], latest_only=True, limit=20)
    assert not df.empty
    assert len(df) <= 20
    assert (df["stockout_risk"] == "HIGH").all()
    assert "risk_explanation" in df.columns
    assert "recommended_reorder_qty" in df.columns


def test_filter_medium_risk(engine):
    """CASE 3: Filter Medium Risk records."""
    df = load_forecast_recommendations(engine, risk_levels=["MEDIUM"], latest_only=True, limit=20)
    assert not df.empty
    assert (df["stockout_risk"] == "MEDIUM").all()


def test_filter_low_risk(engine):
    """CASE 4: Filter Low Risk records."""
    df = load_forecast_recommendations(engine, risk_levels=["LOW"], latest_only=True, limit=20)
    assert not df.empty
    assert (df["stockout_risk"] == "LOW").all()


def test_filter_store(engine):
    """CASE 6: Filter by specific store (Store 631)."""
    df = load_forecast_recommendations(engine, store_id=631, latest_only=True, limit=50)
    assert not df.empty
    assert (df["store_id"] == 631).all()


def test_filter_product_and_store(engine):
    """CASE 5: Select specific product and store (SKU 267 @ Store 631)."""
    df = load_forecast_recommendations(engine, store_id=631, product_id=267, latest_only=True)
    assert not df.empty
    assert len(df) == 1
    row = df.iloc[0]
    assert row["store_id"] == 631
    assert row["product_id"] == 267
    assert row["stockout_risk"] == "HIGH"
    assert row["predicted_sales"] > 0
    assert row["recommended_reorder_qty"] > 0
    assert len(str(row["risk_explanation"])) > 10


def test_filter_empty_results(engine):
    """CASE 9: Non-existent store/product returns empty dataframe gracefully."""
    df = load_forecast_recommendations(engine, store_id=999999, latest_only=True)
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_sorting_options(engine):
    """CASE 10: Sorting by reorder qty vs predicted sales vs stockout risk."""
    df_reorder = load_forecast_recommendations(engine, sort_by="recommended_reorder_qty", latest_only=True, limit=10)
    assert df_reorder["recommended_reorder_qty"].is_monotonic_decreasing

    df_sales = load_forecast_recommendations(engine, sort_by="predicted_sales", latest_only=True, limit=10)
    assert df_sales["predicted_sales"].is_monotonic_decreasing
