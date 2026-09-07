# ============================================================
# SMARTSTOCK AI — PHASE 4 STORES TESTS
# tests/test_phase4_stores.py
# ============================================================

import pytest
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "streamlit"))

from db_connection import get_engine
from data_loader import (
    load_store_recommendations,
    load_store_forecast_trend,
    load_forecast_recommendations
)


@pytest.fixture(scope="module")
def engine():
    return get_engine()


def test_load_store_recommendations(engine):
    """Verify store recommendations table contains 898 stores."""
    df = load_store_recommendations(engine)
    assert not df.empty
    assert len(df) == 898
    assert "store_id" in df.columns
    assert "products" in df.columns
    assert "predicted_sales" in df.columns
    assert "high_risk_products" in df.columns
    assert "urgent_reorders" in df.columns
    assert "high_risk_pct" in df.columns


def test_load_store_forecast_trend(engine):
    """Verify daily forecast trend for Store 417 and Store 631."""
    df = load_store_forecast_trend(engine, 417)
    assert not df.empty
    assert "dt" in df.columns
    assert "actual_sales" in df.columns
    assert "predicted_sales" in df.columns
    assert "recommended_reorder_qty" in df.columns
    assert df["dt"].is_monotonic_increasing

    df631 = load_store_forecast_trend(engine, 631)
    assert not df631.empty
    assert len(df631) == 6


def test_store_forecast_trend_invalid(engine):
    """Verify invalid store returns empty dataframe gracefully."""
    df = load_store_forecast_trend(engine, 999999)
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_store_products_needing_attention(engine):
    """Verify products needing attention can be extracted and deduplicated for a store."""
    recs = load_forecast_recommendations(engine, store_id=417, limit=50)
    assert not recs.empty
    top5 = recs.drop_duplicates(subset=["product_id"]).head(5)
    assert len(top5) <= 5
    for _, r in top5.iterrows():
        assert r["product_id"] is not None
        assert float(r["predicted_sales"]) >= 0
        assert r["stockout_risk"] in ["HIGH", "MEDIUM", "LOW"]


def test_store_risk_classification(engine):
    """Verify the 3-tier risk logic produces valid categories across 898 stores."""
    df = load_store_recommendations(engine)
    good = df[df["high_risk_pct"] < 10]
    attention = df[(df["high_risk_pct"] >= 10) & (df["high_risk_pct"] < 15)]
    action_req = df[df["high_risk_pct"] >= 15]

    assert len(good) == 564
    assert len(attention) == 288
    assert len(action_req) == 46
    assert len(good) + len(attention) + len(action_req) == len(df)
