"""
SmartStock AI — Phase 11: AI Inventory Assistant Automated Tests
================================================================
Verifies all 17 test cases specified in Step 23 of Part 11:
1. Why is a product at risk?
2. Which products need attention?
3. Which stores need attention?
4. How much should I reorder?
5. Why was a reorder recommended?
6. High-risk query
7. Product that exists
8. Product that does not exist
9. Store that exists
10. Store that does not exist
11. Missing data handling
12. Database error handling
13. Unrelated question
14. Navigation to Product 360
15. Navigation to Store 360
16. Navigation to Replenishment
17. Page refresh / query stability
================================================================
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add streamlit directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "streamlit"))

from db_connection import get_engine
from ai_assistant import answer_question, extract_product_id, extract_store_id, is_unrelated_question, is_unsupported_inventory_query


@pytest.fixture(scope="session")
def engine():
    return get_engine()


class TestPhase11AIAssistant:

    # 1. Why is a product at risk?
    def test_case_01_why_is_product_at_risk(self, engine):
        res = answer_question(engine, "Why is SKU 267 at Store 631 at high risk?")
        assert res["answer"]
        assert "SKU 267" in res["answer"]
        assert "Store 631" in res["answer"]
        assert "Risk" in res["answer"]
        assert "Suggested reorder:" in res["answer"]
        assert not res["data"].empty
        assert "Stockout Risk" in res["data"].columns

    # 2. Which products need attention?
    def test_case_02_which_products_need_attention(self, engine):
        res = answer_question(engine, "Which products need attention?")
        assert "Products needing attention:" in res["answer"]
        assert "SKU" in res["answer"]
        assert not res["data"].empty
        assert len(res["data"]) <= 5
        assert "Expected Demand" in res["data"].columns

    # 3. Which stores need attention?
    def test_case_03_which_stores_need_attention(self, engine):
        res = answer_question(engine, "Which stores need attention?")
        assert "needs attention because it has a high number of high-risk products" in res["answer"]
        assert "Store" in res["answer"]
        assert not res["data"].empty
        assert "High Risk Products" in res["data"].columns

    # 4. How much should I reorder?
    def test_case_04_how_much_should_i_reorder(self, engine):
        res = answer_question(engine, "How much should I reorder?")
        assert "Based on the current recommendation, the suggested reorder quantity is" in res["answer"]
        assert "units" in res["answer"]
        assert not res["data"].empty

    # 5. Why was a reorder recommended?
    def test_case_05_why_was_reorder_recommended(self, engine):
        res = answer_question(engine, "Why was this reorder recommended for SKU 267?")
        assert "recommended" in res["answer"].lower()
        assert "SKU 267" in res["answer"]
        assert not res["data"].empty

    # 6. High-risk query
    def test_case_06_high_risk_query(self, engine):
        res = answer_question(engine, "Show high-risk products")
        assert "Products needing attention:" in res["answer"]
        assert not res["data"].empty
        # Verify only high risk
        assert (res["data"]["Stockout Risk"] == "High Risk").all()

    # 7. Product that exists
    def test_case_07_product_that_exists(self, engine):
        res = answer_question(engine, "Explain risk for SKU 0")
        assert "SKU 0" in res["answer"]
        assert "could not find" not in res["answer"].lower()

    # 8. Product that does not exist
    def test_case_08_product_does_not_exist(self, engine):
        res = answer_question(engine, "Why is SKU 999999 at risk?")
        assert "I could not find that product/store in the current data." in res["answer"]
        assert res["data"].empty

    # 9. Store that exists
    def test_case_09_store_that_exists(self, engine):
        res = answer_question(engine, "Show risk for Store 0")
        assert "could not find" not in res["answer"].lower()

    # 10. Store that does not exist
    def test_case_10_store_does_not_exist(self, engine):
        res = answer_question(engine, "Why is Store 999999 at risk?")
        assert "I could not find that product/store in the current data." in res["answer"]
        assert res["data"].empty

    # 11. Missing data / Insufficient data
    def test_case_11_missing_data_handling(self, engine):
        res = answer_question(engine, "What is the replenishment strategy for unknown item?")
        assert "I do not have enough data to answer that" in res["answer"]

    # 12. Database error handling
    def test_case_12_database_error_handling(self):
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = Exception("Database connection lost")
        res = answer_question(mock_engine, "Which products need attention?")
        assert res["answer"] == "I could not access the inventory data right now."

    # 13. Unrelated question
    def test_case_13_unrelated_question(self, engine):
        # Weather
        res1 = answer_question(engine, "What is the weather today?")
        assert res1["answer"] == "I can help with SmartStock inventory data, risks, demand and replenishment recommendations."
        assert res1["data"].empty

        # Joke
        res2 = answer_question(engine, "Tell me a joke")
        assert res2["answer"] == "I can help with SmartStock inventory data, risks, demand and replenishment recommendations."

        # President
        res3 = answer_question(engine, "Who is the president?")
        assert res3["answer"] == "I can help with SmartStock inventory data, risks, demand and replenishment recommendations."

    # 14. Navigation to Product 360 state
    def test_case_14_navigation_product_360_state(self, engine):
        res = answer_question(engine, "Why is SKU 267 at Store 631 at high risk?")
        assert res["product_id"] == 267
        assert res["store_id"] == 631

    # 15. Navigation to Store 360 state
    def test_case_15_navigation_store_360_state(self, engine):
        res = answer_question(engine, "Which stores need attention?")
        assert res["store_id"] is not None
        assert res["store_id"] == 417

    # 16. Navigation to Replenishment state
    def test_case_16_navigation_replenishment_state(self, engine):
        res = answer_question(engine, "How much should I reorder for SKU 267 at Store 631?")
        assert res["product_id"] == 267
        assert res["store_id"] == 631

    # 17. Page refresh / query stability
    def test_case_17_page_refresh_stability(self, engine):
        q = "Which products need attention?"
        res1 = answer_question(engine, q)
        res2 = answer_question(engine, q)
        assert res1["answer"] == res2["answer"]
        assert len(res1["data"]) == len(res2["data"])
