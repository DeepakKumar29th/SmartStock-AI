"""
SmartStock AI — Operational Inventory Updates Table Tests
============================================================
Tests:
- Schema and table existence
- Column definitions and indexes
- Valid insertion and retrieval
- Foreign key enforcement (store_id, product_id)
- Check constraints (sale_amount >= 0, stock_status, discount 0..100)
- Unique constraint (dt, store_id, product_id)
- Verification that core.fact_daily_sales and ML tables are completely untouched
============================================================
"""

import os
from datetime import date
from pathlib import Path
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

import sys
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "streamlit"))
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT.parent / ".env")

from db_connection import get_engine


@pytest.fixture(scope="session")
def engine():
    eng = get_engine()
    with eng.connect() as conn:
        conn.execute(text("SELECT 1"))
    return eng



class TestOperationalTableStructure:
    def test_app_schema_exists(self, engine):
        with engine.connect() as conn:
            schemas = [
                r[0]
                for r in conn.execute(
                    text("SELECT schema_name FROM information_schema.schemata")
                ).fetchall()
            ]
        assert "app" in schemas, "Schema 'app' does not exist"

    def test_inventory_updates_table_exists(self, engine):
        with engine.connect() as conn:
            count = conn.execute(
                text("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'app' AND table_name = 'inventory_updates'
                """)
            ).scalar()
        assert count == 1, "Table 'app.inventory_updates' does not exist"

    def test_required_columns_exist(self, engine):
        expected_columns = {
            "update_id",
            "dt",
            "store_id",
            "product_id",
            "sale_amount",
            "stock_status",
            "discount",
            "holiday_flag",
            "activity_flag",
            "notes",
            "created_at",
            "updated_at",
        }
        with engine.connect() as conn:
            columns = {
                r[0]
                for r in conn.execute(
                    text("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'app' AND table_name = 'inventory_updates'
                    """)
                ).fetchall()
            }
        missing = expected_columns - columns
        assert not missing, f"Missing columns in app.inventory_updates: {missing}"


class TestOperationalTableConstraints:
    TEST_DT = date(2026, 9, 1)
    TEST_STORE = 0
    TEST_PRODUCT = 0

    def cleanup(self, engine):
        with engine.begin() as conn:
            conn.execute(
                text(
                    "DELETE FROM app.inventory_updates WHERE dt = :dt AND store_id = :s AND product_id = :p"
                ),
                {"dt": self.TEST_DT, "s": self.TEST_STORE, "p": self.TEST_PRODUCT},
            )

    def test_valid_insert_and_retrieval(self, engine):
        self.cleanup(engine)
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO app.inventory_updates (
                        dt, store_id, product_id, sale_amount, stock_status, discount, holiday_flag, activity_flag, notes
                    ) VALUES (
                        :dt, :store_id, :product_id, :sale_amount, :stock_status, :discount, :holiday, :activity, :notes
                    )
                """),
                {
                    "dt": self.TEST_DT,
                    "store_id": self.TEST_STORE,
                    "product_id": self.TEST_PRODUCT,
                    "sale_amount": 25.50,
                    "stock_status": "In Stock",
                    "discount": 5.0,
                    "holiday": 0,
                    "activity": 1,
                    "notes": "Test automated entry",
                },
            )

        with engine.connect() as conn:
            row = conn.execute(
                text("""
                    SELECT sale_amount, stock_status, discount, holiday_flag, activity_flag, notes, created_at
                    FROM app.inventory_updates
                    WHERE dt = :dt AND store_id = :s AND product_id = :p
                """),
                {"dt": self.TEST_DT, "s": self.TEST_STORE, "p": self.TEST_PRODUCT},
            ).fetchone()

        assert row is not None
        assert float(row[0]) == 25.50
        assert row[1] == "In Stock"
        assert float(row[2]) == 5.0
        assert row[3] == 0
        assert row[4] == 1
        assert row[5] == "Test automated entry"
        assert row[6] is not None

        self.cleanup(engine)

    def test_foreign_key_store_rejects_invalid_store(self, engine):
        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO app.inventory_updates (
                            dt, store_id, product_id, sale_amount, stock_status
                        ) VALUES ('2026-09-01', 999999, 0, 10.0, 'In Stock')
                    """)
                )

    def test_foreign_key_product_rejects_invalid_product(self, engine):
        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO app.inventory_updates (
                            dt, store_id, product_id, sale_amount, stock_status
                        ) VALUES ('2026-09-01', 0, 999999, 10.0, 'In Stock')
                    """)
                )

    def test_check_constraint_rejects_negative_sales(self, engine):
        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO app.inventory_updates (
                            dt, store_id, product_id, sale_amount, stock_status
                        ) VALUES ('2026-09-01', 0, 0, -15.0, 'In Stock')
                    """)
                )

    def test_check_constraint_rejects_invalid_stock_status(self, engine):
        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO app.inventory_updates (
                            dt, store_id, product_id, sale_amount, stock_status
                        ) VALUES ('2026-09-01', 0, 0, 10.0, 'InvalidStatus')
                    """)
                )

    def test_check_constraint_rejects_out_of_range_discount(self, engine):
        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO app.inventory_updates (
                            dt, store_id, product_id, sale_amount, stock_status, discount
                        ) VALUES ('2026-09-01', 0, 0, 10.0, 'In Stock', 120.0)
                    """)
                )

    def test_unique_constraint_rejects_duplicate(self, engine):
        self.cleanup(engine)
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO app.inventory_updates (
                        dt, store_id, product_id, sale_amount, stock_status
                    ) VALUES (:dt, :s, :p, 10.0, 'In Stock')
                """),
                {"dt": self.TEST_DT, "s": self.TEST_STORE, "p": self.TEST_PRODUCT},
            )

        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO app.inventory_updates (
                            dt, store_id, product_id, sale_amount, stock_status
                        ) VALUES (:dt, :s, :p, 15.0, 'Low Stock')
                    """),
                    {"dt": self.TEST_DT, "s": self.TEST_STORE, "p": self.TEST_PRODUCT},
                )

        self.cleanup(engine)


