# ============================================================
# SMARTSTOCK AI — PHASE 3 PRODUCT 360 TESTS
# tests/test_phase3_products.py
# ============================================================

import pytest
import pandas as pd
import sys
from pathlib import Path

# Add streamlit directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "streamlit"))

from db_connection import get_engine
from data_loader import (
    load_product_recommendations,
    load_product_forecast_trend,
    load_stores_for_product,
    load_store_product_forecast
)


@pytest.fixture(scope="module")
def engine():
    return get_engine()


def test_load_product_recommendations(engine):
    """Verify catalog recommendations contain 865 SKUs with proper metrics."""
    df = load_product_recommendations(engine)
    assert not df.empty
    assert len(df) == 865
    assert "product_id" in df.columns
    assert "total_sales" in df.columns
    assert "predicted_sales" in df.columns
    assert "avg_reorder_qty" in df.columns
    assert "high_risk_pct" in df.columns


def test_load_product_forecast_trend(engine):
    """Verify trend aggregation across network for a product."""
    df = load_product_forecast_trend(engine, 267)
    assert not df.empty
    assert "dt" in df.columns
    assert "actual_sales" in df.columns
    assert "predicted_sales" in df.columns
    assert "recommended_reorder_qty" in df.columns
    assert df["dt"].is_monotonic_increasing


def test_load_stores_for_product(engine):
    """Verify store listing for product SKU 267."""
    stores = load_stores_for_product(engine, 267)
    assert isinstance(stores, list)
    assert len(stores) > 0
    assert all(isinstance(s, int) for s in stores)
    assert 631 in stores
    assert stores == sorted(stores)


def test_load_store_product_forecast(engine):
    """Verify store-specific forecast includes replenishment_priority and risk_explanation."""
    df = load_store_product_forecast(engine, 631, 267)
    assert not df.empty
    assert "dt" in df.columns
    assert "actual_sales" in df.columns
    assert "predicted_sales" in df.columns
    assert "stockout_risk" in df.columns
    assert "replenishment_priority" in df.columns
    assert "recommended_reorder_qty" in df.columns
    assert "risk_explanation" in df.columns
    latest = df.iloc[-1]
    assert pd.notna(latest["risk_explanation"])
    assert len(str(latest["risk_explanation"]).strip()) > 0


def test_store_product_forecast_invalid(engine):
    """Verify empty dataframe is returned gracefully for invalid store/product."""
    df = load_store_product_forecast(engine, 999999, 999999)
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_product_risk_classification(engine):
    """Verify the 3-tier risk logic produces valid categories."""
    df = load_product_recommendations(engine)
    good = df[df["high_risk_pct"] < 20]
    attention = df[(df["high_risk_pct"] >= 20) & (df["high_risk_pct"] < 50)]
    action_req = df[df["high_risk_pct"] >= 50]
    
    assert len(good) > 0
    assert len(attention) > 0
    assert len(action_req) > 0
    assert len(good) + len(attention) + len(action_req) == len(df)
