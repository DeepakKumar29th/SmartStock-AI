"""
SmartStock AI — Phase 10: Add Inventory Data Automated Tests
=============================================================
Verifies all 15 test cases specified in Step 19 of Part 10:
1. Valid record insertion
2. Missing date validation
3. Missing store validation
4. Missing product validation
5. Negative sales blocked
6. Invalid discount blocked (>100 or <0)
7. Invalid date (future date rejection)
8. Duplicate date + store + product protection
9. Optional manager notes (handles both present and empty)
10. Database unavailable error handling
11. Successful insertion directly in PostgreSQL
12. Recent records refresh
13. Newly saved record appears at top (sorting by updated_at/created_at DESC)
14. Page reload persistence
15. Existing pages still work without disruption
=============================================================
"""

import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Add streamlit directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "streamlit"))

load_dotenv(Path(__file__).parent.parent / ".env")

from db_connection import get_engine
from data_loader import (
    check_inventory_update_exists,
    save_inventory_update,
    load_recent_inventory_updates,
    load_inventory_update_summary,
    load_stores_catalog,
    load_products_catalog,
)


@pytest.fixture(scope="session")
def engine():
    return get_engine()


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_records(engine):
    """Clean up test records before and after testing session."""
    test_dt = date(2026, 9, 6)
    test_store = 0
    test_sku = 0
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM app.inventory_updates WHERE dt = :dt AND store_id = :s AND product_id = :p"),
            {"dt": test_dt, "s": test_store, "p": test_sku},
        )
    yield
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM app.inventory_updates WHERE dt = :dt AND store_id = :s AND product_id = :p"),
            {"dt": test_dt, "s": test_store, "p": test_sku},
        )