class TestHistoricalDataUnchanged:
    def test_fact_daily_sales_untouched(self, engine):
        with engine.connect() as conn:
            is_cloud = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'core' AND table_name = 'daily_sales_trend'")).scalar() > 0
            if is_cloud:
                cnt = conn.execute(text("SELECT COUNT(*) FROM core.daily_sales_trend")).scalar()
                assert cnt == 90, f"Expected 90 cloud daily sales trend rows, found {cnt}"
            else:
                cnt = conn.execute(
                    text("SELECT COUNT(*) FROM core.fact_daily_sales")
                ).scalar()
                assert cnt == 4_500_000, f"Expected 4,500,000 historical rows, found {cnt}"

    def test_ml_recommendations_untouched(self, engine):
        with engine.connect() as conn:
            cnt = conn.execute(
                text("SELECT COUNT(*) FROM ml.forecast_recommendations")
            ).scalar()
        assert cnt == 300_000, f"Expected 300,000 ML rows, found {cnt}"


class TestDataLoaderOperationalFunctions:
    def test_load_catalogs(self, engine):
        import sys
        sys.path.insert(0, str(_ROOT / "streamlit"))
        from data_loader import load_stores_catalog, load_products_catalog

        stores = load_stores_catalog(engine)
        assert not stores.empty
        assert "store_id" in stores.columns
        assert len(stores) == 898

        products = load_products_catalog(engine)
        assert not products.empty
        assert "product_id" in products.columns
        assert len(products) == 865

    def test_save_inventory_update_validation(self, engine):
        import sys
        sys.path.insert(0, str(_ROOT / "streamlit"))
        from data_loader import save_inventory_update

        # Negative sales validation
        res = save_inventory_update(engine, date(2026, 9, 2), 0, 0, -10, "In Stock")
        assert not res["success"]
        assert "negative" in res["message"].lower()

        # Invalid stock status validation
        res = save_inventory_update(engine, date(2026, 9, 2), 0, 0, 10, "Bad Status")
        assert not res["success"]
        assert "stock status" in res["message"].lower()

        # Invalid discount (>100)
        res = save_inventory_update(engine, date(2026, 9, 2), 0, 0, 10, "In Stock", discount=120)
        assert not res["success"]
        assert "discount" in res["message"].lower()

    def test_save_and_upsert_lifecycle(self, engine):
        import sys
        sys.path.insert(0, str(_ROOT / "streamlit"))
        from data_loader import save_inventory_update, load_recent_inventory_updates, load_inventory_update_summary

        test_dt = date(2026, 9, 3)
        store = 5
        product = 12

        # 1. Insert new
        res1 = save_inventory_update(
            engine, test_dt, store, product,
            sale_amount=42.0, stock_status="Low Stock", discount=10.0,
            holiday_flag=1, activity_flag=0, notes="Flash sale"
        )
        assert res1["success"]
        assert res1["is_new"] is True

        # 2. Upsert (update existing on same date/store/product)
        res2 = save_inventory_update(
            engine, test_dt, store, product,
            sale_amount=50.0, stock_status="Out of Stock", discount=15.0,
            holiday_flag=1, activity_flag=1, notes="Flash sale updated"
        )
        assert res2["success"]
        assert res2["is_new"] is False

        # 3. Load recent updates
        recent = load_recent_inventory_updates(engine, limit=5)
        assert not recent.empty
        match = recent[(recent["store_id"] == store) & (recent["product_id"] == product)]
        assert not match.empty
        assert float(match.iloc[0]["sale_amount"]) == 50.0
        assert match.iloc[0]["stock_status"] == "Out of Stock"

        # 4. Summary metrics
        summary = load_inventory_update_summary(engine)
        assert summary["total_records"] >= 1
        assert summary["out_of_stock_count"] >= 1

        # Clean up
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM app.inventory_updates WHERE dt = :dt AND store_id = :s AND product_id = :p"),
                {"dt": test_dt, "s": store, "p": product}
            )
