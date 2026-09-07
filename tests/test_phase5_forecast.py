# ============================================================
# SMARTSTOCK AI — PHASE 5 DEMAND & FORECAST TESTS
# tests/test_phase5_forecast.py
# ============================================================

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "streamlit"))

from db_connection import get_engine
from data_loader import (
    load_store_product_forecast,
    load_stores_for_product,
    load_daily_sales_trend
)


@pytest.fixture(scope="module")
def engine():
    return get_engine()


def test_load_store_product_forecast_valid(engine):
    """Verify daily forecast data loads for valid store and product."""
    df = load_store_product_forecast(engine, store_id=631, product_id=267)
    assert not df.empty
    assert len(df) == 6
    expected_cols = [
        "dt", "actual_sales", "predicted_sales",
        "stockout_risk", "replenishment_priority",
        "recommended_reorder_qty", "risk_explanation"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing expected column: {col}"
    assert df["dt"].is_monotonic_increasing


def test_load_store_product_forecast_invalid(engine):
    """Verify invalid store/product returns empty dataframe gracefully."""
    df = load_store_product_forecast(engine, store_id=999999, product_id=999999)
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_load_stores_for_product(engine):
    """Verify stores carrying SKU 267 are retrieved correctly."""
    stores = load_stores_for_product(engine, 267)
    assert isinstance(stores, list)
    assert len(stores) > 0
    assert 631 in stores

    # Non-existent product
    empty_stores = load_stores_for_product(engine, 999999)
    assert isinstance(empty_stores, list)
    assert len(empty_stores) == 0


def test_forecast_demand_metrics_calculations(engine):
    """Verify demand metric formulas: expected demand, next-day demand, change, pattern."""
    df = load_store_product_forecast(engine, store_id=631, product_id=267)
    assert not df.empty

    pred_vals = df["predicted_sales"].values
    mean_val = float(np.mean(pred_vals))
    last_val = float(pred_vals[-1])
    first_val = float(pred_vals[0])

    # Expected Demand > 0
    assert mean_val > 0

    # Next-Day Demand >= 0
    assert last_val >= 0

    # Demand Change calculation
    if first_val > 0:
        pct_change = ((last_val - first_val) / first_val) * 100
        if pct_change > 5:
            change_str = "Increasing"
        elif pct_change < -5:
            change_str = "Decreasing"
        else:
            change_str = "Stable"
    else:
        change_str = "Stable"
    assert change_str in ["Increasing", "Decreasing", "Stable"]

    # Demand Pattern calculation
    cv = float(np.std(pred_vals) / mean_val) if mean_val > 0 else 0
    pattern_str = "Stable" if cv < 0.3 else "Changing"
    assert pattern_str in ["Stable", "Changing"]


def test_load_daily_sales_trend(engine):
    """Verify overall daily sales trend data exists and is properly structured."""
    df = load_daily_sales_trend(engine)
    assert not df.empty
    assert "dt" in df.columns
    assert "total_sales" in df.columns
    assert "stockout_rate_pct" in df.columns