class TestPhase10AddInventoryData:
    TEST_DT = date.today()
    TEST_STORE = 0
    TEST_SKU = 0

    # 1. Valid record
    def test_case_01_valid_record(self, engine):
        res = save_inventory_update(
            engine=engine,
            dt=self.TEST_DT,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            sale_amount=42.5,
            stock_status="In Stock",
            discount=10.0,
            holiday_flag=0,
            activity_flag=1,
            notes="Test entry for Phase 10 verification",
        )
        assert res["success"] is True
        assert res["update_id"] is not None
        assert "successfully" in res["message"].lower()

    # 2. Missing date
    def test_case_02_missing_date(self, engine):
        res = save_inventory_update(
            engine=engine,
            dt=None,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            sale_amount=10.0,
            stock_status="In Stock",
        )
        assert res["success"] is False
        assert "date is required" in res["message"].lower()

    # 3. Missing store
    def test_case_03_missing_store(self, engine):
        res = save_inventory_update(
            engine=engine,
            dt=self.TEST_DT,
            store_id=None,
            product_id=self.TEST_SKU,
            sale_amount=10.0,
            stock_status="In Stock",
        )
        assert res["success"] is False
        assert "store" in res["message"].lower()

    # 4. Missing product
    def test_case_04_missing_product(self, engine):
        res = save_inventory_update(
            engine=engine,
            dt=self.TEST_DT,
            store_id=self.TEST_STORE,
            product_id=None,
            sale_amount=10.0,
            stock_status="In Stock",
        )
        assert res["success"] is False
        assert "sku" in res["message"].lower() or "product" in res["message"].lower()

    # 5. Negative sales
    def test_case_05_negative_sales_blocked(self, engine):
        res = save_inventory_update(
            engine=engine,
            dt=self.TEST_DT,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            sale_amount=-5.0,
            stock_status="In Stock",
        )
        assert res["success"] is False
        assert "cannot be negative" in res["message"].lower()

    # 6. Invalid discount
    def test_case_06_invalid_discount_blocked(self, engine):
        # Above 100%
        res1 = save_inventory_update(
            engine=engine,
            dt=self.TEST_DT,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            sale_amount=10.0,
            stock_status="In Stock",
            discount=105.0,
        )
        assert res1["success"] is False
        assert "discount" in res1["message"].lower()

        # Negative discount
        res2 = save_inventory_update(
            engine=engine,
            dt=self.TEST_DT,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            sale_amount=10.0,
            stock_status="In Stock",
            discount=-10.0,
        )
        assert res2["success"] is False
        assert "discount" in res2["message"].lower()

    # 7. Invalid date (future date check in validation)
    def test_case_07_invalid_future_date_logic(self, engine):
        tomorrow = date.today() + timedelta(days=1)
        res = save_inventory_update(
            engine=engine,
            dt=tomorrow,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            sale_amount=10.0,
            stock_status="In Stock",
        )
        assert res["success"] is False
        assert "future" in res["message"].lower()

    # 8. Duplicate date + store + product protection
    def test_case_08_duplicate_protection(self, engine):
        # First ensure row exists
        save_inventory_update(
            engine=engine,
            dt=self.TEST_DT,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            sale_amount=15.0,
            stock_status="Low Stock",
        )
        # Check duplicate existence
        exists = check_inventory_update_exists(engine, self.TEST_DT, self.TEST_STORE, self.TEST_SKU)
        assert exists is True, "Expected duplicate check to return True"

        # Check non-existent record returns False
        non_existent = check_inventory_update_exists(engine, date(2020, 1, 1), 9999, 9999)
        assert non_existent is False, "Expected non-existent check to return False"

    # 9. Optional manager notes
    def test_case_09_optional_manager_notes(self, engine):
        # Empty notes
        res_empty = save_inventory_update(
            engine=engine,
            dt=self.TEST_DT,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            sale_amount=20.0,
            stock_status="In Stock",
            notes="",
        )
        assert res_empty["success"] is True

        # With notes
        res_notes = save_inventory_update(
            engine=engine,
            dt=self.TEST_DT,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            sale_amount=22.0,
            stock_status="In Stock",
            notes="Morning shipment arrived on time.",
        )
        assert res_notes["success"] is True

    # 10. Database unavailable
    def test_case_10_database_unavailable_handling(self):
        mock_engine = MagicMock()
        mock_engine.begin.side_effect = Exception("could not connect to server: Connection refused")
        res = save_inventory_update(
            engine=mock_engine,
            dt=self.TEST_DT,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            sale_amount=10.0,
            stock_status="In Stock",
        )
        assert res["success"] is False
        assert "could not save the record. please check the database connection." in res["message"].lower()

    # 11. Successful insertion directly in PostgreSQL
    def test_case_11_successful_insertion_postgres(self, engine):
        res = save_inventory_update(
            engine=engine,
            dt=self.TEST_DT,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            sale_amount=55.0,
            stock_status="Out of Stock",
            discount=5.0,
            holiday_flag=1,
            activity_flag=0,
            notes="Direct SQL verification test row",
        )
        assert res["success"] is True

        with engine.connect() as conn:
            row = conn.execute(
                text("""
                    SELECT sale_amount, stock_status, discount, holiday_flag, activity_flag, notes
                    FROM app.inventory_updates
                    WHERE dt = :dt AND store_id = :s AND product_id = :p
                """),
                {"dt": self.TEST_DT, "s": self.TEST_STORE, "p": self.TEST_SKU},
            ).fetchone()

        assert row is not None
        assert float(row[0]) == 55.0
        assert row[1] == "Out of Stock"
        assert float(row[2]) == 5.0
        assert row[3] == 1
        assert row[4] == 0
        assert "Direct SQL verification" in row[5]

    # 12. Recent records refresh
    def test_case_12_recent_records_refresh(self, engine):
        df = load_recent_inventory_updates(engine, limit=10)
        assert not df.empty
        assert len(df) <= 10
        assert "update_id" in df.columns
        assert "dt" in df.columns
        assert "store_id" in df.columns
        assert "product_id" in df.columns

    # 13. Newly saved record appears at top
    def test_case_13_newly_saved_record_appears_first(self, engine):
        # Update test record right now
        res = save_inventory_update(
            engine=engine,
            dt=self.TEST_DT,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            sale_amount=99.0,
            stock_status="In Stock",
            notes="Timestamp ordering test",
        )
        assert res["success"] is True

        df = load_recent_inventory_updates(engine, limit=10)
        assert not df.empty
        # The top record should have update_id matching our newly saved record
        top_row = df.iloc[0]
        assert top_row["update_id"] == res["update_id"]
        assert top_row["store_id"] == self.TEST_STORE
        assert top_row["product_id"] == self.TEST_SKU

    # 14. Page reload persistence
    def test_case_14_page_reload_persistence(self, engine):
        # Create separate connection to simulate fresh session / reload
        eng2 = get_engine()
        df_fresh = load_recent_inventory_updates(eng2, limit=10)
        matching = df_fresh[
            (df_fresh["dt"] == self.TEST_DT)
            & (df_fresh["store_id"] == self.TEST_STORE)
            & (df_fresh["product_id"] == self.TEST_SKU)
        ]
        assert not matching.empty, "Record must persist in separate database session"
        eng2.dispose()

    # 15. Existing pages still work
    def test_case_15_existing_pages_regression(self, engine):
        with engine.connect() as conn:
            # Check dim_store and dim_product (catalogs)
            stores_cnt = conn.execute(text("SELECT COUNT(*) FROM core.dim_store")).scalar()
            products_cnt = conn.execute(text("SELECT COUNT(*) FROM core.dim_product")).scalar()
            assert stores_cnt > 0
            assert products_cnt > 0

            # Check ML forecast tables
            fc_cnt = conn.execute(text("SELECT COUNT(*) FROM ml.forecast_recommendations")).scalar()
            assert fc_cnt > 0

            # Check daily sales (daily_sales_trend in cloud or fact_daily_sales locally)
            is_cloud = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'core' AND table_name = 'daily_sales_trend'")).scalar() > 0
            if is_cloud:
                sales_cnt = conn.execute(text("SELECT COUNT(*) FROM core.daily_sales_trend")).scalar()
            else:
                sales_cnt = conn.execute(text("SELECT COUNT(*) FROM core.fact_daily_sales")).scalar()
            assert sales_cnt > 0

            # Check replenishment & alerts tables
            repl_cnt = conn.execute(text("SELECT COUNT(*) FROM app.replenishment_decisions")).scalar()
            alert_cnt = conn.execute(text("SELECT COUNT(*) FROM app.alert_actions")).scalar()
            assert repl_cnt >= 0
            assert alert_cnt >= 0

    # 16. Today's date accepted dynamically (not hard-coded)
    def test_case_16_today_date_dynamic_accepted(self, engine):
        current_today = date.today()
        res = save_inventory_update(
            engine=engine,
            dt=current_today,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            sale_amount=88.5,
            stock_status="In Stock",
            notes="Dynamic current date verification",
        )
        assert res["success"] is True
        assert res["update_id"] is not None

    # 17. Real-time read-after-write from Neon
    def test_case_17_read_after_write_immediate(self, engine):
        current_today = date.today()
        save_res = save_inventory_update(
            engine=engine,
            dt=current_today,
            store_id=self.TEST_STORE,
            product_id=self.TEST_SKU,
            sale_amount=99.0,
            stock_status="Low Stock",
            notes="Immediate query back check",
        )
        assert save_res["success"] is True

        df = load_recent_inventory_updates(engine, limit=10)
        assert not df.empty
        matching = df[
            (df["dt"] == current_today)
            & (df["store_id"] == self.TEST_STORE)
            & (df["product_id"] == self.TEST_SKU)
        ]
        assert not matching.empty, "Newly inserted record must be immediately queryable"
        assert float(matching.iloc[0]["sale_amount"]) == 99.0
        assert matching.iloc[0]["stock_status"] == "Low Stock"

    # 18. Timestamp stored correctly in PostgreSQL
    def test_case_18_timestamp_stored_correctly(self, engine):
        current_today = date.today()
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT created_at, updated_at
                FROM app.inventory_updates
                WHERE dt = :dt AND store_id = :store_id AND product_id = :product_id
            """), {
                "dt": current_today,
                "store_id": self.TEST_STORE,
                "product_id": self.TEST_SKU
            }).fetchone()
            assert row is not None, "Record must exist in database"
            ts = row[1] or row[0]
            assert ts is not None, "Timestamp must not be null"

