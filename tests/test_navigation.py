"""
test_navigation.py
==================
Tests for cross-page navigation, sidebar radio synchronization,
and ensuring StreamlitWidgetAlreadyInstantiatedError cannot occur
when switching pages via action buttons.
"""

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest


PAGES = [
    "Dashboard",
    "Products",
    "Stores",
    "Demand & Forecast",
    "Inventory Risk",
    "Replenishment",
    "Add Inventory Data",
    "AI Inventory Assistant",
]

NAVIGATION_APP_CODE = """
import streamlit as st

PAGES = [
    "Dashboard",
    "Products",
    "Stores",
    "Demand & Forecast",
    "Inventory Risk",
    "Replenishment",
    "Add Inventory Data",
    "AI Inventory Assistant",
]

if "nav_page" not in st.session_state or st.session_state["nav_page"] not in PAGES:
    st.session_state["nav_page"] = PAGES[0]

# Synchronize sidebar radio with nav_page state before widget instantiation
st.session_state["sidebar_nav_radio"] = st.session_state["nav_page"]

def _on_nav_change():
    st.session_state["nav_page"] = st.session_state["sidebar_nav_radio"]

page = st.sidebar.radio(
    "Navigate",
    PAGES,
    key="sidebar_nav_radio",
    on_change=_on_nav_change,
    label_visibility="collapsed",
)

st.write(f"Active Page: {page}")

if page == "Products":
    target_sid = 631
    if st.button("Review Recommendation", type="primary", key="btn_review_rec"):
        st.session_state["nav_page"] = "Replenishment"
        if target_sid is not None:
            st.session_state["repl_store_filter"] = f"Store {target_sid}"
        else:
            st.session_state["repl_store_filter"] = "All Stores"
        st.rerun()

elif page == "Stores":
    target_pid = 267
    if st.button("View Product", key="btn_vp_store_prod"):
        st.session_state["nav_page"] = "Products"
        st.session_state["analyzed_product_id"] = target_pid
        st.rerun()

elif page == "Demand & Forecast":
    if st.button("View Inventory Risk", key="btn_fc_risk"):
        st.session_state["nav_page"] = "Inventory Risk"
        st.rerun()

elif page == "Replenishment":
    st.write(f"Replenishment store: {st.session_state.get('repl_store_filter', 'All Stores')}")
"""


class TestNavigation:
    """Validate that sidebar radio and programmatic button navigation work seamlessly."""

    def test_default_page_is_dashboard(self):
        at = AppTest.from_string(NAVIGATION_APP_CODE)
        at.run()
        assert at.session_state["nav_page"] == "Dashboard"
        assert at.sidebar.radio[0].value == "Dashboard"
        assert len(at.exception) == 0

    def test_sidebar_radio_selection(self):
        at = AppTest.from_string(NAVIGATION_APP_CODE)
        at.run()
        at.sidebar.radio[0].set_value("Products").run()
        assert at.session_state["nav_page"] == "Products"
        assert at.sidebar.radio[0].value == "Products"
        assert len(at.exception) == 0

    def test_review_recommendation_button_navigation(self):
        """Simulate the exact button from Product 360 (line 1563) that previously caused StreamlitWidgetAlreadyInstantiatedError."""
        at = AppTest.from_string(NAVIGATION_APP_CODE)
        at.run()
        # Go to Products page
        at.sidebar.radio[0].set_value("Products").run()
        assert at.session_state["nav_page"] == "Products"

        # Click Review Recommendation
        at.button[0].click().run()
        assert len(at.exception) == 0, f"Exception occurred: {at.exception}"
        assert at.session_state["nav_page"] == "Replenishment"
        assert at.sidebar.radio[0].value == "Replenishment"
        assert at.session_state["repl_store_filter"] == "Store 631"

    def test_view_product_from_store_page(self):
        """Simulate cross-page navigation from Stores to Products."""
        at = AppTest.from_string(NAVIGATION_APP_CODE)
        at.run()
        at.sidebar.radio[0].set_value("Stores").run()
        assert at.session_state["nav_page"] == "Stores"

        at.button[0].click().run()
        assert len(at.exception) == 0
        assert at.session_state["nav_page"] == "Products"
        assert at.sidebar.radio[0].value == "Products"
        assert at.session_state["analyzed_product_id"] == 267

    def test_view_risk_from_forecast_page(self):
        """Simulate cross-page navigation from Demand & Forecast to Inventory Risk."""
        at = AppTest.from_string(NAVIGATION_APP_CODE)
        at.run()
        at.sidebar.radio[0].set_value("Demand & Forecast").run()
        assert at.session_state["nav_page"] == "Demand & Forecast"

        at.button[0].click().run()
        assert len(at.exception) == 0
        assert at.session_state["nav_page"] == "Inventory Risk"
        assert at.sidebar.radio[0].value == "Inventory Risk"

    def test_sidebar_navigate_to_add_inventory_data(self):
        """Verify direct sidebar navigation to Add Inventory Data."""
        at = AppTest.from_string(NAVIGATION_APP_CODE)
        at.run()
        at.sidebar.radio[0].set_value("Add Inventory Data").run()
        assert at.session_state["nav_page"] == "Add Inventory Data"
        assert at.sidebar.radio[0].value == "Add Inventory Data"
        assert len(at.exception) == 0

    def test_sanitizer_defaults_invalid_page(self):
        """Ensure invalid or stale pages redirect cleanly to Dashboard."""
        code_with_invalid_init = """
import streamlit as st
PAGES = ['Dashboard', 'Products', 'Stores', 'Demand & Forecast', 'Inventory Risk', 'Replenishment', 'Add Inventory Data', 'AI Inventory Assistant']

st.session_state['nav_page'] = 'InvalidPage'
if 'nav_page' not in st.session_state or st.session_state['nav_page'] not in PAGES:
    st.session_state['nav_page'] = PAGES[0]

st.session_state['sidebar_nav_radio'] = st.session_state['nav_page']
assert st.session_state['nav_page'] == 'Dashboard'
assert st.session_state['sidebar_nav_radio'] == 'Dashboard'
st.write('Sanitized successfully')
"""
        at = AppTest.from_string(code_with_invalid_init)
        at.run()
        assert len(at.exception) == 0
        assert at.session_state["nav_page"] == "Dashboard"
