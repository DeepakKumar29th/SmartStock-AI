# ============================================================
# SMARTSTOCK AI
# streamlit/app.py — Multi-Page Application Entry Point
# ============================================================

import streamlit as st
import sys
from pathlib import Path

# ── page config — MUST be the very first Streamlit call ───────
st.set_page_config(
    page_title="SmartStock AI",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── path setup ─────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

# ── imports ────────────────────────────────────────────────────
import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── global chart theme (warehouse & retail operations palette) ────
pio.templates["smartstock"] = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#0F172A"),
        title=dict(font=dict(size=15, color="#0F172A")),
        xaxis=dict(gridcolor="#E2E8F0", linecolor="#E2E8F0", zerolinecolor="#E2E8F0"),
        yaxis=dict(gridcolor="#E2E8F0", linecolor="#E2E8F0", zerolinecolor="#E2E8F0"),
        colorway=["#2563EB", "#D97706", "#7C3AED", "#DC2626", "#0D9488", "#0284C7",
                  "#EA580C", "#8B5CF6", "#10B981", "#F59E0B"],
        legend=dict(bgcolor="rgba(255,255,255,0.85)", bordercolor="#E2E8F0", borderwidth=1),
        margin=dict(t=50, b=40, l=40, r=20),
    )
)
pio.templates.default = "smartstock"

from db_connection import get_engine
from data_loader   import (
    load_business_kpis, load_store_recommendations,
    load_product_recommendations, load_category_summary,
    load_top20_recommendations, load_forecast_recommendations,
    load_store_product_forecast, load_daily_sales_trend, instacart_available,
    load_instacart_kpis, load_top_products,
    load_top_reorder_products, load_department_summary,
    load_aisle_summary, load_basket_rules,
    load_product_associations, load_unified_intelligence,
    load_stores_catalog, load_products_catalog,
    save_inventory_update, load_recent_inventory_updates,
    load_inventory_update_summary, check_inventory_update_exists,
    save_replenishment_decision, load_recent_replenishment_decisions,
    load_replenishment_decision_summary, load_today_decisions,
    load_decided_stores_and_products,
    load_stores_for_product, load_store_forecast_trend,
    load_risk_summary_counts,
    save_alert_action, load_actionable_alerts, load_alerts_summary
)
from components import (
    render_kpi_row, custom_kpi_card, risk_donut, priority_donut,
    horizontal_bar, paginated_table, no_data_message,
    db_error_message, ai_unsupported_message,
    sidebar_store_filter, sidebar_risk_filter,
    sidebar_priority_filter, RISK_COLORS,
    recommendation_card
)

# ══════════════════════════════════════════════════════════════
# DATABASE CONNECTION (cached)
# ══════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner="Connecting to SmartStock database…")
def get_db_engine():
    return get_engine()

try:
    engine = get_db_engine()
except RuntimeError as e:
    db_error_message(str(e))
    st.stop()

# ══════════════════════════════════════════════════════════════
# GLOBAL THEME CSS — WAREHOUSE & RETAIL OPERATIONS AESTHETIC
# ══════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* ── Header & Toolbar — Keep Sidebar Controls Fully Accessible ── */
header[data-testid="stHeader"],
.stAppHeader {
    background: transparent !important;
    color: #0F172A !important;
    z-index: 99999 !important;
}

[data-testid="stToolbar"],
.stAppToolbar {
    background: transparent !important;
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* Hide Streamlit Clutter (Menu, Deploy, Status, Badges, Rainbow Line) */
#MainMenu, [data-testid="stMainMenu"] { visibility: hidden !important; display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stToolbarActions"] { display: none !important; }
.stDeployButton, [data-testid="manage-app-button"] { display: none !important; }
.viewerBadge_container__1QSob { display: none !important; }
footer { visibility: hidden !important; display: none !important; }

/* ── Sidebar Expand & Collapse Buttons — Small, Sleek & Minimalist ── */
button[data-testid="stExpandSidebarButton"],
[data-testid="stExpandSidebarButton"],
button[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
[data-testid="collapsedControl"] button {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    visibility: visible !important;
    opacity: 1 !important;
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 6px !important;
    box-shadow: 0 1px 4px rgba(15, 23, 42, 0.1) !important;
    padding: 3px 5px !important;
    height: 26px !important;
    min-height: 26px !important;
    width: auto !important;
    cursor: pointer !important;
    transition: all 0.15s ease-in-out !important;
}

button[data-testid="stExpandSidebarButton"]:hover,
[data-testid="stExpandSidebarButton"]:hover,
button[data-testid="stSidebarCollapseButton"]:hover,
[data-testid="stSidebarCollapseButton"]:hover {
    background: #F8FAFC !important;
    border-color: #2563EB !important;
    box-shadow: 0 2px 6px rgba(37, 99, 235, 0.2) !important;
    transform: scale(1.04) !important;
}

button[data-testid="stExpandSidebarButton"] svg,
[data-testid="stExpandSidebarButton"] svg,
button[data-testid="stExpandSidebarButton"] span,
[data-testid="stExpandSidebarButton"] span,
button[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapseButton"] svg {
    fill: #2563EB !important;
    color: #2563EB !important;
    stroke: #2563EB !important;
    width: 16px !important;
    height: 16px !important;
    font-size: 16px !important;
}

/* ── Container Geometry & Layout Spacing ── */
.block-container {
    padding-top: 1.8rem !important;
    padding-bottom: 3.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1340px !important;
}

/* ── Clean Modern Slate Canvas (replaces yellow-cream) ── */
.stApp {
    background: #F8FAFC !important;
}

/* ── Modern Warehouse/Retail Operations Sidebar ── */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
}
[data-testid="stSidebar"] hr {
    margin: 10px 0 !important;
    border-color: #E2E8F0 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > label {
    display: none !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] {
    gap: 6px !important;
    display: flex !important;
    flex-direction: column !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] > label {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 9px !important;
    padding: 10px 14px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: all 0.18s ease-in-out !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02) !important;
    display: flex !important;
    align-items: center !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
    background: #F1F5F9 !important;
    border-color: #CBD5E1 !important;
    transform: translateX(3px) !important;
}
/* Hide default radio circle bullet */
[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"] {
    display: none !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] div[data-testid="stMarkdownContainer"] p {
    font-size: 13.5px !important;
    font-weight: 600 !important;
    color: #1E293B !important;
    margin: 0 !important;
}
/* Active Pill Highlight — Modern Industrial Slate/Navy */
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked),
[data-testid="stSidebar"] [data-testid="stRadio"] div[aria-checked="true"] {
    background: #1E293B !important;
    border-color: #0F172A !important;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.22) !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p,
[data-testid="stSidebar"] [data-testid="stRadio"] div[aria-checked="true"] p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* ── Typography Standards ── */
h1, h2, h3, h4, h5 {
    color: #0F172A !important;
    font-weight: 700;
    letter-spacing: -0.3px;
}
p, li, label {
    color: #334155 !important;
    line-height: 1.6;
}

/* ── Metrics Cards Polish ── */
[data-testid="metric-container"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-top: 3.5px solid #2563EB !important;
    border-radius: 12px !important;
    padding: 10px 14px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02) !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease !important;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.07) !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"],
[data-testid="metric-container"] [data-testid="stMetricValue"] > div,
[data-testid="metric-container"] [data-testid="stMetricValue"] * {
    color: #0F172A !important;
    font-weight: 700 !important;
    font-size: 18px !important;
    line-height: 1.25 !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    word-break: normal !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"],
[data-testid="metric-container"] [data-testid="stMetricLabel"] p,
[data-testid="metric-container"] [data-testid="stMetricLabel"] * {
    color: #64748B !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

/* ── DataFrames & Table Polish ── */
.stDataFrame {
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03) !important;
    background: #FFFFFF !important;
}
thead tr th {
    background: #F1F5F9 !important;
    color: #1E293B !important;
    font-weight: 700 !important;
    font-size: 12.5px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    border-bottom: 2px solid #CBD5E1 !important;
}
tbody tr:nth-child(even) {
    background: #F8FAFC !important;
}
tbody tr:hover {
    background: rgba(37, 99, 235, 0.04) !important;
}

/* ── Action Buttons — High-Visibility Cobalt Blue with Pure White Text ── */
.stButton > button,
.stDownloadButton > button,
div[data-testid="stFormSubmitButton"] > button,
button[data-testid="baseButton-primary"],
button[data-testid="baseButton-secondary"] {
    background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 13.5px !important;
    border: none !important;
    border-radius: 9px !important;
    padding: 9px 22px !important;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.28) !important;
    transition: all 0.18s ease-in-out !important;
}

/* Force pure white text on all child tags (p, span, div, svg, label) inside buttons */
.stButton > button *,
.stButton > button p,
.stButton > button span,
.stButton > button div,
.stDownloadButton > button *,
.stDownloadButton > button p,
.stDownloadButton > button span,
.stDownloadButton > button div,
div[data-testid="stFormSubmitButton"] > button *,
div[data-testid="stFormSubmitButton"] > button p,
div[data-testid="stFormSubmitButton"] > button span,
div[data-testid="stFormSubmitButton"] > button div,
button[data-testid="baseButton-primary"] *,
button[data-testid="baseButton-primary"] p,
button[data-testid="baseButton-primary"] span,
button[data-testid="baseButton-secondary"] *,
button[data-testid="baseButton-secondary"] p,
button[data-testid="baseButton-secondary"] span {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover,
button[data-testid="baseButton-primary"]:hover,
button[data-testid="baseButton-secondary"]:hover {
    background: linear-gradient(135deg, #172554 0%, #1D4ED8 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.38) !important;
}

.stButton > button:hover *,
.stDownloadButton > button:hover *,
div[data-testid="stFormSubmitButton"] > button:hover *,
button[data-testid="baseButton-primary"]:hover *,
button[data-testid="baseButton-secondary"]:hover * {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}

.stButton > button:active,
.stDownloadButton > button:active,
div[data-testid="stFormSubmitButton"] > button:active {
    transform: translateY(0) !important;
}

/* ── Form Controls & Selectboxes — Black Text On White Backgrounds ── */
.stSelectbox, .stMultiSelect, .stTextInput, .stNumberInput, .stDateInput, .stTextArea {
    color: #0F172A !important;
}

/* BaseWeb Selectbox Container */
div[data-baseweb="select"] {
    background-color: #FFFFFF !important;
    border-radius: 8px !important;
}

div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    color: #0F172A !important;
    transition: border-color 0.15s ease !important;
}

div[data-baseweb="select"] > div:hover {
    border-color: #2563EB !important;
}

/* Force selected value text and options to be pure black / dark slate */
div[data-baseweb="select"] *,
div[data-baseweb="select"] div,
div[data-baseweb="select"] span,
div[data-baseweb="select"] input,
div[data-baseweb="select"] p,
[data-testid="stSelectbox"] *,
[data-testid="stSelectbox"] div,
[data-testid="stSelectbox"] span,
[data-testid="stSelectbox"] input,
[data-testid="stSelectbox"] p,
[data-testid="stMultiSelect"] *,
[data-testid="stMultiSelect"] div,
[data-testid="stMultiSelect"] span,
[data-testid="stMultiSelect"] input,
[data-testid="stMultiSelect"] p {
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    font-weight: 600 !important;
}

/* Multiselect Tags (Pills) */
div[data-baseweb="tag"] {
    background-color: #F1F5F9 !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 6px !important;
}

div[data-baseweb="tag"] * {
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    font-weight: 600 !important;
}

/* Dropdown Options Menu / Popover when clicking selectbox */
div[data-baseweb="popover"],
div[data-baseweb="popover"] *,
div[data-baseweb="menu"],
ul[data-baseweb="menu"],
ul[data-baseweb="menu"] li {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
}

ul[data-baseweb="menu"] li:hover,
ul[data-baseweb="menu"] li[aria-selected="true"] {
    background-color: #EFF6FF !important;
    color: #1D4ED8 !important;
    -webkit-text-fill-color: #1D4ED8 !important;
}

/* Text Input & Number Input */
.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stTextArea textarea {
    background-color: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    padding: 9px 12px !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
}

.stTextInput input:focus,
.stNumberInput input:focus,
.stDateInput input:focus,
.stTextArea textarea:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #94A3B8 !important;
    -webkit-text-fill-color: #94A3B8 !important;
}

/* Form Widget Labels */
label[data-testid="stWidgetLabel"],
label[data-testid="stWidgetLabel"] p,
label[data-testid="stWidgetLabel"] span {
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    font-weight: 700 !important;
    font-size: 13px !important;
}

/* Warehouse DB Connected Badge text MUST be pure white */
.warehouse-db-pill,
.warehouse-db-pill * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* ── Segmented Tabs — Modern Deep Slate Active ── */
.stTabs [data-baseweb="tab-list"] {
    background: #FFFFFF !important;
    border-radius: 10px !important;
    border: 1px solid #E2E8F0 !important;
    padding: 5px !important;
    gap: 6px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
}
.stTabs [data-baseweb="tab"] {
    color: #475569 !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    border-radius: 7px !important;
    padding: 8px 18px !important;
    transition: all 0.15s ease !important;
    border: none !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #0F172A !important;
    background: #F1F5F9 !important;
}
.stTabs [aria-selected="true"] {
    background: #1E293B !important;
    color: #FFFFFF !important;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.22) !important;
}
.stTabs [aria-selected="true"] *,
.stTabs [aria-selected="true"] p,
.stTabs [aria-selected="true"] span,
.stTabs [aria-selected="true"] div {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* ── Alerts & Dividers ── */
.stAlert { border-radius: 10px !important; }
hr { border-color: #E2E8F0 !important; }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────

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

st.sidebar.markdown("""
<div style="padding: 16px 12px 14px 12px; text-align: center; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
    <div style="display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #2563EB 100%); border-radius: 10px; font-size: 22px; color: #FFFFFF; margin-bottom: 8px; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.28);">
        📦
    </div>
    <div style="font-size: 19px; font-weight: 800; color: #0F172A; letter-spacing: -0.3px;">SmartStock AI</div>
    <div style="font-size: 11px; color: #2563EB; letter-spacing: 0.8px; text-transform: uppercase; margin-top: 3px; font-weight: 700;">
        Inventory Intelligence
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()

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



# ══════════════════════════════════════════════════════════════
# CACHED DATA LOADERS
# ══════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner="Loading inventory data…")
def get_kpi():
    return load_business_kpis(engine)

@st.cache_data(ttl=300)
def get_stores():
    return load_store_recommendations(engine)

@st.cache_data(ttl=300)
def get_products():
    return load_product_recommendations(engine)

@st.cache_data(ttl=300)
def get_categories():
    return load_category_summary(engine)

@st.cache_data(ttl=300)
def get_top20():
    return load_top20_recommendations(engine)

@st.cache_data(ttl=300)
def get_daily_trend():
    return load_daily_sales_trend(engine)

_instacart_ok = instacart_available(engine)

@st.cache_data(ttl=300)
def get_instacart_kpis():
    return load_instacart_kpis(engine)

@st.cache_data(ttl=300)
def get_top_purchased():
    return load_top_products(engine, 25)

@st.cache_data(ttl=300)
def get_top_reorder():
    return load_top_reorder_products(engine, 25)

@st.cache_data(ttl=300)
def get_departments():
    return load_department_summary(engine)

@st.cache_data(ttl=300)
def get_aisles():
    return load_aisle_summary(engine, 25)

@st.cache_data(ttl=300)
def get_basket_rules(min_lift: float = 1.5):
    return load_basket_rules(engine, min_lift, 100)

@st.cache_data(ttl=300)
def get_unified(risk=None):
    return load_unified_intelligence(engine, risk, 200)

@st.cache_data(ttl=300)
def get_stores_catalog():
    return load_stores_catalog(engine)

@st.cache_data(ttl=300)
def get_products_catalog():
    return load_products_catalog(engine)

DEPT_MAP = {
    0: "Leafy & Green Vegetables",
    1: "Root Vegetables & Tubers",
    2: "Fresh Fruits & Berries",
    3: "Herbs & Seasonings",
    4: "Specialty & Organic Produce",
    5: "Pre-cut & Packaged Fresh",
    6: "General Perishable Produce"
}


# ══════════════════════════════════════════════════════════════
# GLOBAL APPLICATION HEADER & REFRESH SYSTEM
# ══════════════════════════════════════════════════════════════

from datetime import datetime

if "last_updated" not in st.session_state:
    st.session_state["last_updated"] = datetime.now().strftime("%d %b %Y, %I:%M %p")

# ── TOP HERO BANNER ───────────────────────────────────────────
st.markdown("""
<div style="background: linear-gradient(135deg, #0A1128 0%, #101F42 35%, #1B2A4A 70%, #0F172A 100%); padding: 26px 20px 24px 20px; border-radius: 14px; text-align: center; margin-bottom: 14px; box-shadow: 0 12px 28px -6px rgba(10, 17, 40, 0.35), 0 4px 12px rgba(0, 0, 0, 0.08); border: 1px solid rgba(255, 255, 255, 0.12); position:relative; overflow:hidden;">
    <div style="font-size: 38px; font-weight: 900; color: #FFFFFF; letter-spacing: 0.8px; line-height: 1.15; text-shadow: 0 2px 10px rgba(0, 0, 0, 0.45); font-family: 'Plus Jakarta Sans', sans-serif;">
        SMARTSTOCK AI
    </div>
    <div style="font-size: 16px; font-weight: 600; color: #93C5FD; letter-spacing: 0.3px; margin-top: 8px; max-width: 820px; margin-left: auto; margin-right: auto; text-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);">
        Data-Driven Inventory Replenishment &amp; Stock Optimization
    </div>
</div>
""", unsafe_allow_html=True)

# ── TOP UTILITY TOOLBAR ─────────────────────────────────────────
top_u1, top_u2 = st.columns([3, 1])
with top_u1:
    st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:10px 18px; box-shadow:0 1px 3px rgba(0,0,0,0.03); display:flex; align-items:center; gap:10px; font-size:13px; color:#475569;">
    <span style="width:8px; height:8px; background:#10B981; border-radius:50%; display:inline-block; box-shadow:0 0 6px #10B981;"></span>
    <span>Last updated: <strong style="color:#0F172A;">{st.session_state['last_updated']}</strong></span>
</div>
""", unsafe_allow_html=True)

with top_u2:
    if st.button("🔄 Refresh Data", key="global_refresh_btn", use_container_width=True):
        st.session_state["last_updated"] = datetime.now().strftime("%d %b %Y, %I:%M %p")
        st.cache_data.clear()
        st.rerun()

st.markdown("<div style='border-bottom: 1.5px solid #E2E8F0; margin: 4px 0 20px 0;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════

if page == "Dashboard":
    st.title("Dashboard")

    st.markdown("""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid #2563EB; border-radius:10px; padding:14px 18px; margin:8px 0 18px 0; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="font-size:13.5px; color:#1E293B; line-height:1.6;">
        Operational inventory summary across <strong>898 store locations</strong> and <strong>865 perishable produce SKUs</strong>. Monitor stockout risks, track customer demand, and review prioritized replenishment recommendations.
    </div>
</div>
""", unsafe_allow_html=True)

    try:
        kpi = get_kpi()
        prod_df = get_products()
        store_df = get_stores()
        top20_df = get_top20()
    except Exception as e:
        db_error_message(str(e)); st.stop()

    dept_names = {
        0: "Leafy & Green Vegetables",
        1: "Root Vegetables & Tubers",
        2: "Fresh Fruits & Berries",
        3: "Herbs & Seasonings",
        4: "Specialty & Organic Produce",
        5: "Pre-cut & Packaged Fresh",
        6: "General Perishable Produce"
    }

    urgent_cnt = int(kpi.get("high_priority_reorders", 0))
    risk_cnt = int(kpi.get("high_risk_products", 0))
    high_risk_prods = int((prod_df["high_risk_pct"] >= 50).sum())
    good_prods = int((prod_df["high_risk_pct"] < 20).sum())

    # ── SECTION 1: INVENTORY OVERVIEW ─────────────────────────
    st.markdown("### Inventory Overview")
    k1, k2, k3 = st.columns(3)
    custom_kpi_card(k1, "Total Products", f"{len(prod_df):,} SKUs", subtext="Active perishable catalog", help_text="Total active catalog items across 7 fresh produce categories", top_color="#2563EB")
    custom_kpi_card(k2, "Total Stores", f"{len(store_df):,} Stores", subtext="Retail network locations", help_text="Active retail store locations in the fulfillment network", top_color="#0284C7")
    custom_kpi_card(k3, "Products at Risk", f"{high_risk_prods:,} SKUs", subtext="Elevated stockout probability", help_text="Products facing frequent stockouts requiring attention", top_color="#DC2626")

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    k4, k5, k6 = st.columns(3)
    custom_kpi_card(k4, "Urgent Reorders", f"{urgent_cnt:,} Items", subtext="Needs replenishment review", help_text="Store and product combinations requiring prioritized replenishment", top_color="#EA580C")
    custom_kpi_card(k5, "Good Performers", f"{good_prods:,} SKUs", subtext="Stable stock & steady demand", help_text="Products with low risk frequency and steady turnover", top_color="#059669")
    custom_kpi_card(k6, "Expected Demand", f"{float(kpi['avg_predicted_sales']):.2f} units/day", subtext="Average daily demand per SKU", help_text="Mean expected daily unit demand across all stores and products", top_color="#4F46E5")

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # ── SECTION 2: INVENTORY HEALTH ───────────────────────────
    st.markdown("### Inventory Health")

    h_col1, h_col2, h_col3 = st.columns(3)
    with h_col1:
        st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-top:4px solid #059669; border-radius:8px; padding:14px 18px; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="font-size:11px; font-weight:700; color:#059669; letter-spacing:0.8px; text-transform:uppercase;">🟢 GOOD</div>
    <div style="font-size:24px; font-weight:800; color:#0F172A; margin-top:4px;">{int(kpi['low_risk_products']):,} records</div>
    <div style="font-size:12.5px; color:#64748B; margin-top:3px;">Inventory performing normally with steady sales velocity.</div>
</div>
""", unsafe_allow_html=True)
    with h_col2:
        st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-top:4px solid #D97706; border-radius:8px; padding:14px 18px; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="font-size:11px; font-weight:700; color:#D97706; letter-spacing:0.8px; text-transform:uppercase;">🟡 ATTENTION</div>
    <div style="font-size:24px; font-weight:800; color:#0F172A; margin-top:4px;">{int(kpi['medium_risk_products']):,} records</div>
    <div style="font-size:12.5px; color:#64748B; margin-top:3px;">Inventory requires monitoring before the next order cycle.</div>
</div>
""", unsafe_allow_html=True)
    with h_col3:
        st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-top:4px solid #DC2626; border-radius:8px; padding:14px 18px; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="font-size:11px; font-weight:700; color:#DC2626; letter-spacing:0.8px; text-transform:uppercase;">🔴 ACTION REQUIRED</div>
    <div style="font-size:24px; font-weight:800; color:#0F172A; margin-top:4px;">{int(kpi['high_risk_products']):,} records</div>
    <div style="font-size:12.5px; color:#64748B; margin-top:3px;">Immediate attention required to prevent stockouts and lost sales.</div>
</div>
""", unsafe_allow_html=True)

    v_col1, v_col2 = st.columns(2)
    with v_col1:
        st.plotly_chart(risk_donut(kpi, "Network Risk Breakdown"), use_container_width=True)
    with v_col2:
        st.plotly_chart(priority_donut(kpi, "Priority"), use_container_width=True)

    st.divider()

    # ── SECTION 3: PRIORITY ACTIONS ───────────────────────────
    st.markdown("### Priority Actions")
    st.caption("Critical store and product recommendations requiring immediate replenishment review:")

    if not top20_df.empty:
        pa_col1, pa_col2 = st.columns(2)
        top_items = top20_df.head(4).to_dict(orient="records")
        for idx, act in enumerate(top_items):
            target_col = pa_col1 if idx % 2 == 0 else pa_col2
            dept_lbl = dept_names.get(int(act.get("management_group_id", 0)), "Fresh Produce")
            with target_col:
                recommendation_card(
                    st,
                    status=act["stockout_risk"],
                    title=f"SKU {int(act['product_id'])} at Store {int(act['store_id'])}",
                    subtitle=f"{dept_lbl} · Category {int(act.get('first_category_id', 0))}",
                    demand=f"{float(act['predicted_sales']):.2f} units/day",
                    reorder=f"{float(act['recommended_reorder_qty']):.0f} units (7-day cover)",
                    why=f"Customer demand is elevated ({float(act['predicted_sales']):.2f} units/day) with persistent historical stockouts.",
                    action="Review Recommendation"
                )

    st.divider()

    # ── SECTION 4: PRODUCTS NEEDING ATTENTION ─────────────────
    st.markdown("### Products Needing Attention")
    st.caption("Products with highest expected demand and stockout risk:")

    perf_prod = prod_df.sort_values(["high_risk_pct", "predicted_sales"], ascending=[False, False]).head(10).copy()
    perf_prod["Department"] = perf_prod["management_group_id"].map(lambda g: dept_names.get(int(g), f"Category {g}"))
    perf_prod["Product"] = perf_prod["product_id"].apply(lambda p: f"SKU {int(p)}")
    perf_prod["Status"] = perf_prod["high_risk_pct"].apply(
        lambda p: "🔴 Action Required" if p >= 50 else ("🟡 Attention" if p >= 20 else "🟢 Good")
    )
    perf_prod["Expected Demand"] = perf_prod["predicted_sales"].apply(lambda v: f"{float(v):.2f} units/day")
    perf_prod["Historical Sales"] = perf_prod["total_sales"].apply(lambda v: f"{float(v):,.0f} units")
    perf_prod["Suggested Reorder"] = perf_prod["avg_reorder_qty"].apply(lambda v: f"{float(v):,.0f} units")

    prod_cols = [
        "Product",
        "Department",
        "Expected Demand",
        "Historical Sales",
        "Suggested Reorder",
        "Status"
    ]
    st.dataframe(perf_prod[prod_cols], use_container_width=True, hide_index=True)

    st.divider()

    # ── SECTION 5: STORES NEEDING ATTENTION ───────────────────
    st.markdown("### Stores Needing Attention")
    st.caption("Store locations requiring replenishment attention compared with top volume stores:")

    s_top, s_attn = st.columns(2)
    with s_top:
        st.markdown("##### 🟢 Top Performing Stores")
        strong_stores = store_df.sort_values("predicted_sales", ascending=False).head(5).copy()
        strong_stores["Store"] = strong_stores["store_id"].apply(lambda s: f"Store {int(s)}")
        strong_stores["Expected Demand"] = strong_stores["predicted_sales"].apply(lambda v: f"{float(v):.2f} units/day")
        strong_stores["Risk %"] = strong_stores["high_risk_pct"].apply(lambda v: f"{float(v):.1f}%")
        strong_stores["Status"] = "🟢 Good"
        st_cols = ["Store", "Expected Demand", "Risk %", "Status"]
        st.dataframe(strong_stores[st_cols], use_container_width=True, hide_index=True)

    with s_attn:
        st.markdown("##### 🔴 Stores Needing Attention")
        attn_stores = store_df.sort_values("high_risk_pct", ascending=False).head(5).copy()
        attn_stores["Store"] = attn_stores["store_id"].apply(lambda s: f"Store {int(s)}")
        attn_stores["High-Risk SKUs"] = attn_stores["high_risk_products"].apply(lambda v: f"{int(v):,}")
        attn_stores["Urgent Reorders"] = attn_stores["urgent_reorders"].apply(lambda v: f"{int(v):,}")
        attn_stores["Risk %"] = attn_stores["high_risk_pct"].apply(lambda v: f"{float(v):.1f}%")
        attn_stores["Status"] = "🔴 Action Required"
        st_attn_cols = ["Store", "High-Risk SKUs", "Urgent Reorders", "Risk %", "Status"]
        st.dataframe(attn_stores[st_attn_cols], use_container_width=True, hide_index=True)

    st.divider()

    # ── SECTION 6: REPLENISHMENT RECOMMENDATIONS ──────────────
    st.markdown("### Replenishment Recommendations")
    st.caption("Suggested reorders based on expected demand and 7-day demand cover:")

    rep_summary = top20_df.head(8).copy()
    rep_summary["Product"] = rep_summary["product_id"].apply(lambda p: f"SKU {int(p)}")
    rep_summary["Store"] = rep_summary["store_id"].apply(lambda s: f"Store {int(s)}")
    rep_summary["Expected Demand"] = rep_summary["predicted_sales"].apply(lambda v: f"{float(v):.2f} units/day")
    rep_summary["Risk"] = rep_summary["stockout_risk"].apply(lambda r: f"🔴 {r}" if "HIGH" in str(r).upper() else f"🟡 {r}")
    rep_summary["Recommended Reorder"] = rep_summary["recommended_reorder_qty"].apply(lambda v: f"{float(v):,.0f} units")
    rep_summary["Action"] = "Review Recommendation"

    rep_cols = [
        "Product",
        "Store",
        "Expected Demand",
        "Risk",
        "Recommended Reorder",
        "Action"
    ]
    st.dataframe(rep_summary[rep_cols], use_container_width=True, hide_index=True)
    st.info("For comprehensive store-by-store filtering, reorder calculators, and CSV export, visit the **Replenishment** page.")




# ══════════════════════════════════════════════════════════════
# PAGE: STORE INTELLIGENCE
# ══════════════════════════════════════════════════════════════

elif page == "Stores":
    st.title("Stores")
    st.markdown("""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid #2563EB; border-radius:10px; padding:14px 18px; margin:8px 0 18px 0; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="font-size:13.5px; color:#1E293B; line-height:1.6;">
        Store inventory summary tracking expected demand and stockout risk across <strong>898 stores</strong>.
    </div>
</div>
""", unsafe_allow_html=True)

    try:
        store_df = get_stores()
    except Exception as e:
        db_error_message(str(e)); st.stop()

    # Classification rules:
    # 🟢 Good: high_risk_pct < 10%
    # 🟡 Attention: 10% <= high_risk_pct < 15%
    # 🔴 Action Required: high_risk_pct >= 15%
    classified_stores = store_df.copy()
    classified_stores["Status"] = "🟢 Good"
    classified_stores.loc[classified_stores["high_risk_pct"] >= 10, "Status"] = "🟡 Attention"
    classified_stores.loc[classified_stores["high_risk_pct"] >= 15, "Status"] = "🔴 Action Required"

    good_count = int((classified_stores["high_risk_pct"] < 10).sum())
    attention_count = int(((classified_stores["high_risk_pct"] >= 10) & (classified_stores["high_risk_pct"] < 15)).sum())
    urgent_count = int((classified_stores["high_risk_pct"] >= 15).sum())

    # STEP 14: 4 Summary KPIs
    c1, c2, c3, c4 = st.columns(4)
    custom_kpi_card(c1, "Total Stores", f"{len(store_df):,}", subtext="Active fulfillment locations", top_color="#2563EB")
    custom_kpi_card(c2, "Good", f"{good_count:,}", subtext="<10% stockout risk", top_color="#059669")
    custom_kpi_card(c3, "Attention", f"{attention_count:,}", subtext="10–14.9% stockout risk", top_color="#D97706")
    custom_kpi_card(c4, "Action Required", f"{urgent_count:,}", subtext="≥15% stockout risk", top_color="#DC2626")

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # ── STEP 2, 3, 4: STORE SELECTION & ANALYSIS WORKFLOW ─────────
    st.markdown("### Store Analysis")
    st.caption("Select a store to see its performance and products that need attention.")

    all_store_ids = sorted(classified_stores["store_id"].unique().tolist())

    if "analyzed_store_id" not in st.session_state:
        st.session_state["analyzed_store_id"] = 417

    current_store = st.session_state["analyzed_store_id"]
    current_idx = all_store_ids.index(current_store) if current_store in all_store_ids else 0

    col_sel, col_btn = st.columns([3, 1.2])
    with col_sel:
        selected_store_str = st.selectbox(
            "Select Store:",
            options=all_store_ids,
            index=current_idx,
            format_func=lambda s: f"Store {s} — {classified_stores.loc[classified_stores['store_id'] == s, 'Status'].values[0]}",
            key="store_analysis_selectbox"
        )
    with col_btn:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        analyze_store_btn = st.button("Analyze Store", type="primary", use_container_width=True)

    if analyze_store_btn:
        st.session_state["analyzed_store_id"] = selected_store_str

    target_store_id = st.session_state["analyzed_store_id"]

    # STEP 4: VALIDATION
    matched_store = classified_stores[classified_stores["store_id"] == target_store_id]
    if matched_store.empty:
        st.warning(f"No data found for Store {target_store_id}.")
    else:
        s_row = matched_store.iloc[0]
        status_str = s_row["Status"]
        risk_pct = float(s_row["high_risk_pct"])
        predicted_sales = float(s_row["predicted_sales"])
        products_count = int(s_row["products"])
        urgent_reorders = int(s_row["urgent_reorders"])

        if analyze_store_btn:
            with st.spinner("Analyzing store..."):
                import time
                time.sleep(0.05)

        # Status styling & explanations (Step 7 & 9)
        if risk_pct >= 15:
            status_color = "#DC2626"
            status_badge = "🔴 Action Required"
            risk_label = "🔴 High Risk"
            why_store_text = "Several products in this store have high inventory risk and require immediate replenishment."
            action_advice = "Review the products marked as high risk and approve replenishment orders."
            action_card_bg = "#FEF2F2"
            action_border = "#DC2626"
        elif risk_pct >= 10:
            status_color = "#D97706"
            status_badge = "🟡 Attention"
            risk_label = "🟡 Medium Risk"
            why_store_text = "Some products in this store need monitoring before the next delivery window."
            action_advice = "Monitor stock levels across items approaching reorder thresholds."
            action_card_bg = "#FFFBEB"
            action_border = "#D97706"
        else:
            status_color = "#059669"
            status_badge = "🟢 Good"
            risk_label = "🟢 Low Risk"
            why_store_text = "Most products in this store are performing normally with stable inventory coverage."
            action_advice = "Maintain standard replenishment schedules for this store."
            action_card_bg = "#F0FDF4"
            action_border = "#059669"

        # ── STEP 5: STORE SUMMARY ───────────────────────────────────
        st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid {status_color}; border-radius:10px; padding:12px 18px; margin:14px 0 12px 0; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
        <div>
            <div style="font-size:18px; font-weight:800; color:#0F172A;">Store {target_store_id}</div>
            <div style="font-size:13px; color:#64748B; margin-top:2px;">
                Active Inventory: <strong style="color:#0F172A;">{products_count:,} SKUs</strong> · Expected Demand: <strong style="color:#0F172A;">{predicted_sales:,.0f} units/day</strong>
            </div>
        </div>
        <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:6px; padding:6px 14px; font-size:13px; font-weight:700; color:#0F172A;">
            Status: {status_badge}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

        # ── STEP 6: STORE KEY RESULTS ───────────────────────────────
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Active Products", f"{products_count:,} SKUs")
        k2.metric("Expected Daily Demand", f"{predicted_sales:,.0f} units/day")
        k3.metric("Risk Exposure", f"{risk_pct:.1f}% high risk", help="Percentage of products at high stockout risk")
        k4.metric("Urgent Reorders", f"{urgent_reorders:,}", help="Items requiring replenishment attention")

        st.markdown(f"""
<div style="background:#F8FAFC; border:1px solid #E2E8F0; border-left:4px solid #64748B; border-radius:8px; padding:10px 16px; font-size:13px; color:#1E293B; margin-bottom:14px;">
    <strong>Store Assessment:</strong> {why_store_text}
</div>
""", unsafe_allow_html=True)

        # ── STEP 10 & 11: PRODUCTS NEEDING ATTENTION ─────────────────
        st.markdown("#### Products Needing Attention")
        st.caption("Top products requiring replenishment focus at this store location:")

        try:
            store_recs = load_forecast_recommendations(engine, store_id=target_store_id, limit=50)
            if not store_recs.empty:
                top_store_prods = store_recs.drop_duplicates(subset=["product_id"]).head(5).copy()
            else:
                top_store_prods = pd.DataFrame()
        except Exception:
            top_store_prods = pd.DataFrame()

        if top_store_prods.empty:
            st.info("No products need attention for this store.")
        else:
            for idx, p_row in top_store_prods.iterrows():
                pid = int(p_row["product_id"])
                dept_name = DEPT_MAP.get(pid % 7, "Perishable Produce")
                demand_val = float(p_row["predicted_sales"])
                reorder_val = float(p_row["recommended_reorder_qty"])
                p_risk = str(p_row["stockout_risk"]).upper()
                p_prio = str(p_row.get("replenishment_priority", "LOW")).upper()

                if "HIGH" in p_risk:
                    risk_badge_str = "🔴 High Risk"
                elif "MEDIUM" in p_risk:
                    risk_badge_str = "🟡 Medium Risk"
                else:
                    risk_badge_str = "🟢 Low Risk"

                if "HIGH" in p_prio:
                    prio_badge_str = "🔴 Urgent"
                elif "MEDIUM" in p_prio:
                    prio_badge_str = "🟡 Monitor"
                else:
                    prio_badge_str = "🟢 Normal"

                with st.container():
                    p_c1, p_c2, p_c3, p_c4, p_c5, p_c6 = st.columns([1.8, 1.4, 1.2, 1.3, 1.1, 1.2])
                    with p_c1:
                        st.markdown(f"**SKU {pid}**<br><span style='font-size:12px; color:#64748B;'>{dept_name}</span>", unsafe_allow_html=True)
                    with p_c2:
                        st.markdown(f"<span style='font-size:11px; color:#64748B;'>Demand:</span><br><strong>{demand_val:.1f} units/day</strong>", unsafe_allow_html=True)
                    with p_c3:
                        st.markdown(f"<span style='font-size:11px; color:#64748B;'>Risk:</span><br>{risk_badge_str}", unsafe_allow_html=True)
                    with p_c4:
                        st.markdown(f"<span style='font-size:11px; color:#64748B;'>Reorder:</span><br><strong>{reorder_val:,.0f} units</strong>", unsafe_allow_html=True)
                    with p_c5:
                        st.markdown(f"<span style='font-size:11px; color:#64748B;'>Priority:</span><br>{prio_badge_str}", unsafe_allow_html=True)
                    with p_c6:
                        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
                        if st.button("View Product", key=f"btn_vp_{target_store_id}_{pid}", use_container_width=True):
                            st.session_state["nav_page"] = "Products"
                            st.session_state["analyzed_product_id"] = pid
                            st.session_state["analyzed_store"] = f"Store {target_store_id}"
                            st.rerun()
                    st.markdown("<div style='border-bottom:1px solid #F1F5F9; margin:4px 0;'></div>", unsafe_allow_html=True)

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

        # ── STEP 8: STORE PERFORMANCE (CHART) ───────────────────────
        st.markdown("#### Store Performance")
        try:
            store_trend_df = load_store_forecast_trend(engine, target_store_id)
            if not store_trend_df.empty:
                store_trend_df["dt"] = pd.to_datetime(store_trend_df["dt"]).dt.strftime("%b %d")
                fig_store_trend = go.Figure()
                fig_store_trend.add_trace(go.Bar(
                    x=store_trend_df["dt"],
                    y=store_trend_df["actual_sales"],
                    name="Recorded Sales",
                    marker_color="#2563EB",
                    opacity=0.85
                ))
                fig_store_trend.add_trace(go.Scatter(
                    x=store_trend_df["dt"],
                    y=store_trend_df["predicted_sales"],
                    name="Expected Demand",
                    mode="lines+markers",
                    line=dict(color="#D97706", width=3, dash="dash"),
                    marker=dict(size=8, color="#D97706")
                ))
                fig_store_trend.update_layout(
                    title=dict(text=f"Sales Trend — Store {target_store_id}", font=dict(size=14, color="#0F172A")),
                    height=280,
                    margin=dict(t=35, b=25, l=40, r=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(title=None, showgrid=False),
                    yaxis=dict(title="Units", showgrid=True, gridcolor="#E2E8F0")
                )
                st.plotly_chart(fig_store_trend, use_container_width=True)
            else:
                st.caption("Sales trend data is currently unavailable for this store.")
        except Exception:
            st.caption("Unable to render store performance chart.")

        # ── STEP 15, 16: WHAT SHOULD I DO? & [ VIEW RECOMMENDATIONS ] ──
        st.markdown("#### What Should I Do?")
        act_c1, act_c2 = st.columns([3, 1])
        with act_c1:
            st.markdown(f"""
<div style="background:{action_card_bg}; border:1px solid {action_border}; border-radius:8px; padding:12px 16px;">
    <div style="font-size:14px; font-weight:700; color:#0F172A;">{status_badge}: Store {target_store_id}</div>
    <div style="font-size:12.5px; color:#475569; margin-top:3px;">{action_advice}</div>
</div>
""", unsafe_allow_html=True)
        with act_c2:
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            if st.button("View Recommendations", type="primary", key="btn_view_store_recs", use_container_width=True):
                st.session_state["nav_page"] = "Replenishment"
                st.session_state["repl_store_filter"] = f"Store {target_store_id}"
                st.rerun()

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.divider()

    # ── STEP 12, 13: TOP STORES & STORES NEEDING ATTENTION ───────
    st.markdown("### Network Stores Overview")
    st.caption("Comparison between stores requiring operational replenishment focus and highest volume stores:")

    s_attn_col, s_top_col = st.columns(2)
    with s_attn_col:
        st.markdown("##### 🔴 Stores Needing Attention")
        top_attn_stores = classified_stores.sort_values("high_risk_pct", ascending=False).head(5).copy()
        top_attn_stores["Store"] = top_attn_stores["store_id"].apply(lambda s: f"Store {int(s)}")
        top_attn_stores["High-Risk Products"] = top_attn_stores["high_risk_products"].apply(lambda v: f"{int(v):,}")
        top_attn_stores["Urgent Reorders"] = top_attn_stores["urgent_reorders"].apply(lambda v: f"{int(v):,}")
        top_attn_stores["Expected Demand"] = top_attn_stores["predicted_sales"].apply(lambda v: f"{float(v):,.0f} units/day")
        top_attn_stores["Risk %"] = top_attn_stores["high_risk_pct"].apply(lambda v: f"{float(v):.1f}%")
        st.dataframe(
            top_attn_stores[["Store", "Status", "High-Risk Products", "Urgent Reorders", "Expected Demand"]],
            use_container_width=True,
            hide_index=True
        )

    with s_top_col:
        st.markdown("##### 🟢 Top Performing Stores")
        top_perf_stores = classified_stores.sort_values("predicted_sales", ascending=False).head(5).copy()
        top_perf_stores["Store"] = top_perf_stores["store_id"].apply(lambda s: f"Store {int(s)}")
        top_perf_stores["Expected Demand"] = top_perf_stores["predicted_sales"].apply(lambda v: f"{float(v):,.0f} units/day")
        top_perf_stores["Active Products"] = top_perf_stores["products"].apply(lambda v: f"{int(v):,} SKUs")
        top_perf_stores["Risk %"] = top_perf_stores["high_risk_pct"].apply(lambda v: f"{float(v):.1f}%")
        st.dataframe(
            top_perf_stores[["Store", "Status", "Expected Demand", "Active Products", "Risk %"]],
            use_container_width=True,
            hide_index=True
        )

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # ── STEP 24, 26: SEARCHABLE STORE DIRECTORY ─────────────────
    st.markdown("### Search Store Directory")
    search_kw = st.text_input("Search by Store ID:", placeholder="e.g. 417 or 631", key="store_search_input")
    
    display_stores = classified_stores.copy()
    if search_kw.strip().isdigit():
        display_stores = display_stores[display_stores["store_id"] == int(search_kw.strip())]

    disp_table_cols = ["store_id", "Status", "products", "predicted_sales", "high_risk_products", "urgent_reorders", "high_risk_pct"]
    disp_rename = {
        "store_id": "Store ID",
        "Status": "Status",
        "products": "Active Products",
        "predicted_sales": "Expected Demand (units/day)",
        "high_risk_products": "High-Risk Products",
        "urgent_reorders": "Urgent Reorders",
        "high_risk_pct": "Risk Exposure (%)"
    }

    if not display_stores.empty:
        dir_df = display_stores[disp_table_cols].copy()
        dir_df["predicted_sales"] = dir_df["predicted_sales"].apply(lambda v: f"{float(v):,.0f}")
        dir_df["high_risk_pct"] = dir_df["high_risk_pct"].apply(lambda v: f"{float(v):.1f}%")
        paginated_table(dir_df.rename(columns=disp_rename), page_size=20, key="store_directory_page")
    else:
        no_data_message("the entered Store ID")





# ══════════════════════════════════════════════════════════════
# PAGE: PRODUCT INTELLIGENCE
# ══════════════════════════════════════════════════════════════

elif page == "Products":
    st.title("Products")
    st.markdown("""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid #2563EB; border-radius:10px; padding:14px 18px; margin:8px 0 18px 0; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="font-size:13.5px; color:#1E293B; line-height:1.6;">
        Product inventory summary tracking expected demand, stockout risk, and suggested reorders across <strong>865 SKUs</strong>.
    </div>
</div>
""", unsafe_allow_html=True)

    DEPT_MAP = {
        0: "Leafy & Green Vegetables",
        1: "Root Vegetables & Tubers",
        2: "Fresh Fruits & Berries",
        3: "Herbs & Seasonings",
        4: "Specialty & Organic Produce",
        5: "Pre-cut & Packaged Fresh",
        6: "General Perishable Produce"
    }

    try:
        prod_df = get_products()
    except Exception as e:
        db_error_message(str(e)); st.stop()

    # Enrich catalog data
    classified_prod = prod_df.copy()
    classified_prod["Department"] = classified_prod["management_group_id"].map(lambda g: DEPT_MAP.get(int(g), f"Category {g}"))
    classified_prod["Product Name"] = classified_prod["product_id"].apply(lambda p: f"SKU {int(p)}")

    classified_prod["Stockout Risk"] = "🟢 Good"
    classified_prod.loc[classified_prod["high_risk_pct"] >= 20, "Stockout Risk"] = "🟡 Attention"
    classified_prod.loc[classified_prod["high_risk_pct"] >= 50, "Stockout Risk"] = "🔴 Action Required"

    classified_prod["Replenishment Priority"] = "🟢 LOW"
    classified_prod.loc[classified_prod["high_risk_pct"] >= 20, "Replenishment Priority"] = "🟡 MEDIUM"
    classified_prod.loc[classified_prod["high_risk_pct"] >= 50, "Replenishment Priority"] = "🔴 HIGH"

    p_good = int((classified_prod["high_risk_pct"] < 20).sum())
    p_attn = int(((classified_prod["high_risk_pct"] >= 20) & (classified_prod["high_risk_pct"] < 50)).sum())
    p_high = int((classified_prod["high_risk_pct"] >= 50).sum())

    # Summary KPI row (Step 17)
    c1, c2, c3, c4 = st.columns(4)
    custom_kpi_card(c1, "Total Products", f"{len(prod_df):,} SKUs", subtext="Active perishable catalog", top_color="#2563EB")
    custom_kpi_card(c2, "Good", f"{p_good:,} SKUs", subtext="<20% risk frequency", top_color="#059669")
    custom_kpi_card(c3, "Attention", f"{p_attn:,} SKUs", subtext="20–49% risk frequency", top_color="#D97706")
    custom_kpi_card(c4, "Action Required", f"{p_high:,} SKUs", subtext="≥50% risk frequency", top_color="#DC2626")

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # ── STEP 2, 3, 4: INTERACTIVE PRODUCT SELECTION & ANALYSIS ──────────
    st.markdown("### Product Analysis")
    st.caption("Select a product to see its demand, risk, and reorder recommendation.")

    # Initialize analysis state
    if "analyzed_product_id" not in st.session_state:
        st.session_state["analyzed_product_id"] = 267
    if "analyzed_store" not in st.session_state:
        st.session_state["analyzed_store"] = "All Stores"

    col_prod, col_store, col_btn = st.columns([2.5, 2, 1.2])

    with col_prod:
        prod_options = [f"SKU {int(row['product_id'])} — {row['Department']}" for _, row in classified_prod.iterrows()]
        current_sku_str = f"SKU {st.session_state.get('analyzed_product_id', 267)} "
        default_prod_idx = 0
        for idx, opt in enumerate(prod_options):
            if opt.startswith(current_sku_str):
                default_prod_idx = idx
                break
        selected_prod_str = st.selectbox("Select Product:", prod_options, index=default_prod_idx, key="prod_select_box")
        
        import re
        m = re.search(r'SKU (\d+)', selected_prod_str)
        curr_selected_pid = int(m.group(1)) if m else 267

    with col_store:
        try:
            available_stores = load_stores_for_product(engine, curr_selected_pid)
        except Exception:
            available_stores = []
        
        store_dropdown_options = ["All Stores"] + [f"Store {s}" for s in available_stores]
        
        curr_store_val = st.session_state.get("analyzed_store", "All Stores")
        default_store_idx = 0
        if curr_store_val in store_dropdown_options:
            default_store_idx = store_dropdown_options.index(curr_store_val)
        
        selected_store_str = st.selectbox("Store (optional):", store_dropdown_options, index=default_store_idx, key="store_select_box")

    with col_btn:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        analyze_btn = st.button("Analyze Product", type="primary", use_container_width=True)

    if analyze_btn:
        st.session_state["analyzed_product_id"] = curr_selected_pid
        st.session_state["analyzed_store"] = selected_store_str

    target_pid = st.session_state["analyzed_product_id"]
    target_store = st.session_state["analyzed_store"]

    # STEP 5: VALIDATION
    prod_row_matches = classified_prod[classified_prod["product_id"] == target_pid]
    if prod_row_matches.empty:
        st.warning(f"No data found for SKU {target_pid}.")
    else:
        p_row = prod_row_matches.iloc[0]
        
        # Loading State (Step 25)
        if analyze_btn:
            with st.spinner("Analyzing product..."):
                import time
                time.sleep(0.05)

        target_sid = None
        if target_store != "All Stores" and target_store.startswith("Store "):
            try:
                target_sid = int(target_store.replace("Store ", "").strip())
            except ValueError:
                target_sid = None

        store_specific_data = pd.DataFrame()
        if target_sid is not None:
            try:
                store_specific_data = load_store_product_forecast(engine, target_sid, target_pid)
            except Exception as e:
                db_error_message("Unable to load store-specific forecast data.")
                store_specific_data = pd.DataFrame()

        if target_sid is not None and store_specific_data.empty:
            st.warning(f"No data found for SKU {target_pid} at Store {target_sid}.")
        else:
            # Prepare Metrics (Step 6, 7, 9, 10, 12, 31)
            if target_sid is not None and not store_specific_data.empty:
                latest_sp = store_specific_data.iloc[-1]
                
                exp_demand_val = float(latest_sp["predicted_sales"])
                exp_demand_display = f"{exp_demand_val:.1f} units/day"
                demand_subtext = "Next-day expected demand"
                
                sp_risk = str(latest_sp["stockout_risk"]).upper()
                if sp_risk == "HIGH":
                    risk_display = "🔴 High Risk"
                    risk_status_color = "#DC2626"
                    status_badge = "🔴 Action Required"
                elif sp_risk == "MEDIUM":
                    risk_display = "🟡 Medium Risk"
                    risk_status_color = "#D97706"
                    status_badge = "🟡 Attention"
                else:
                    risk_display = "🟢 Low Risk"
                    risk_status_color = "#059669"
                    status_badge = "🟢 Good"

                sp_prio = str(latest_sp.get("replenishment_priority", "LOW")).upper()
                if sp_prio == "HIGH":
                    priority_display = "🔴 Urgent"
                elif sp_prio == "MEDIUM":
                    priority_display = "🟡 Monitor"
                else:
                    priority_display = "🟢 Normal"

                reorder_qty_val = float(latest_sp["recommended_reorder_qty"])
                reorder_qty_display = f"{reorder_qty_val:,.0f} units"
                reorder_subtext = "7-day demand cover"

                location_label = f"Store {target_sid}"
                
                # Explanation (Step 11)
                why_explanation = str(latest_sp["risk_explanation"]) if pd.notna(latest_sp.get("risk_explanation")) and str(latest_sp["risk_explanation"]).strip() else "Demand and stockout patterns indicate current inventory levels require attention."

            else:
                # All Stores (Network level)
                exp_demand_val = float(p_row["predicted_sales"])
                exp_demand_display = f"{exp_demand_val:,.1f} units/day"
                demand_subtext = "Daily network projection"

                risk_pct = float(p_row["high_risk_pct"])
                if risk_pct >= 50:
                    risk_display = "🔴 High Risk"
                    risk_status_color = "#DC2626"
                    status_badge = "🔴 Action Required"
                    priority_display = "🔴 Urgent"
                elif risk_pct >= 20:
                    risk_display = "🟡 Medium Risk"
                    risk_status_color = "#D97706"
                    status_badge = "🟡 Attention"
                    priority_display = "🟡 Monitor"
                else:
                    risk_display = "🟢 Low Risk"
                    risk_status_color = "#059669"
                    status_badge = "🟢 Good"
                    priority_display = "🟢 Normal"

                reorder_qty_val = float(p_row["avg_reorder_qty"])
                reorder_qty_display = f"{reorder_qty_val:,.0f} units/store"
                reorder_subtext = "Average per store"

                store_count_text = f"All Stores ({len(available_stores)} locations)" if available_stores else "All Stores"
                location_label = store_count_text

                # Explanation (Step 11)
                if risk_pct >= 50:
                    why_explanation = f"High stockout risk observed across {risk_pct:.0f}% of stores carrying this SKU. Expected demand is elevated and requires replenishment."
                elif risk_pct >= 20:
                    why_explanation = f"Moderate stockout risk observed across {risk_pct:.0f}% of stores. Inventory should be monitored before the next delivery."
                else:
                    why_explanation = f"Stable stock and steady sales observed across network stores ({risk_pct:.0f}% risk frequency)."

            # ── STEP 6: PRODUCT RESULT SUMMARY ──────────────────────────
            st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid {risk_status_color}; border-radius:10px; padding:12px 18px; margin:14px 0 12px 0; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
        <div>
            <div style="font-size:18px; font-weight:800; color:#0F172A;">SKU {target_pid}</div>
            <div style="font-size:13px; color:#64748B; margin-top:2px;">
                Department: <strong style="color:#0F172A;">{p_row['Department']}</strong> · Location: <strong style="color:#0F172A;">{location_label}</strong>
            </div>
        </div>
        <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:6px; padding:6px 14px; font-size:13px; font-weight:700; color:#0F172A;">
            Status: {status_badge}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

            # ── STEP 7: KEY RESULTS ─────────────────────────────────────
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Expected Demand", exp_demand_display, help=demand_subtext)
            k2.metric("Inventory Risk", risk_display)
            k3.metric("Priority", priority_display)
            k4.metric("Reorder Quantity", reorder_qty_display, help=reorder_subtext)

            # ── STEP 8: SALES TREND (HISTORICAL SALES) ───────────────────
            st.markdown("#### Sales Trend")
            try:
                if target_sid is not None and not store_specific_data.empty:
                    chart_df = store_specific_data.copy()
                    chart_df["dt"] = pd.to_datetime(chart_df["dt"]).dt.strftime("%b %d")
                    
                    fig_trend = go.Figure()
                    fig_trend.add_trace(go.Bar(
                        x=chart_df["dt"],
                        y=chart_df["actual_sales"],
                        name="Recorded Sales",
                        marker_color="#2563EB",
                        opacity=0.85
                    ))
                    fig_trend.add_trace(go.Scatter(
                        x=chart_df["dt"],
                        y=chart_df["predicted_sales"],
                        name="Expected Demand",
                        mode="lines+markers",
                        line=dict(color="#D97706", width=3, dash="dash"),
                        marker=dict(size=8, color="#D97706")
                    ))
                    fig_trend.update_layout(
                        title=dict(text=f"Sales Trend — SKU {target_pid} at Store {target_sid}", font=dict(size=14, color="#0F172A")),
                        height=280,
                        margin=dict(t=35, b=25, l=40, r=20),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        xaxis=dict(title=None, showgrid=False),
                        yaxis=dict(title="Units", showgrid=True, gridcolor="#E2E8F0")
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)
                else:
                    trend_data = load_product_forecast_trend(engine, target_pid)
                    if not trend_data.empty:
                        trend_data["dt"] = pd.to_datetime(trend_data["dt"]).dt.strftime("%b %d")
                        fig_trend = go.Figure()
                        fig_trend.add_trace(go.Bar(
                            x=trend_data["dt"],
                            y=trend_data["actual_sales"],
                            name="Recorded Sales (All Stores)",
                            marker_color="#2563EB",
                            opacity=0.85
                        ))
                        fig_trend.add_trace(go.Scatter(
                            x=trend_data["dt"],
                            y=trend_data["predicted_sales"],
                            name="Expected Demand (All Stores)",
                            mode="lines+markers",
                            line=dict(color="#D97706", width=3, dash="dash"),
                            marker=dict(size=8, color="#D97706")
                        ))
                        fig_trend.update_layout(
                            title=dict(text=f"Sales Trend — SKU {target_pid} (Network-Wide)", font=dict(size=14, color="#0F172A")),
                            height=280,
                            margin=dict(t=35, b=25, l=40, r=20),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            xaxis=dict(title=None, showgrid=False),
                            yaxis=dict(title="Units", showgrid=True, gridcolor="#E2E8F0")
                        )
                        st.plotly_chart(fig_trend, use_container_width=True)
                    else:
                        st.caption("Sales trend data is currently unavailable for this SKU.")
            except Exception as e:
                st.caption("Unable to render sales trend chart.")

            # ── STEP 11: WHY THIS NEEDS ATTENTION ────────────────────────
            st.markdown("#### Why This Needs Attention")
            st.markdown(f"""
<div style="background:#F8FAFC; border:1px solid #E2E8F0; border-left:4px solid #64748B; border-radius:8px; padding:12px 16px; font-size:13.5px; color:#1E293B; line-height:1.5;">
    {why_explanation}
</div>
""", unsafe_allow_html=True)

            # ── STEP 13, 14: RECOMMENDED ACTION & [ REVIEW RECOMMENDATION ] ──
            st.markdown("#### What Should I Do?")
            
            if "Action Required" in status_badge or "High" in risk_display:
                action_text = f"🔴 **Review the reorder recommendation.** Suggested reorder quantity: **{reorder_qty_display}**."
                action_detail = "Expected demand is outpacing inventory coverage. Review replenishment guidance to avoid imminent stockouts."
                action_card_color = "#FEF2F2"
                action_border_color = "#DC2626"
            elif "Attention" in status_badge or "Medium" in risk_display:
                action_text = f"🟡 **Monitor this product and review the reorder recommendation.** Suggested reorder quantity: **{reorder_qty_display}**."
                action_detail = "Moderate stockout frequency observed. Monitor store coverage and confirm replenishment before next delivery window."
                action_card_color = "#FFFBEB"
                action_border_color = "#D97706"
            else:
                action_text = f"🟢 **No immediate action is recommended.** Suggested reorder quantity: **{reorder_qty_display}**."
                action_detail = "Inventory fill rates are healthy. Maintain current replenishment cadence."
                action_card_color = "#F0FDF4"
                action_border_color = "#059669"

            act_col1, act_col2 = st.columns([3, 1])
            with act_col1:
                st.markdown(f"""
<div style="background:{action_card_color}; border:1px solid {action_border_color}; border-radius:8px; padding:12px 16px;">
    <div style="font-size:14px; font-weight:700; color:#0F172A;">{action_text}</div>
    <div style="font-size:12.5px; color:#475569; margin-top:3px;">{action_detail}</div>
</div>
""", unsafe_allow_html=True)
            with act_col2:
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                if st.button("Review Recommendation", type="primary", key="btn_review_rec", use_container_width=True):
                    st.session_state["nav_page"] = "Replenishment"
                    if target_sid is not None:
                        st.session_state["repl_store_filter"] = f"Store {target_sid}"
                    else:
                        st.session_state["repl_store_filter"] = "All Stores"
                    st.rerun()

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.divider()

    # ── STEP 15, 16: PRODUCT CATALOG & FILTERS ───────────────────
    st.markdown("### Product Catalog")
    st.caption("Browse all perishable produce items across the catalog:")

    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        dept_options = ["All Departments"] + sorted(list(set(DEPT_MAP.values())))
        sel_dept = st.selectbox("Department:", dept_options, key="catalog_dept_filter")
    with f_col2:
        risk_options = ["All Risks", "🔴 Action Required (≥50%)", "🟡 Attention (20-49%)", "🟢 Good (<20%)"]
        sel_risk = st.selectbox("Stockout Risk:", risk_options, key="catalog_risk_filter")
    with f_col3:
        prio_options = ["All Priorities", "🔴 HIGH Priority", "🟡 MEDIUM Priority", "🟢 LOW Priority"]
        sel_prio = st.selectbox("Priority:", prio_options, key="catalog_prio_filter")
    with f_col4:
        search_kw = st.text_input("Search SKU or Department:", placeholder="e.g. 267 or Berries", key="catalog_search_kw")

    filtered_prod = classified_prod.copy()
    if sel_dept != "All Departments":
        filtered_prod = filtered_prod[filtered_prod["Department"] == sel_dept]
    if "Action Required" in sel_risk:
        filtered_prod = filtered_prod[filtered_prod["high_risk_pct"] >= 50]
    elif "Attention" in sel_risk:
        filtered_prod = filtered_prod[(filtered_prod["high_risk_pct"] >= 20) & (filtered_prod["high_risk_pct"] < 50)]
    elif "Good" in sel_risk:
        filtered_prod = filtered_prod[filtered_prod["high_risk_pct"] < 20]

    if "HIGH" in sel_prio:
        filtered_prod = filtered_prod[filtered_prod["Replenishment Priority"] == "🔴 HIGH"]
    elif "MEDIUM" in sel_prio:
        filtered_prod = filtered_prod[filtered_prod["Replenishment Priority"] == "🟡 MEDIUM"]
    elif "LOW" in sel_prio:
        filtered_prod = filtered_prod[filtered_prod["Replenishment Priority"] == "🟢 LOW"]

    if search_kw.strip():
        kw = search_kw.strip().lower()
        filtered_prod = filtered_prod[
            filtered_prod["Department"].str.lower().str.contains(kw) |
            filtered_prod["product_id"].astype(str).str.contains(kw)
        ]

    st.caption(f"Showing **{len(filtered_prod):,}** matching products out of {len(prod_df):,} total catalog items.")

    prod_view_cols = ["Product Name", "Department", "predicted_sales", "total_sales", "avg_reorder_qty", "Stockout Risk", "Replenishment Priority"]
    prod_rename = {
        "Product Name": "Product",
        "Department": "Department",
        "predicted_sales": "Expected Demand (units/day)",
        "total_sales": "Historical Sales (units)",
        "avg_reorder_qty": "Suggested Reorder (units)",
        "Stockout Risk": "Stockout Risk",
        "Replenishment Priority": "Priority"
    }

    if not filtered_prod.empty:
        disp_df = filtered_prod[prod_view_cols].copy()
        disp_df["predicted_sales"] = disp_df["predicted_sales"].apply(lambda v: f"{float(v):.2f}")
        disp_df["total_sales"] = disp_df["total_sales"].apply(lambda v: f"{float(v):,.0f}")
        disp_df["avg_reorder_qty"] = disp_df["avg_reorder_qty"].apply(lambda v: f"{float(v):,.0f}")
        paginated_table(disp_df.rename(columns=prod_rename), key="catalog_prod_page")
    else:
        no_data_message("the chosen filter selection")





# ══════════════════════════════════════════════════════════════
# PAGE: DEMAND & FORECAST
# ══════════════════════════════════════════════════════════════

elif page == "Demand & Forecast":
    st.title("Demand & Forecast")
    st.markdown("""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid #2563EB; border-radius:10px; padding:14px 18px; margin:8px 0 18px 0; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="font-size:13.5px; color:#1E293B; line-height:1.6;">
        Compare historical sales with expected demand to understand future product needs across <strong>898 stores</strong>.
    </div>
</div>
""", unsafe_allow_html=True)

    try:
        store_df = get_stores()
        prod_df = get_products()
    except Exception as e:
        db_error_message(str(e)); st.stop()

    # STEP 2, 3, 4: PRODUCT & STORE SELECTION
    st.markdown("### Select Product & Store")
    st.caption("Select a product and store to view sales history and expected customer demand.")

    # Initialize state from existing navigation if set, or default
    if "fc_prod_id" not in st.session_state:
        st.session_state["fc_prod_id"] = st.session_state.get("analyzed_product_id", 267)
    if "fc_store_id" not in st.session_state:
        st.session_state["fc_store_id"] = st.session_state.get("analyzed_store_id", 631)

    p_list = sorted(prod_df["product_id"].unique().tolist())
    curr_fc_pid = st.session_state["fc_prod_id"]
    def_p_idx = p_list.index(curr_fc_pid) if curr_fc_pid in p_list else 0

    col_p, col_s, col_b = st.columns([2.5, 2, 1.2])
    with col_p:
        prod_options = [f"SKU {p} — {DEPT_MAP.get(int(p) % 7, 'Perishable Produce')}" for p in p_list]
        selected_prod_label = st.selectbox("Select Product:", prod_options, index=def_p_idx, key="fc_prod_select")
        import re
        m_pid = re.search(r'SKU (\d+)', selected_prod_label)
        chosen_pid = int(m_pid.group(1)) if m_pid else 267

    with col_s:
        try:
            available_stores = load_stores_for_product(engine, chosen_pid)
        except Exception:
            available_stores = []
        if not available_stores:
            available_stores = sorted(store_df["store_id"].unique().tolist())

        curr_fc_sid = st.session_state["fc_store_id"]
        def_s_idx = available_stores.index(curr_fc_sid) if curr_fc_sid in available_stores else 0
        store_options = [f"Store {s}" for s in available_stores]
        selected_store_label = st.selectbox("Select Store:", store_options, index=def_s_idx, key="fc_store_select")
        m_sid = re.search(r'Store (\d+)', selected_store_label)
        chosen_sid = int(m_sid.group(1)) if m_sid else 631

    with col_b:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        view_demand_btn = st.button("View Demand", type="primary", use_container_width=True)

    if view_demand_btn:
        st.session_state["fc_prod_id"] = chosen_pid
        st.session_state["fc_store_id"] = chosen_sid

    target_pid = st.session_state["fc_prod_id"]
    target_sid = st.session_state["fc_store_id"]

    # STEP 5: VALIDATION
    try:
        fc_df = load_store_product_forecast(engine, int(target_sid), int(target_pid))
    except Exception as e:
        db_error_message(str(e))
        fc_df = pd.DataFrame()

    if fc_df.empty:
        st.warning(f"No demand data found for SKU {target_pid} at Store {target_sid}.")
    else:
        if view_demand_btn:
            with st.spinner("Loading demand forecast..."):
                import time
                time.sleep(0.05)

        dept_name = DEPT_MAP.get(int(target_pid) % 7, "General Perishable Produce")
        latest = fc_df.iloc[-1]
        next_day_demand = round(float(latest["predicted_sales"]))
        avg_demand = float(fc_df["predicted_sales"].mean())
        tot_sales = float(fc_df["actual_sales"].sum())
        reorder_qty = float(latest.get("recommended_reorder_qty", 0))
        risk_badge = str(latest.get("stockout_risk", "LOW")).upper()

        # STEP 10: DEMAND CHANGE
        start_p = float(fc_df.iloc[0]["predicted_sales"])
        end_p = float(fc_df.iloc[-1]["predicted_sales"])
        pct_change = ((end_p - start_p) / max(0.1, start_p)) * 100

        if pct_change > 5:
            change_label = f"↑ Increasing (+{pct_change:.0f}%)"
            change_color = "#2563EB"
        elif pct_change < -5:
            change_label = f"↓ Decreasing ({pct_change:.0f}%)"
            change_color = "#DC2626"
        else:
            change_label = "→ Stable"
            change_color = "#059669"

        # STEP 11: DEMAND PATTERN (VARIABILITY)
        std_val = float(fc_df["actual_sales"].std())
        mean_val = float(fc_df["actual_sales"].mean())
        cv = std_val / max(0.1, mean_val)
        pattern_label = "Stable" if cv < 0.3 else "Changing"

        if risk_badge == "HIGH":
            status_color = "#DC2626"
            status_badge = "🔴 High Risk"
        elif risk_badge == "MEDIUM":
            status_color = "#D97706"
            status_badge = "🟡 Medium Risk"
        else:
            status_color = "#059669"
            status_badge = "🟢 Low Risk"

        # STEP 12: SIMPLE INSIGHT
        risk_exp = str(latest.get("risk_explanation", "")).strip()
        if not risk_exp:
            if pct_change > 5:
                risk_exp = f"Demand has been increasing recently, averaging {avg_demand:.1f} units/day."
            elif pct_change < -5:
                risk_exp = f"Demand has been trending downward recently, averaging {avg_demand:.1f} units/day."
            else:
                risk_exp = f"Demand has remained stable at approximately {avg_demand:.1f} units/day."

        # ── STEP 6: RESULT SUMMARY ──────────────────────────────────
        st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid {status_color}; border-radius:10px; padding:12px 18px; margin:14px 0 12px 0; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
        <div>
            <div style="font-size:18px; font-weight:800; color:#0F172A;">SKU {target_pid} · Store {target_sid}</div>
            <div style="font-size:13px; color:#64748B; margin-top:2px;">
                Department: <strong style="color:#0F172A;">{dept_name}</strong> · Date Range: <strong style="color:#0F172A;">6-Day Observation Window</strong>
            </div>
        </div>
        <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:6px; padding:6px 14px; font-size:13px; font-weight:700; color:#0F172A;">
            Status: {status_badge}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

        # 4 Key Result Metrics
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Expected Demand", f"{avg_demand:.1f} units/day", help="Average daily demand over observation period")
        k2.metric("Next-Day Demand", f"{next_day_demand:,} units", help="Projected next day demand")
        k3.metric("Demand Change", change_label)
        k4.metric("Demand Pattern", pattern_label, help="Demand stability based on sales variability")

        # ── STEP 7, 8, 9, 24: CHARTS (SALES TREND & FORECAST VS ACTUAL) ──
        chart_df = fc_df.copy()
        chart_df["dt_fmt"] = pd.to_datetime(chart_df["dt"]).dt.strftime("%b %d")

        ch_col1, ch_col2 = st.columns(2)
        with ch_col1:
            st.markdown("#### Sales Trend")
            fig_sales = go.Figure()
            fig_sales.add_trace(go.Bar(
                x=chart_df["dt_fmt"],
                y=chart_df["actual_sales"],
                name="Recorded Sales",
                marker_color="#2563EB",
                opacity=0.85
            ))
            fig_sales.update_layout(
                title=dict(text=f"Historical Sales — SKU {target_pid} at Store {target_sid}", font=dict(size=13, color="#0F172A")),
                height=280,
                margin=dict(t=35, b=25, l=40, r=20),
                xaxis=dict(title=None, showgrid=False),
                yaxis=dict(title="Units", showgrid=True, gridcolor="#E2E8F0")
            )
            st.plotly_chart(fig_sales, use_container_width=True)

        with ch_col2:
            st.markdown("#### Forecast vs Actual")
            fig_compare = go.Figure()
            fig_compare.add_trace(go.Scatter(
                x=chart_df["dt_fmt"],
                y=chart_df["actual_sales"],
                name="Recorded Sales",
                mode="lines+markers",
                line=dict(color="#475569", width=2.5, dash="dash"),
                marker=dict(size=7, color="#475569")
            ))
            fig_compare.add_trace(go.Scatter(
                x=chart_df["dt_fmt"],
                y=chart_df["predicted_sales"],
                name="Expected Demand",
                mode="lines+markers",
                line=dict(color="#D97706", width=3),
                marker=dict(size=8, color="#D97706")
            ))
            fig_compare.update_layout(
                title=dict(text=f"Expected Demand vs Sales — SKU {target_pid} at Store {target_sid}", font=dict(size=13, color="#0F172A")),
                height=280,
                margin=dict(t=35, b=25, l=40, r=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(title=None, showgrid=False),
                yaxis=dict(title="Units", showgrid=True, gridcolor="#E2E8F0")
            )
            st.plotly_chart(fig_compare, use_container_width=True)

        # ── STEP 12: WHAT THIS MEANS ────────────────────────────────
        st.markdown("#### What This Means")
        st.markdown(f"""
<div style="background:#F8FAFC; border:1px solid #E2E8F0; border-left:4px solid #64748B; border-radius:8px; padding:12px 16px; font-size:13.5px; color:#1E293B; line-height:1.5;">
    {risk_exp}
</div>
""", unsafe_allow_html=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # ── STEP 13, 14, 15, 16: WHAT SHOULD I DO? (NEXT STEPS) ──────
        st.markdown("#### What Should I Do?")
        if risk_badge == "HIGH":
            advice_text = f"🔴 **High Expected Demand:** Customer demand is running at **{avg_demand:.1f} units/day** with **{reorder_qty:,.0f} units** suggested replenishment to prevent stockouts."
            adv_bg = "#FEF2F2"
            adv_border = "#DC2626"
        elif risk_badge == "MEDIUM":
            advice_text = f"🟡 **Moderate Demand:** Expected demand is **{avg_demand:.1f} units/day**. Monitor stock levels before placing replenishment orders."
            adv_bg = "#FFFBEB"
            adv_border = "#D97706"
        else:
            advice_text = f"🟢 **Stable Demand:** Demand is steady at **{avg_demand:.1f} units/day**. Maintain normal replenishment cadence."
            adv_bg = "#F0FDF4"
            adv_border = "#059669"

        st.markdown(f"""
<div style="background:{adv_bg}; border:1px solid {adv_border}; border-radius:8px; padding:12px 16px; margin-bottom:12px;">
    <div style="font-size:13.5px; font-weight:600; color:#0F172A;">{advice_text}</div>
</div>
""", unsafe_allow_html=True)

        btn_c1, btn_c2, btn_c3 = st.columns(3)
        with btn_c1:
            if st.button("View Product", key="btn_fc_view_prod", use_container_width=True):
                st.session_state["nav_page"] = "Products"
                st.session_state["analyzed_product_id"] = int(target_pid)
                st.session_state["analyzed_store"] = f"Store {target_sid}"
                st.rerun()

        with btn_c2:
            if st.button("View Inventory Risk", key="btn_fc_view_risk", use_container_width=True):
                st.session_state["nav_page"] = "Inventory Risk"
                st.rerun()

        with btn_c3:
            if st.button("Review Replenishment", type="primary", key="btn_fc_review_repl", use_container_width=True):
                st.session_state["nav_page"] = "Replenishment"
                st.session_state["repl_store_filter"] = f"Store {target_sid}"
                st.rerun()

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        st.divider()

        # ── STEP 26: DAILY BREAKDOWN TABLE ──────────────────────────
        st.markdown("#### Daily Breakdown")
        st.caption("Day-by-day comparison of recorded sales, expected customer demand, difference, and replenishment buffer:")

        disp_table = fc_df.copy()
        disp_table["dt_str"] = pd.to_datetime(disp_table["dt"]).dt.strftime("%d %b %Y")
        disp_table["difference"] = (disp_table["predicted_sales"] - disp_table["actual_sales"]).apply(lambda v: f"{float(v):+.1f}")
        disp_table["actual_sales"] = disp_table["actual_sales"].apply(lambda v: f"{float(v):.1f}")
        disp_table["predicted_sales"] = disp_table["predicted_sales"].apply(lambda v: f"{float(v):.1f}")
        disp_table["recommended_reorder_qty"] = disp_table["recommended_reorder_qty"].apply(lambda v: f"{float(v):,.0f}")
        disp_table["stockout_risk"] = disp_table["stockout_risk"].map(lambda r: "🔴 High" if r == "HIGH" else ("🟡 Medium" if r == "MEDIUM" else "🟢 Low"))

        cols_show = ["dt_str", "actual_sales", "predicted_sales", "difference", "stockout_risk", "recommended_reorder_qty"]
        rename_map = {
            "dt_str": "Date",
            "actual_sales": "Recorded Sales (units)",
            "predicted_sales": "Expected Demand (units)",
            "difference": "Difference (units)",
            "stockout_risk": "Stockout Risk",
            "recommended_reorder_qty": "Suggested Reorder (units)"
        }
        st.dataframe(disp_table[cols_show].rename(columns=rename_map), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════
# PAGE: INVENTORY RISK
# ══════════════════════════════════════════════════════════════

elif page == "Inventory Risk":
    st.title("Inventory Risk")
    st.markdown("""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid #0F766E; border-radius:10px; padding:14px 18px; margin:8px 0 16px 0;">
    <div style="font-size:16px; font-weight:800; color:#0F172A;">Inventory Risk</div>
    <div style="font-size:13px; color:#64748B; margin-top:2px;">
        Find products and stores that need attention, understand why, and take immediate action.
    </div>
</div>
""", unsafe_allow_html=True)

    # ── SESSION STATE PRE-FILLS ──────────────────────────────────
    pre_store = st.session_state.get("analyzed_store_id")
    if pre_store is None:
        raw_pre_store = st.session_state.get("analyzed_store")
        if raw_pre_store and str(raw_pre_store).startswith("Store "):
            try:
                pre_store = int(str(raw_pre_store).replace("Store ", "").strip())
            except ValueError:
                pre_store = None

    pre_sku = st.session_state.get("analyzed_product_id")

    # ── STEP 7 & 8: FILTERS ───────────────────────────────────────
    st.markdown("#### Filter Inventory Risks")
    f_c1, f_c2, f_c3, f_c4, f_c5 = st.columns([1.2, 1.2, 1.4, 1.2, 1.2])

    with f_c1:
        risk_options = ["High Risk", "Medium Risk", "Low Risk", "All"]
        sel_risk = st.selectbox("Risk Level:", risk_options, index=0, key="ir_filter_risk")

    with f_c2:
        try:
            stores_df = get_stores()
            avail_stores = sorted(stores_df['store_id'].unique().tolist())
            stores_list = ["All Stores"] + [f"Store {s}" for s in avail_stores]
        except Exception:
            stores_list = ["All Stores"] + [f"Store {s}" for s in range(50)]

        def_store_idx = 0
        if pre_store is not None:
            match_str = f"Store {pre_store}"
            if match_str in stores_list:
                def_store_idx = stores_list.index(match_str)

        sel_store_str = st.selectbox("Store:", stores_list, index=def_store_idx, key="ir_filter_store")
        sel_store_id = int(sel_store_str.replace("Store ", "")) if sel_store_str != "All Stores" else None

    with f_c3:
        dept_options = ["All Departments"] + [DEPT_MAP[k] for k in sorted(DEPT_MAP.keys())]
        sel_dept_str = st.selectbox("Department:", dept_options, index=0, key="ir_filter_dept")
        inv_dept_map = {v: k for k, v in DEPT_MAP.items()}
        sel_dept_id = inv_dept_map.get(sel_dept_str)

    with f_c4:
        priority_options = ["All Priorities", "Urgent", "Monitor", "Normal"]
        sel_priority = st.selectbox("Priority:", priority_options, index=0, key="ir_filter_priority")

    with f_c5:
        sort_options = ["Highest Reorder Quantity", "Highest Expected Demand", "Highest Risk"]
        sel_sort = st.selectbox("Sort By:", sort_options, index=0, key="ir_filter_sort")

    # SKU Search & Filter Reset
    sku_c1, sku_c2 = st.columns([3.5, 1])
    with sku_c1:
        sku_search = st.text_input(
            "Search by SKU ID (optional):",
            value=str(pre_sku) if pre_sku is not None else "",
            placeholder="e.g. 267",
            key="ir_search_sku"
        ).strip()
    with sku_c2:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if st.button("Reset Filters", key="ir_reset_filters", use_container_width=True):
            st.session_state.pop("analyzed_store_id", None)
            st.session_state.pop("analyzed_store", None)
            st.session_state.pop("analyzed_product_id", None)
            st.rerun()

    # ── STEP 3: RISK SUMMARY CARDS ───────────────────────────────
    try:
        summary_counts = load_risk_summary_counts(
            engine,
            store_id=sel_store_id,
            department_id=sel_dept_id
        )
    except Exception:
        summary_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "TOTAL": 0}

    high_cnt = summary_counts.get("HIGH", 0)
    med_cnt = summary_counts.get("MEDIUM", 0)
    low_cnt = summary_counts.get("LOW", 0)

    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #FECACA; border-top:4px solid #DC2626; border-radius:10px; padding:14px 16px; box-shadow:0 1px 3px rgba(0,0,0,0.04); text-align:center;">
    <div style="font-size:11px; font-weight:700; color:#DC2626; letter-spacing:0.8px; text-transform:uppercase;">🔴 High Risk</div>
    <div style="font-size:26px; font-weight:800; color:#0F172A; margin-top:3px;">{high_cnt:,}</div>
    <div style="font-size:12px; color:#64748B; margin-top:2px;">Needs attention</div>
</div>
""", unsafe_allow_html=True)
    with r2:
        st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #FDE68A; border-top:4px solid #D97706; border-radius:10px; padding:14px 16px; box-shadow:0 1px 3px rgba(0,0,0,0.04); text-align:center;">
    <div style="font-size:11px; font-weight:700; color:#D97706; letter-spacing:0.8px; text-transform:uppercase;">🟡 Medium Risk</div>
    <div style="font-size:26px; font-weight:800; color:#0F172A; margin-top:3px;">{med_cnt:,}</div>
    <div style="font-size:12px; color:#64748B; margin-top:2px;">Needs monitoring</div>
</div>
""", unsafe_allow_html=True)
    with r3:
        st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #A7F3D0; border-top:4px solid #059669; border-radius:10px; padding:14px 16px; box-shadow:0 1px 3px rgba(0,0,0,0.04); text-align:center;">
    <div style="font-size:11px; font-weight:700; color:#059669; letter-spacing:0.8px; text-transform:uppercase;">🟢 Low Risk</div>
    <div style="font-size:26px; font-weight:800; color:#0F172A; margin-top:3px;">{low_cnt:,}</div>
    <div style="font-size:12px; color:#64748B; margin-top:2px;">Currently stable</div>
</div>
""", unsafe_allow_html=True)

    # ── DATABASE QUERY ───────────────────────────────────────────
    risk_map = {"High Risk": ["HIGH"], "Medium Risk": ["MEDIUM"], "Low Risk": ["LOW"], "All": None}
    priority_map = {"Urgent": ["HIGH"], "Monitor": ["MEDIUM"], "Normal": ["LOW"], "All Priorities": None}
    sort_map = {
        "Highest Reorder Quantity": "recommended_reorder_qty",
        "Highest Expected Demand": "predicted_sales",
        "Highest Risk": "stockout_risk"
    }

    parsed_pid = None
    if sku_search:
        try:
            parsed_pid = int(sku_search.replace("SKU", "").strip())
        except ValueError:
            parsed_pid = -1

    try:
        risk_df = load_forecast_recommendations(
            engine,
            store_id=sel_store_id,
            product_id=parsed_pid if (parsed_pid is not None and parsed_pid >= 0) else None,
            risk_levels=risk_map.get(sel_risk),
            priorities=priority_map.get(sel_priority),
            department_id=sel_dept_id,
            latest_only=True,
            sort_by=sort_map.get(sel_sort, "recommended_reorder_qty"),
            limit=20
        )
    except Exception as e:
        db_error_message(f"Unable to load inventory risk data: {e}")
        risk_df = pd.DataFrame()

    # ── STEP 5: PRODUCTS NEEDING ATTENTION ───────────────────────
    st.markdown("---")
    st.markdown("### Products Needing Attention")
    st.caption("Review calculated risk records, expected demand, and suggested replenishment quantities:")

    if parsed_pid == -1:
        st.info("Please enter a valid numeric SKU ID (e.g. 267).")
    elif risk_df.empty:
        st.info("No products match the selected filters. Try broadening your filter criteria.")
    else:
        disp_df = risk_df.copy()
        disp_df["Product"] = disp_df.apply(
            lambda r: f"SKU {int(r['product_id'])} — {DEPT_MAP.get(int(r.get('management_group_id', 6)), 'Produce')}",
            axis=1
        )
        disp_df["Store"] = disp_df["store_id"].apply(lambda s: f"Store {s}")
        disp_df["Expected Demand"] = disp_df["predicted_sales"].apply(lambda v: f"{v:.1f} units/day")
        disp_df["Risk"] = disp_df["stockout_risk"].map({
            "HIGH": "🔴 High Risk",
            "MEDIUM": "🟡 Medium Risk",
            "LOW": "🟢 Low Risk"
        }).fillna("🟢 Low Risk")
        disp_df["Priority"] = disp_df["replenishment_priority"].map({
            "HIGH": "🔴 Urgent",
            "MEDIUM": "🟡 Monitor",
            "LOW": "🟢 Normal"
        }).fillna("🟢 Normal")
        disp_df["Reorder Quantity"] = disp_df["recommended_reorder_qty"].apply(lambda v: f"{v:,.0f} units")

        cols_to_show = ["Product", "Store", "Expected Demand", "Risk", "Priority", "Reorder Quantity"]
        st.dataframe(disp_df[cols_to_show], use_container_width=True, hide_index=True)

        # ── STEP 6, 20: SELECTED RISK DETAIL ──────────────────────────
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        st.markdown("### Inspect Risk & Take Action")
        st.caption("Select a record below to view why it needs attention and review recommended actions:")

        options_list = []
        for _, row in risk_df.iterrows():
            p_id = int(row['product_id'])
            s_id = int(row['store_id'])
            r_badge = "🔴 High" if row['stockout_risk'] == "HIGH" else ("🟡 Medium" if row['stockout_risk'] == "MEDIUM" else "🟢 Low")
            r_qty = f"{row['recommended_reorder_qty']:,.0f} units"
            options_list.append(f"SKU {p_id} @ Store {s_id} ({r_badge} · {r_qty})")

        selected_str = st.selectbox(
            "Select a record to inspect details:",
            options_list,
            index=0,
            key="ir_selected_record"
        )
        selected_idx = options_list.index(selected_str)
        selected_record = risk_df.iloc[selected_idx]

        sel_pid = int(selected_record["product_id"])
        sel_sid = int(selected_record["store_id"])
        sel_risk_val = str(selected_record["stockout_risk"]).upper()
        sel_priority_val = str(selected_record["replenishment_priority"]).upper()
        sel_pred = float(selected_record["predicted_sales"])
        sel_reorder = float(selected_record["recommended_reorder_qty"])
        sel_actual = float(selected_record.get("actual_sales", 0))
        sel_dept_name = DEPT_MAP.get(int(selected_record.get("management_group_id", 6)), "Produce")
        sel_explanation = str(selected_record.get("risk_explanation", "")).strip()

        if not sel_explanation:
            sel_explanation = "Recent customer demand and historical stockout patterns indicate this product needs attention."

        if sel_risk_val == "HIGH":
            badge_html = "<span style='background:#FEE2E2; color:#B91C1C; font-weight:700; padding:4px 10px; border-radius:6px; font-size:12px;'>🔴 High Risk</span>"
            card_border = "#DC2626"
            action_text = f"Review the replenishment recommendation immediately and replenish <strong>{sel_reorder:,.0f} units</strong> to prevent stockouts under expected demand of <strong>{sel_pred:.1f} units/day</strong>."
        elif sel_risk_val == "MEDIUM":
            badge_html = "<span style='background:#FEF3C7; color:#B45309; font-weight:700; padding:4px 10px; border-radius:6px; font-size:12px;'>🟡 Medium Risk</span>"
            card_border = "#D97706"
            action_text = f"Monitor daily sales and review replenishment before demand peaks. Suggested reorder: <strong>{sel_reorder:,.0f} units</strong>."
        else:
            badge_html = "<span style='background:#D1FAE5; color:#047857; font-weight:700; padding:4px 10px; border-radius:6px; font-size:12px;'>🟢 Low Risk</span>"
            card_border = "#059669"
            action_text = "Stock is currently stable under expected demand. Maintain normal replenishment schedule."

        priority_badge_html = "<span style='background:#F1F5F9; color:#334155; font-weight:600; padding:4px 8px; border-radius:6px; font-size:12px;'>" + ("🔴 Urgent Priority" if sel_priority_val == "HIGH" else ("🟡 Monitor Priority" if sel_priority_val == "MEDIUM" else "🟢 Normal Priority")) + "</span>"

        st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid {card_border}; border-radius:10px; padding:18px 20px; margin:12px 0 16px 0; box-shadow:0 1px 4px rgba(0,0,0,0.03);">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
        <div>
            <div style="font-size:18px; font-weight:800; color:#0F172A;">SKU {sel_pid} &bull; Store {sel_sid}</div>
            <div style="font-size:13px; color:#64748B; margin-top:2px;">
                Department: <strong style="color:#0F172A;">{sel_dept_name}</strong>
            </div>
        </div>
        <div style="display:flex; gap:8px; align-items:center;">
            {priority_badge_html}
            {badge_html}
        </div>
    </div>
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:12px; margin-top:16px; padding:12px; background:#F8FAFC; border-radius:8px; border:1px solid #E2E8F0;">
        <div>
            <div style="font-size:11px; font-weight:600; color:#64748B; text-transform:uppercase;">Expected Demand</div>
            <div style="font-size:17px; font-weight:800; color:#0F172A; margin-top:2px;">{sel_pred:.1f} <span style="font-size:12px; font-weight:500; color:#64748B;">units/day</span></div>
        </div>
        <div>
            <div style="font-size:11px; font-weight:600; color:#64748B; text-transform:uppercase;">Suggested Reorder</div>
            <div style="font-size:17px; font-weight:800; color:#0F172A; margin-top:2px;">{sel_reorder:,.0f} <span style="font-size:12px; font-weight:500; color:#64748B;">units</span></div>
        </div>
        <div>
            <div style="font-size:11px; font-weight:600; color:#64748B; text-transform:uppercase;">Recorded Sales</div>
            <div style="font-size:17px; font-weight:800; color:#0F172A; margin-top:2px;">{sel_actual:.1f} <span style="font-size:12px; font-weight:500; color:#64748B;">units</span></div>
        </div>
    </div>
    <div style="margin-top:14px;">
        <div style="font-size:12.5px; font-weight:700; color:#0F172A; text-transform:uppercase; letter-spacing:0.5px;">Why This Needs Attention:</div>
        <div style="font-size:13px; color:#334155; margin-top:4px; line-height:1.5; background:#F1F5F9; border-left:3px solid #64748B; padding:8px 12px; border-radius:0 6px 6px 0;">
            {sel_explanation}
        </div>
    </div>
    <div style="margin-top:12px;">
        <div style="font-size:12.5px; font-weight:700; color:#0F172A; text-transform:uppercase; letter-spacing:0.5px;">Recommended Action:</div>
        <div style="font-size:13px; color:#334155; margin-top:4px; line-height:1.5;">
            {action_text}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

        # ── STEP 10, 11, 12: CONNECTED ACTION BUTTONS ─────────────────
        act_c1, act_c2, act_c3 = st.columns(3)
        with act_c1:
            if st.button("View Product", key="btn_ir_view_product", use_container_width=True):
                st.session_state["nav_page"] = "Products"
                st.session_state["analyzed_product_id"] = sel_pid
                st.session_state["analyzed_store"] = f"Store {sel_sid}"
                st.session_state["curr_selected_store"] = sel_sid
                st.rerun()

        with act_c2:
            if st.button("View Store", key="btn_ir_view_store", use_container_width=True):
                st.session_state["nav_page"] = "Stores"
                st.session_state["analyzed_store_id"] = sel_sid
                st.rerun()

        with act_c3:
            if st.button("Review Recommendation", key="btn_ir_review_reorder", use_container_width=True):
                st.session_state["nav_page"] = "Replenishment"
                st.session_state["repl_store_filter"] = sel_sid
                st.rerun()

    # ── STEP 13: HOW RISK IS CLASSIFIED ───────────────────────────
    st.markdown("""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:16px 20px; margin-top:24px;">
    <div style="font-size:14px; font-weight:700; color:#0F172A; margin-bottom:4px;">How Risk Is Classified</div>
    <div style="font-size:12.5px; color:#64748B; margin-bottom:14px;">High Risk means the product needs attention based on the existing demand and stock-related analysis.</div>
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:14px; font-size:12.5px;">
        <div style="border-left:3px solid #DC2626; padding:10px 14px; background:#FEF2F2; border-radius:0 8px 8px 0;">
            <div style="color:#DC2626; font-size:13px; font-weight:700;">🔴 High Risk</div>
            <div style="font-size:12px; font-weight:600; color:#991B1B; margin-top:2px;">Needs attention</div>
            <div style="margin-top:4px; font-size:12px; color:#7F1D1D; line-height:1.4;">
                High Risk means this product needs attention based on the current demand and stock-related analysis.
            </div>
        </div>
        <div style="border-left:3px solid #D97706; padding:10px 14px; background:#FFFBEB; border-radius:0 8px 8px 0;">
            <div style="color:#D97706; font-size:13px; font-weight:700;">🟡 Medium Risk</div>
            <div style="font-size:12px; font-weight:600; color:#92400E; margin-top:2px;">Needs monitoring</div>
            <div style="margin-top:4px; font-size:12px; color:#92400E; line-height:1.4;">
                Medium Risk means inventory should be monitored before the next delivery cycle.
            </div>
        </div>
        <div style="border-left:3px solid #059669; padding:10px 14px; background:#ECFDF5; border-radius:0 8px 8px 0;">
            <div style="color:#059669; font-size:13px; font-weight:700;">🟢 Low Risk</div>
            <div style="font-size:12px; font-weight:600; color:#065F46; margin-top:2px;">Currently stable</div>
            <div style="margin-top:4px; font-size:12px; color:#065F46; line-height:1.4;">
                Low Risk means inventory is currently performing normally with steady sales.
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)




# ══════════════════════════════════════════════════════════════
# PAGE: REPLENISHMENT / REORDER PLANNER
# ══════════════════════════════════════════════════════════════

elif page == "Replenishment":
    st.title("Replenishment")
    st.markdown("""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid #0284C7; border-radius:10px; padding:14px 18px; margin:8px 0 16px 0;">
    <div style="font-size:16px; font-weight:800; color:#0F172A;">Replenishment</div>
    <div style="font-size:13px; color:#64748B; margin-top:2px;">
        Review reorder recommendations and decide what to do.
    </div>
</div>
""", unsafe_allow_html=True)

    # ── SESSION STATE PRE-FILLS ──────────────────────────────────
    pre_store = st.session_state.get("repl_store_filter")
    if pre_store is None:
        pre_store = st.session_state.get("analyzed_store_id")
        if pre_store is None:
            raw_s = st.session_state.get("analyzed_store")
            if raw_s and str(raw_s).startswith("Store "):
                try:
                    pre_store = int(str(raw_s).replace("Store ", "").strip())
                except ValueError:
                    pre_store = None

    pre_sku = st.session_state.get("analyzed_product_id")

    # ── FILTERS ──────────────────────────────────────────────────
    st.markdown("#### Filter Recommendations")
    fcol1, fcol2, fcol3, fcol4 = st.columns([1.5, 1.2, 1.2, 1.5])
    with fcol1:
        try:
            stores_df = get_stores()
            avail_stores = sorted(stores_df['store_id'].unique().tolist())
            all_stores_list = ["All Stores"] + [f"Store {s}" for s in avail_stores]
        except Exception:
            all_stores_list = ["All Stores"] + [f"Store {s}" for s in range(50)]

        def_store_idx = 0
        if pre_store is not None:
            match_str = f"Store {pre_store}"
            if match_str in all_stores_list:
                def_store_idx = all_stores_list.index(match_str)

        store_choice = st.selectbox("Store Location:", all_stores_list, index=def_store_idx, key="repl_store_filter_box")
        target_store_id = None if store_choice == "All Stores" else int(store_choice.replace("Store ", ""))

    with fcol2:
        priority_choice = st.selectbox("Priority:", ["All Priorities", "🔴 Urgent", "🟡 Monitor", "🟢 Normal"], index=0, key="repl_priority_filter_box")
        priority_filter = None if priority_choice == "All Priorities" else (["HIGH"] if "Urgent" in priority_choice else (["MEDIUM"] if "Monitor" in priority_choice else ["LOW"]))

    with fcol3:
        risk_choice = st.selectbox("Risk Level:", ["All Risk Levels", "🔴 High Risk", "🟡 Medium Risk", "🟢 Low Risk"], index=0, key="repl_risk_filter_box")
        risk_filter = None if risk_choice == "All Risk Levels" else (["HIGH"] if "High" in risk_choice else (["MEDIUM"] if "Medium" in risk_choice else ["LOW"]))

    with fcol4:
        dept_choice = st.selectbox("Department:", ["All Departments"] + [DEPT_MAP[k] for k in sorted(DEPT_MAP.keys())], index=0, key="repl_dept_filter_box")
        inv_dept_map = {v: k for k, v in DEPT_MAP.items()}
        dept_id_filter = inv_dept_map.get(dept_choice)

    # Optional SKU Search & Reset Filters
    s_col1, s_col2 = st.columns([3.5, 1])
    with s_col1:
        sku_search = st.text_input(
            "Filter by SKU ID (optional):",
            value=str(pre_sku) if pre_sku is not None else "",
            placeholder="e.g. 267",
            key="repl_search_sku"
        ).strip()
    with s_col2:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if st.button("Reset Filters", key="repl_reset_filters_btn", use_container_width=True):
            st.session_state.pop("repl_store_filter", None)
            st.session_state.pop("analyzed_store_id", None)
            st.session_state.pop("analyzed_store", None)
            st.session_state.pop("analyzed_product_id", None)
            st.rerun()

    parsed_pid = None
    if sku_search:
        try:
            parsed_pid = int(sku_search.replace("SKU", "").strip())
        except ValueError:
            parsed_pid = -1

    # ── LOAD REAL REPLENISHMENT DECISIONS MADE TODAY ──────────────
    try:
        today_decisions = load_today_decisions(engine)
        dec_summary = load_replenishment_decision_summary(engine)
    except Exception:
        today_decisions = {}
        dec_summary = {"total_decisions": 0, "approved_count": 0, "modified_count": 0, "rejected_count": 0, "total_approved_units": 0}

    # ── QUERY RECOMMENDATIONS ────────────────────────────────────
    if parsed_pid == -1:
        recs = pd.DataFrame()
    else:
        try:
            recs = load_forecast_recommendations(
                engine,
                store_id=target_store_id,
                product_id=parsed_pid if (parsed_pid is not None and parsed_pid >= 0) else None,
                risk_levels=risk_filter,
                priorities=priority_filter,
                department_id=dept_id_filter,
                latest_only=True,
                limit=100
            )
        except Exception as e:
            db_error_message(f"Unable to load recommendations: {e}")
            recs = pd.DataFrame()

    # ── SUMMARY METRICS CARDS ────────────────────────────────────
    tot_orders = len(recs)
    urgent_orders = int((recs['replenishment_priority'] == 'HIGH').sum()) if not recs.empty else 0
    tot_units = float(recs['recommended_reorder_qty'].sum()) if not recs.empty else 0.0
    decisions_today_cnt = len(today_decisions)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #BAE6FD; border-top:4px solid #0284C7; border-radius:10px; padding:14px 16px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="font-size:11px; font-weight:700; color:#0284C7; text-transform:uppercase;">Recommendations</div>
    <div style="font-size:24px; font-weight:800; color:#0F172A; margin-top:3px;">{tot_orders:,}</div>
    <div style="font-size:12px; color:#64748B; margin-top:2px;">Matching filters</div>
</div>
""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #FECACA; border-top:4px solid #DC2626; border-radius:10px; padding:14px 16px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="font-size:11px; font-weight:700; color:#DC2626; text-transform:uppercase;">🔴 Urgent Reorders</div>
    <div style="font-size:24px; font-weight:800; color:#0F172A; margin-top:3px;">{urgent_orders:,}</div>
    <div style="font-size:12px; color:#64748B; margin-top:2px;">Review required</div>
</div>
""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #FDE68A; border-top:4px solid #D97706; border-radius:10px; padding:14px 16px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="font-size:11px; font-weight:700; color:#D97706; text-transform:uppercase;">Suggested Volume</div>
    <div style="font-size:24px; font-weight:800; color:#0F172A; margin-top:3px;">{tot_units:,.0f}</div>
    <div style="font-size:12px; color:#64748B; margin-top:2px;">Total recommended units</div>
</div>
""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #A7F3D0; border-top:4px solid #059669; border-radius:10px; padding:14px 16px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="font-size:11px; font-weight:700; color:#059669; text-transform:uppercase;">Decisions Today</div>
    <div style="font-size:24px; font-weight:800; color:#0F172A; margin-top:3px;">{decisions_today_cnt:,}</div>
    <div style="font-size:12px; color:#64748B; margin-top:2px;">Saved to database</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    # ── STEP 6: RECOMMENDATION TABLE ──────────────────────────────
    st.markdown("### Reorder Recommendations")
    st.caption("Review calculated replenishment recommendations, expected demand, and recorded decisions:")

    if parsed_pid == -1:
        st.info("Please enter a valid numeric SKU ID (e.g. 267).")
    elif recs.empty:
        st.info("No recommendations match your filters. Try broadening your filter criteria.")
    else:
        disp_recs = recs.copy()
        disp_recs["Product"] = disp_recs.apply(
            lambda r: f"SKU {int(r['product_id'])} — {DEPT_MAP.get(int(r.get('management_group_id', 6)), 'Produce')}",
            axis=1
        )
        disp_recs["Store"] = disp_recs["store_id"].apply(lambda s: f"Store {s}")
        disp_recs["Expected Demand"] = disp_recs["predicted_sales"].apply(lambda v: f"{v:.1f} units/day")
        disp_recs["Risk"] = disp_recs["stockout_risk"].map({
            "HIGH": "🔴 High Risk",
            "MEDIUM": "🟡 Medium Risk",
            "LOW": "🟢 Low Risk"
        }).fillna("🟢 Low Risk")
        disp_recs["Priority"] = disp_recs["replenishment_priority"].map({
            "HIGH": "🔴 Urgent",
            "MEDIUM": "🟡 Monitor",
            "LOW": "🟢 Normal"
        }).fillna("🟢 Normal")
        disp_recs["Suggested Reorder"] = disp_recs["recommended_reorder_qty"].apply(lambda v: f"{v:,.0f} units")

        def map_decision_status(row):
            key = (int(row["store_id"]), int(row["product_id"]))
            dec = today_decisions.get(key)
            if not dec:
                return "Pending Review"
            status = dec["status"]
            qty = dec["approved_qty"]
            if status == "APPROVED":
                return f"🟢 Approved ({qty:,.0f}u)"
            elif status == "MODIFIED":
                return f"🟡 Modified ({qty:,.0f}u)"
            elif status == "REJECTED":
                return "⚪ Rejected"
            else:
                return f"⚪ {status.capitalize()}"

        disp_recs["Decision Status"] = disp_recs.apply(map_decision_status, axis=1)
        disp_recs["Reason"] = disp_recs["risk_explanation"]

        table_cols = ["Product", "Store", "Expected Demand", "Risk", "Priority", "Suggested Reorder", "Decision Status", "Reason"]
        st.dataframe(disp_recs[table_cols], use_container_width=True, hide_index=True)

        # ── STEP 7 & 8: REVIEW & DECISION DETAIL ──────────────────────
        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        st.markdown("### Review & Decision")
        st.caption("Select a recommendation below to review why it was recommended and save your decision:")

        rec_options = []
        for _, row in recs.head(40).iterrows():
            p_id = int(row['product_id'])
            s_id = int(row['store_id'])
            q = float(row['recommended_reorder_qty'])
            dec = today_decisions.get((s_id, p_id))
            status_label = f" [{dec['status']}: {dec['approved_qty']:.0f} units]" if dec else " [Pending]"
            rec_options.append(f"SKU {p_id} @ Store {s_id} — Suggested: {q:,.0f} units{status_label}")

        sel_rec_str = st.selectbox(
            "Select a recommendation to review:",
            rec_options,
            index=0,
            key="repl_selected_rec_box"
        )
        selected_idx = rec_options.index(sel_rec_str)
        selected_row = recs.iloc[selected_idx]

        sel_pid = int(selected_row["product_id"])
        sel_sid = int(selected_row["store_id"])
        sel_pred = float(selected_row["predicted_sales"])
        sel_reorder = float(selected_row["recommended_reorder_qty"])
        sel_actual = float(selected_row.get("actual_sales", 0))
        sel_risk = str(selected_row["stockout_risk"]).upper()
        sel_priority = str(selected_row["replenishment_priority"]).upper()
        sel_dept = DEPT_MAP.get(int(selected_row.get("management_group_id", 6)), "Produce")
        sel_why = str(selected_row.get("risk_explanation", "")).strip()

        if not sel_why:
            sel_why = f"Recent customer demand and stockout patterns indicate {sel_reorder:,.0f} units needed to cover expected demand."

        existing_decision = today_decisions.get((sel_sid, sel_pid))

        # Status Badges
        r_badge_html = "<span style='background:#FEE2E2; color:#B91C1C; font-weight:700; padding:4px 10px; border-radius:6px; font-size:12px;'>🔴 High Risk</span>" if sel_risk == "HIGH" else ("<span style='background:#FEF3C7; color:#B45309; font-weight:700; padding:4px 10px; border-radius:6px; font-size:12px;'>🟡 Medium Risk</span>" if sel_risk == "MEDIUM" else "<span style='background:#D1FAE5; color:#047857; font-weight:700; padding:4px 10px; border-radius:6px; font-size:12px;'>🟢 Low Risk</span>")
        p_badge_html = "<span style='background:#F1F5F9; color:#334155; font-weight:600; padding:4px 8px; border-radius:6px; font-size:12px;'>" + ("🔴 Urgent Priority" if sel_priority == "HIGH" else ("🟡 Monitor Priority" if sel_priority == "MEDIUM" else "🟢 Normal Priority")) + "</span>"

        if existing_decision:
            ed_status = existing_decision["status"]
            ed_qty = existing_decision["approved_qty"]
            if ed_status == "APPROVED":
                cur_dec_html = f"<span style='background:#DCFCE7; color:#166534; font-weight:700; padding:4px 10px; border-radius:6px; font-size:12px;'>Decision: Approved ({ed_qty:,.0f} units)</span>"
            elif ed_status == "MODIFIED":
                cur_dec_html = f"<span style='background:#FEF9C3; color:#854D0E; font-weight:700; padding:4px 10px; border-radius:6px; font-size:12px;'>Decision: Modified ({ed_qty:,.0f} units)</span>"
            elif ed_status == "REJECTED":
                cur_dec_html = "<span style='background:#F1F5F9; color:#475569; font-weight:700; padding:4px 10px; border-radius:6px; font-size:12px;'>Decision: Rejected</span>"
            else:
                cur_dec_html = f"<span style='background:#E2E8F0; color:#334155; font-weight:700; padding:4px 10px; border-radius:6px; font-size:12px;'>Decision: {ed_status.capitalize()}</span>"
        else:
            cur_dec_html = "<span style='background:#EFF6FF; color:#1D4ED8; font-weight:600; padding:4px 10px; border-radius:6px; font-size:12px;'>Status: Pending Review</span>"

        st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid #0284C7; border-radius:10px; padding:18px 20px; margin:12px 0 16px 0; box-shadow:0 1px 4px rgba(0,0,0,0.03);">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
        <div>
            <div style="font-size:18px; font-weight:800; color:#0F172A;">SKU {sel_pid} &bull; Store {sel_sid}</div>
            <div style="font-size:13px; color:#64748B; margin-top:2px;">
                Department: <strong style="color:#0F172A;">{sel_dept}</strong>
            </div>
        </div>
        <div style="display:flex; gap:8px; align-items:center;">
            {p_badge_html}
            {r_badge_html}
            {cur_dec_html}
        </div>
    </div>
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:12px; margin-top:16px; padding:12px; background:#F8FAFC; border-radius:8px; border:1px solid #E2E8F0;">
        <div>
            <div style="font-size:11px; font-weight:600; color:#64748B; text-transform:uppercase;">Expected Demand</div>
            <div style="font-size:17px; font-weight:800; color:#0F172A; margin-top:2px;">{sel_pred:.1f} <span style="font-size:12px; font-weight:500; color:#64748B;">units/day</span></div>
        </div>
        <div>
            <div style="font-size:11px; font-weight:600; color:#64748B; text-transform:uppercase;">Suggested Reorder</div>
            <div style="font-size:17px; font-weight:800; color:#0F172A; margin-top:2px;">{sel_reorder:,.0f} <span style="font-size:12px; font-weight:500; color:#64748B;">units</span></div>
        </div>
        <div>
            <div style="font-size:11px; font-weight:600; color:#64748B; text-transform:uppercase;">Recorded Sales</div>
            <div style="font-size:17px; font-weight:800; color:#0F172A; margin-top:2px;">{sel_actual:.1f} <span style="font-size:12px; font-weight:500; color:#64748B;">units</span></div>
        </div>
    </div>
    <div style="margin-top:14px;">
        <div style="font-size:12.5px; font-weight:700; color:#0F172A; text-transform:uppercase; letter-spacing:0.5px;">Why This Is Recommended:</div>
        <div style="font-size:13px; color:#334155; margin-top:4px; line-height:1.5; background:#F1F5F9; border-left:3px solid #64748B; padding:8px 12px; border-radius:0 6px 6px 0;">
            {sel_why}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

        # ── USER DECISION TABS (APPROVE / CHANGE QUANTITY / REJECT) ────
        st.markdown("#### User Decision")
        st.caption("Select your decision and save it to the database:")

        d_tab_app, d_tab_mod, d_tab_rej = st.tabs(["Approve", "Change Quantity", "Reject"])

        # ── TAB 1: APPROVE ───────────────────────────────────────────
        with d_tab_app:
            st.markdown(f"Accept the recommended reorder of **{sel_reorder:,.0f} units** for Store {sel_sid}.")
            app_note = st.text_input("Manager Note (optional):", value="", placeholder="e.g. Approved standard reorder", key=f"app_note_{sel_sid}_{sel_pid}")
            if st.button(f"Save Decision: Approve ({sel_reorder:,.0f} Units)", type="primary", key=f"btn_save_app_{sel_sid}_{sel_pid}"):
                res = save_replenishment_decision(
                    engine=engine,
                    store_id=sel_sid,
                    product_id=sel_pid,
                    recommended_qty=sel_reorder,
                    approved_qty=sel_reorder,
                    decision_status="APPROVED",
                    notes=app_note or f"Approved recommended order of {sel_reorder:,.0f} units."
                )
                if res["success"]:
                    st.cache_data.clear()
                    st.success(f"Decision saved: Approved {sel_reorder:,.0f} units for SKU {sel_pid} at Store {sel_sid}.")
                    st.rerun()
                else:
                    st.error(f"Unable to save decision: {res.get('message', 'Database error')}")

        # ── TAB 2: CHANGE QUANTITY ───────────────────────────────────
        with d_tab_mod:
            st.markdown("Adjust the replenishment quantity based on operational constraints or storage capacity:")
            mq_c1, mq_c2 = st.columns(2)
            with mq_c1:
                st.metric("Original Recommendation", f"{sel_reorder:,.0f} units")
            with mq_c2:
                default_mod_qty = float(existing_decision["approved_qty"]) if existing_decision and existing_decision["status"] == "MODIFIED" else float(sel_reorder)
                new_qty = st.number_input(
                    "New Quantity (units):",
                    min_value=0.0,
                    max_value=50000.0,
                    value=default_mod_qty,
                    step=5.0,
                    key=f"mod_qty_input_{sel_sid}_{sel_pid}"
                )
            mod_reason = st.text_input(
                "Reason for Quantity Change:",
                value=existing_decision["notes"] if existing_decision and existing_decision["status"] == "MODIFIED" else "",
                placeholder="e.g. Adjusted for storage shelf limits or upcoming weekend promotion",
                key=f"mod_reason_{sel_sid}_{sel_pid}"
            ).strip()

            if st.button("Save Decision: Update Quantity", type="primary", key=f"btn_save_mod_{sel_sid}_{sel_pid}"):
                if new_qty < 0:
                    st.error("Quantity cannot be negative.")
                elif not mod_reason:
                    st.warning("Please provide a reason for changing the quantity.")
                else:
                    res = save_replenishment_decision(
                        engine=engine,
                        store_id=sel_sid,
                        product_id=sel_pid,
                        recommended_qty=sel_reorder,
                        approved_qty=new_qty,
                        decision_status="MODIFIED",
                        notes=mod_reason
                    )
                    if res["success"]:
                        st.cache_data.clear()
                        st.success(f"Decision saved: Quantity updated to {new_qty:,.0f} units (Original: {sel_reorder:,.0f} units).")
                        st.rerun()
                    else:
                        st.error(f"Unable to save decision: {res.get('message', 'Database error')}")

        # ── TAB 3: REJECT ────────────────────────────────────────────
        with d_tab_rej:
            st.markdown("Reject this replenishment recommendation if additional stock is not required:")
            rej_reason_choice = st.selectbox(
                "Reason for Rejection:",
                ["Not needed", "Already stocked", "Manager decision", "Delivery issue", "Seasonal demand drop", "Other"],
                key=f"rej_choice_{sel_sid}_{sel_pid}"
            )
            rej_comment = st.text_input("Additional Details (optional):", value="", placeholder="e.g. Received internal transfer from nearby depot", key=f"rej_comment_{sel_sid}_{sel_pid}")

            if st.button("Save Decision: Reject Reorder", key=f"btn_save_rej_{sel_sid}_{sel_pid}"):
                full_reason = f"{rej_reason_choice}: {rej_comment}".strip(" :")
                res = save_replenishment_decision(
                    engine=engine,
                    store_id=sel_sid,
                    product_id=sel_pid,
                    recommended_qty=sel_reorder,
                    approved_qty=0.0,
                    decision_status="REJECTED",
                    notes=full_reason
                )
                if res["success"]:
                    st.cache_data.clear()
                    st.warning(f"Decision saved: Reorder rejected for SKU {sel_pid} at Store {sel_sid}.")
                    st.rerun()
                else:
                    st.error(f"Unable to save decision: {res.get('message', 'Database error')}")

        # ── CROSS-PAGE NAVIGATION ─────────────────────────────────────
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        nav_c1, nav_c2, _ = st.columns([1, 1, 2])
        with nav_c1:
            if st.button("View Product", key=f"btn_repl_to_prod_{sel_sid}_{sel_pid}", use_container_width=True):
                st.session_state["nav_page"] = "Products"
                st.session_state["analyzed_product_id"] = sel_pid
                st.session_state["analyzed_store"] = f"Store {sel_sid}"
                st.session_state["curr_selected_store"] = sel_sid
                st.rerun()
        with nav_c2:
            if st.button("View Store", key=f"btn_repl_to_store_{sel_sid}_{sel_pid}", use_container_width=True):
                st.session_state["nav_page"] = "Stores"
                st.session_state["analyzed_store_id"] = sel_sid
                st.rerun()

    # ── STEP 19 & 36: AUDITED DECISION HISTORY ─────────────────────────
    st.markdown("---")
    with st.expander("Audited Decision History", expanded=False):
        st.markdown("#### Decision History")
        st.caption("Complete database log of approved, modified, and rejected replenishment decisions:")

        try:
            recent_decisions = load_recent_replenishment_decisions(engine, limit=50)
        except Exception as e:
            db_error_message(f"Unable to load decision history: {e}")
            recent_decisions = pd.DataFrame()

        if recent_decisions.empty:
            st.info("No replenishment decisions recorded yet. Review recommendations above to record decisions.")
        else:
            disp_history = recent_decisions.copy()
            disp_history["Store"] = disp_history["store_id"].apply(lambda s: f"Store {int(s)}")
            disp_history["Product"] = disp_history.apply(
                lambda r: f"SKU {int(r['product_id'])} — {DEPT_MAP.get(int(r.get('management_group_id', 6)), 'Produce')}",
                axis=1
            )
            disp_history["Original Rec."] = disp_history["recommended_qty"].apply(lambda v: f"{float(v):,.0f} units")
            disp_history["Final Qty"] = disp_history["approved_qty"].apply(lambda v: f"{float(v):,.0f} units")
            disp_history["Decision"] = disp_history["decision_status"].map({
                "APPROVED": "🟢 Approved",
                "MODIFIED": "🟡 Modified",
                "REJECTED": "⚪ Rejected",
                "DEFERRED": "⚪ Deferred"
            }).fillna("🟢 Approved")
            disp_history["Timestamp"] = pd.to_datetime(disp_history["updated_at"]).dt.strftime("%Y-%m-%d %H:%M:%S")

            hist_cols = ["decision_id", "Timestamp", "Store", "Product", "Original Rec.", "Final Qty", "Decision", "decision_notes", "decided_by"]
            rename_hist = {
                "decision_id": "Record ID",
                "decision_notes": "Manager Notes / Reason",
                "decided_by": "Operator"
            }

            h_c1, h_c2 = st.columns([3, 1.2])
            with h_c1:
                st.caption(f"Showing **{len(disp_history):,} audited decision records**.")
            with h_c2:
                csv_bytes = disp_history[hist_cols].rename(columns=rename_hist).to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Decisions (CSV)",
                    data=csv_bytes,
                    file_name=f"smartstock_decisions_{datetime.now():%Y%m%d_%H%M}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="btn_export_decisions_csv"
                )

            st.dataframe(disp_history[hist_cols].rename(columns=rename_hist), use_container_width=True, hide_index=True)




# ══════════════════════════════════════════════════════════════
# PAGE: ACTION HISTORY
# ══════════════════════════════════════════════════════════════

elif page == "Action History":
    st.title("Action History")
    st.markdown("""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid #2563EB; border-radius:10px; padding:14px 18px; margin:8px 0 18px 0; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="font-size:16px; font-weight:800; color:#0F172A;">Action History</div>
    <div style="font-size:13.5px; color:#64748B; margin-top:3px;">
        View inventory decisions that have been made.
    </div>
</div>
""", unsafe_allow_html=True)

    # ── LOAD REAL SUMMARY FROM DATABASE ─────────────────────────
    try:
        summary = load_replenishment_decision_summary(engine)
    except Exception as e:
        st.error("Unable to load action history.")
        st.stop()

    # ── EMPTY STATE IF NO DECISIONS RECORDED (STEP 5, 20, 23) ────
    if summary["total_decisions"] == 0:
        st.info("No decisions have been recorded yet.")
        st.caption("When you approve, modify, or reject replenishment recommendations, your decisions will appear here.")
        if st.button("Go to Replenishment to Review Recommendations", key="btn_no_dec_goto_repl"):
            st.session_state["nav_page"] = "Replenishment"
            st.rerun()
        st.stop()

    # ── SUMMARY CARDS (STEP 5) ──────────────────────────────────
    s1, s2, s3, s4 = st.columns(4)
    custom_kpi_card(s1, "Approved", f"{summary['approved_count']:,}", subtext="Recommendations accepted", top_color="#10B981")
    custom_kpi_card(s2, "Modified", f"{summary['modified_count']:,}", subtext="Quantities adjusted by user", top_color="#F59E0B")
    custom_kpi_card(s3, "Rejected", f"{summary['rejected_count']:,}", subtext="Reorders declined with reason", top_color="#EF4444")
    custom_kpi_card(s4, "Total Decisions", f"{summary['total_decisions']:,}", subtext="Decisions recorded in database", top_color="#2563EB")

    # ── FILTERS & SORTING (STEPS 8-13) ───────────────────────────
    st.markdown("#### Filter Decisions")
    f_c1, f_c2, f_c3, f_c4, f_c5 = st.columns([1.2, 1.2, 1.2, 1.2, 1.2])

    with f_c1:
        date_filter_choice = st.selectbox(
            "Date Range:",
            ["All", "Today", "Last 7 Days", "Last 30 Days"],
            index=0,
            key="act_hist_date_filter"
        )
        days_map = {"All": None, "Today": 0, "Last 7 Days": 7, "Last 30 Days": 30}
        filter_days = days_map.get(date_filter_choice)

    with f_c2:
        decided_stores, decided_prods = load_decided_stores_and_products(engine)
        store_options = ["All Stores"] + [f"Store {s}" for s in decided_stores]
        store_filter_choice = st.selectbox(
            "Store Location:",
            store_options,
            index=0,
            key="act_hist_store_filter"
        )
        filter_store_id = None if store_filter_choice == "All Stores" else int(store_filter_choice.replace("Store ", ""))

    with f_c3:
        prod_options = ["All Products"] + [f"SKU {p}" for p in decided_prods]
        prod_filter_choice = st.selectbox(
            "Product (SKU):",
            prod_options,
            index=0,
            key="act_hist_prod_filter"
        )
        filter_prod_id = None if prod_filter_choice == "All Products" else int(prod_filter_choice.replace("SKU ", ""))

    with f_c4:
        decision_options = ["All", "Approved", "Modified", "Rejected"]
        decision_filter_choice = st.selectbox(
            "Decision Status:",
            decision_options,
            index=0,
            key="act_hist_decision_filter"
        )
        status_map = {"All": None, "Approved": "APPROVED", "Modified": "MODIFIED", "Rejected": "REJECTED"}
        filter_status = status_map.get(decision_filter_choice)

    with f_c5:
        sort_choice = st.selectbox(
            "Sorting:",
            ["Newest First", "Oldest First"],
            index=0,
            key="act_hist_sort_filter"
        )
        sort_asc = (sort_choice == "Oldest First")

    # Reset filters button
    rst_c1, rst_c2 = st.columns([4.2, 1])
    with rst_c2:
        if st.button("Reset Filters", key="btn_reset_act_hist_filters", use_container_width=True):
            st.session_state["act_hist_date_filter"] = "All"
            st.session_state["act_hist_store_filter"] = "All Stores"
            st.session_state["act_hist_prod_filter"] = "All Products"
            st.session_state["act_hist_decision_filter"] = "All"
            st.session_state["act_hist_sort_filter"] = "Newest First"
            st.rerun()

    # ── QUERY FILTERED DECISIONS ────────────────────────────────
    try:
        history_df = load_recent_replenishment_decisions(
            engine,
            limit=200,
            store_id=filter_store_id,
            product_id=filter_prod_id,
            decision_status=filter_status,
            days=filter_days,
            sort_asc=sort_asc
        )
    except Exception as e:
        st.error("Unable to load action history.")
        st.stop()

    # ── EMPTY STATE FOR FILTERS (STEP 23) ───────────────────────
    if history_df.empty:
        st.info("No decisions match your filters.")
        st.stop()

    # ── FORMAT DISPLAY TABLE (STEPS 6, 7, 26, 27, 28, 29, 30) ────
    st.markdown("#### Decision History")
    disp_df = history_df.copy()

    disp_df["Date"] = pd.to_datetime(disp_df["updated_at"]).dt.strftime("%d %b %Y, %H:%M")
    disp_df["Product"] = disp_df["product_id"].apply(lambda p: f"SKU {int(p)}")
    disp_df["Store"] = disp_df["store_id"].apply(lambda s: f"Store {int(s)}")
    disp_df["Recommended Quantity"] = disp_df["recommended_qty"].apply(lambda q: f"{float(q):,.0f} units")

    def _format_final_qty(row):
        status = str(row["decision_status"]).upper()
        if status == "REJECTED":
            return "0 units"
        return f"{float(row['approved_qty']):,.0f} units"

    disp_df["Final Quantity"] = disp_df.apply(_format_final_qty, axis=1)

    status_display_map = {
        "APPROVED": "🟢 Approved",
        "MODIFIED": "🟡 Modified",
        "REJECTED": "🔴 Rejected",
        "DEFERRED": "⚪ Deferred"
    }
    disp_df["Decision"] = disp_df["decision_status"].map(status_display_map).fillna("🟢 Approved")
    disp_df["Reason"] = disp_df["decision_notes"].fillna("—").apply(lambda n: str(n).strip() if str(n).strip() else "—")

    table_cols = ["Date", "Product", "Store", "Recommended Quantity", "Final Quantity", "Decision", "Reason"]
    st.dataframe(disp_df[table_cols], use_container_width=True, hide_index=True)
    st.caption(f"Showing **{len(disp_df):,} decisions** recorded in database.")

    # ── SELECTED DECISION DETAIL AREA (STEPS 14, 15, 16) ────────
    st.markdown("---")
    st.markdown("#### Selected Decision")

    detail_options = [
        f"SKU {int(r['product_id'])} at Store {int(r['store_id'])} — {r['Decision']} ({r['Date']})"
        for _, r in disp_df.iterrows()
    ]
    selected_idx = st.selectbox(
        "Select a decision to inspect details:",
        range(len(detail_options)),
        format_func=lambda i: detail_options[i],
        key="act_hist_sel_detail_idx"
    )

    if selected_idx is not None and 0 <= selected_idx < len(history_df):
        selected_record = history_df.iloc[selected_idx]
        sel_pid = int(selected_record["product_id"])
        sel_sid = int(selected_record["store_id"])
        sel_status = str(selected_record["decision_status"]).upper()
        sel_rec_qty = float(selected_record["recommended_qty"])
        sel_app_qty = float(selected_record["approved_qty"])
        sel_reason = str(selected_record["decision_notes"] or "—").strip() or "—"
        sel_badge = status_display_map.get(sel_status, "🟢 Approved")
        sel_date_str = pd.to_datetime(selected_record["updated_at"]).strftime("%d %b %Y, %H:%M")

        det_c1, det_c2, det_c3 = st.columns([1.5, 1.5, 1.5])
        with det_c1:
            st.markdown(f"**Product:** SKU {sel_pid}")
            st.markdown(f"**Store:** Store {sel_sid}")
            st.markdown(f"**Date:** {sel_date_str}")

        with det_c2:
            st.markdown(f"**Recommended Quantity:** {sel_rec_qty:,.0f} units")
            if sel_status == "REJECTED":
                st.markdown(f"**Final Quantity:** 0 units *(Declined)*")
            else:
                st.markdown(f"**Final Quantity:** {sel_app_qty:,.0f} units")
            st.markdown(f"**Decision:** {sel_badge}")

        with det_c3:
            st.markdown(f"**Reason:** {sel_reason}")
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            btn_c1, btn_c2 = st.columns(2)
            with btn_c1:
                if st.button("View Product", key=f"btn_hist_view_prod_{sel_sid}_{sel_pid}", use_container_width=True):
                    st.session_state["nav_page"] = "Products"
                    st.session_state["analyzed_product_id"] = sel_pid
                    st.session_state["analyzed_store_id"] = sel_sid
                    st.session_state["analyzed_store"] = f"Store {sel_sid}"
                    st.session_state["curr_selected_store"] = sel_sid
                    st.rerun()
            with btn_c2:
                if st.button("View Store", key=f"btn_hist_view_store_{sel_sid}_{sel_pid}", use_container_width=True):
                    st.session_state["nav_page"] = "Stores"
                    st.session_state["analyzed_store_id"] = sel_sid
                    st.rerun()




# ══════════════════════════════════════════════════════════════
# PAGE: CUSTOMER INSIGHTS
# ══════════════════════════════════════════════════════════════

elif page == "Customer Insights":
    st.title("Customer Insights")

    if not _instacart_ok:
        st.warning(
            "The customer basket dataset has not been loaded into the database yet. "
            "Please run the ingest pipeline first."
        )
        st.stop()

    st.markdown("""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid #0D9488; border-radius:10px; padding:14px 18px; margin:8px 0 16px 0;">
    <div style="font-size:14px; font-weight:600; color:#0F172A;">Customer Basket &amp; Purchase Intelligence (Instacart)</div>
    <div style="font-size:13px; color:#475569; margin-top:3px; line-height:1.5;">
        Complementary market-basket evidence mined from 3.4M grocery checkout transactions (49,688 products).
        <br>
        <span style="color:#64748B; font-size:12px;"><strong>Data Notice:</strong> Customer basket patterns originate from a separate grocery retail environment and are analyzed independently to surface cross-sell affinity and loyalty benchmarks — they are not directly joined with FreshRetailNet store-level sales.</span>
    </div>
</div>
""", unsafe_allow_html=True)


    try:
        ikpi = get_instacart_kpis()
    except Exception as e:
        db_error_message(str(e)); st.stop()

    c1, c2, c3, c4 = st.columns(4)
    custom_kpi_card(c1, "Catalog Products", f"{int(ikpi['total_products']):,}", subtext="Distinct grocery items", top_color="#0D9488")
    custom_kpi_card(c2, "Verified Shoppers", f"{int(ikpi['total_users']):,}", subtext="Household accounts", top_color="#6366F1")
    custom_kpi_card(c3, "Total Baskets", f"{int(ikpi['total_orders']):,}", subtext="Analyzed checkout orders", top_color="#2563EB")
    custom_kpi_card(c4, "Repeat Reorder Rate", f"{ikpi['overall_reorder_rate']:.1f}%", subtext="Basket loyalty benchmark", top_color="#D97706")

    st.divider()

    tab_rules, tab_vol, tab_reord, tab_dept = st.tabs([
        "Frequently Bought Together",
        "Top Purchased Products",
        "Repeat Purchase Loyalty",
        "Department & Aisle Breakdown"
    ])

    _lyt = dict(
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FAF8F3",
        font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#1A2B1F"),
        xaxis=dict(gridcolor="#E2E8E4", tickfont=dict(color="#4A5568")),
        yaxis=dict(gridcolor="#E2E8E4", tickfont=dict(color="#4A5568")),
        legend=dict(font=dict(color="#1A2B1F")),
    )
    _lyt_rev = dict(
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FAF8F3",
        font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#1A2B1F"),
        xaxis=dict(gridcolor="#E2E8E4", tickfont=dict(color="#4A5568")),
        yaxis=dict(autorange="reversed", gridcolor="#E2E8E4", tickfont=dict(color="#4A5568")),
        legend=dict(font=dict(color="#1A2B1F")),
    )

    with tab_rules:
        st.markdown("#### Frequently Bought Together")
        st.caption("Statistically significant product pairings frequently co-purchased in the same customer basket:")

        r_col1, r_col2 = st.columns([3, 1])
        with r_col1:
            min_lift = st.slider("Purchase Connection Strength (Lift):", min_value=1.0, max_value=5.0, value=1.5, step=0.1)
        with r_col2:
            st.caption("Higher lift means items are bought together more frequently than normal.")

        try:
            rules_df = get_basket_rules(min_lift)
            if rules_df.empty:
                st.info("No association rules found with the selected lift threshold. Try lowering the threshold.")
            else:
                fig_scatter = px.scatter(
                    rules_df,
                    x="support",
                    y="confidence",
                    size="lift",
                    color="lift",
                    color_continuous_scale=["#5BAF7A", "#E67E22", "#C0392B"],
                    hover_data=["antecedent_product", "consequent_product"],
                    title="Frequently Bought Together: Frequency vs. Likelihood",
                    labels={"support": "Support (%)", "confidence": "Confidence (%)", "lift": "Lift Multiplier"}
                )
                fig_scatter.update_layout(height=420, **_lyt)
                st.plotly_chart(fig_scatter, use_container_width=True)

                st.markdown("##### Frequently Bought Together List")
                rename_rules = {
                    "antecedent_product": "When Customer Buys",
                    "consequent_product": "They Also Buy",
                    "support": "Support (%)",
                    "confidence": "Confidence (%)",
                    "lift": "Lift Multiplier"
                }
                display_rules = rules_df[list(rename_rules.keys())].rename(columns=rename_rules)
                paginated_table(display_rules, page_size=20, key="rules_page")

        except Exception as e:
            st.warning(f"Basket rules not available: {e}")

        st.divider()

        # ──────────────────────────────────────────────────────────────
        # Interactive Product Cross-Sell Lookup
        # ──────────────────────────────────────────────────────────────
        st.markdown("#### Cross-Sell Opportunities")
        st.caption("Search or select a product to inspect complementary items frequently co-purchased in customer orders:")

        # Quick preset buttons
        qs1, qs2, qs3, qs4 = st.columns(4)
        if "assoc_search_key" not in st.session_state:
            st.session_state["assoc_search_key"] = "Banana"

        with qs1:
            if st.button("🍌 Banana", use_container_width=True):
                st.session_state["assoc_search_key"] = "Banana"
        with qs2:
            if st.button("🍓 Organic Strawberries", use_container_width=True):
                st.session_state["assoc_search_key"] = "Organic Strawberries"
        with qs3:
            if st.button("🥬 Organic Baby Spinach", use_container_width=True):
                st.session_state["assoc_search_key"] = "Organic Baby Spinach"
        with qs4:
            if st.button("🥑 Hass Avocado", use_container_width=True):
                st.session_state["assoc_search_key"] = "Organic Hass Avocado"

        product_search = st.text_input(
            "Or search product name:",
            value=st.session_state.get("assoc_search_key", "Banana"),
            placeholder="e.g. Lime, Raspberries, Strawberries..."
        )

        if product_search.strip():
            try:
                assoc = load_product_associations(engine, product_search.strip())
                if assoc.empty:
                    st.info(f"No cross-sell matches found for '{product_search}'. Try a common grocery item like 'Banana' or 'Organic Strawberries'.")
                else:
                    st.markdown(f"**Cross-Selling Companions for '{product_search}':**")
                    rename_assoc = {
                        "associated_product": "Frequently Co-Purchased Product",
                        "confidence": "Co-Purchase Confidence (%)",
                        "lift": "Lift Multiplier",
                        "support": "Support (%)"
                    }
                    st.dataframe(
                        assoc.rename(columns=rename_assoc),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Co-Purchase Confidence (%)": st.column_config.NumberColumn(format="%.3f"),
                            "Lift Multiplier": st.column_config.NumberColumn(format="%.2fx"),
                            "Support (%)": st.column_config.NumberColumn(format="%.3f"),
                        }
                    )
            except Exception as e:
                st.warning(f"Lookup failed: {e}")

    with tab_vol:
        st.markdown("#### Top Products by Total Purchase Volume")
        st.caption("Highest-volume items across analyzed customer transactions:")
        try:
            top_prod = get_top_purchased()
            fig_vol = px.bar(
                top_prod.head(20),
                x="purchase_count",
                y="product_name",
                orientation="h",
                color="department",
                title="Top 20 Products by Purchase Count",
                labels={"purchase_count": "Total Purchases", "product_name": "Product Name", "department": "Department"},
                color_discrete_sequence=["#2D8653", "#2980B9", "#E67E22", "#8E44AD", "#16A085"]
            )
            fig_vol.update_layout(height=520, **_lyt_rev)
            st.plotly_chart(fig_vol, use_container_width=True)

            rename_top = {
                "product_name": "Product Name",
                "department": "Department",
                "purchase_count": "Total Purchases",
                "reorder_rate_pct": "Reorder Rate (%)"
            }
            cols_top = [c for c in rename_top.keys() if c in top_prod.columns]
            paginated_table(top_prod[cols_top].rename(columns=rename_top), page_size=20, key="top_prod_page")
        except Exception as e:
            st.warning(f"Data not available: {e}")

    with tab_reord:
        st.markdown("#### Products with Highest Repeat Purchase Rates")
        st.caption("Items with minimum 1,000 purchases exhibiting the highest repeat purchase rates:")
        try:
            reorder_prod = get_top_reorder()
            fig_reord = px.bar(
                reorder_prod.head(20),
                x="reorder_rate_pct",
                y="product_name",
                orientation="h",
                color="reorder_signal",
                color_discrete_map={"HIGH": "#C0392B", "MEDIUM": "#E67E22", "LOW": "#2D8653"},
                title="Top 20 Habitual Reorder Products (% Repeat Purchases)",
                labels={"reorder_rate_pct": "Reorder Rate (%)", "product_name": "Product Name", "reorder_signal": "Loyalty Signal"}
            )
            fig_reord.update_layout(height=520, **_lyt_rev)
            st.plotly_chart(fig_reord, use_container_width=True)

            st.markdown("""
<div style="background:#F0FDFA; border:1px solid #99F6E4; border-left:4px solid #0D9488; border-radius:10px; padding:14px 18px; margin:14px 0 16px 0;">
    <div style="font-size:12.5px; font-weight:700; color:#0F766E; margin-bottom:4px;">
        Merchandising Insight: Habitual Staples
    </div>
    <div style="font-size:13px; color:#134E4A; line-height:1.5;">
        Staples with <strong>&gt;80% reorder rates</strong> (such as milk, bananas, and eggs) represent habitual household necessities. Out-of-stock events on these items trigger basket abandonment and customer dissatisfaction. Maintain reliable replenishment coverage on these lines.
    </div>
</div>
""", unsafe_allow_html=True)

            paginated_table(reorder_prod, page_size=20, key="reorder_page")
        except Exception as e:
            st.warning(f"Data not available: {e}")

    with tab_dept:
        st.markdown("#### Purchases by Department & Aisle")
        col1, col2 = st.columns(2)
        with col1:
            try:
                dept_df = get_departments()
                fig_d = px.bar(
                    dept_df,
                    x="total_purchases",
                    y="department",
                    orientation="h",
                    color="avg_reorder_rate",
                    color_continuous_scale="Teal",
                    title="Department Order Volume (All 21 Departments)",
                    labels={"total_purchases": "Total Purchases", "department": "Department", "avg_reorder_rate": "Avg Reorder %"}
                )
                fig_d.update_layout(height=500, **_lyt_rev)
                st.plotly_chart(fig_d, use_container_width=True)
            except Exception as e:
                st.warning(str(e))
        with col2:
            try:
                aisle_df = get_aisles()
                fig_a = px.bar(
                    aisle_df,
                    x="total_purchases",
                    y="aisle",
                    orientation="h",
                    color="avg_reorder_rate",
                    color_continuous_scale="Teal",
                    title="Top 20 Aisles by Order Volume",
                    labels={"total_purchases": "Total Purchases", "aisle": "Aisle Name", "avg_reorder_rate": "Avg Reorder %"}
                )
                fig_a.update_layout(height=500, **_lyt_rev)
                st.plotly_chart(fig_a, use_container_width=True)
            except Exception as e:
                st.warning(str(e))




# ══════════════════════════════════════════════════════════════
# PAGE: OPERATIONAL ALERTS
# ══════════════════════════════════════════════════════════════

elif page == "Alerts":
    st.title("Alerts")
    st.markdown("""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid #DC2626; border-radius:10px; padding:14px 18px; margin:8px 0 16px 0; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="font-size:16px; font-weight:800; color:#0F172A;">Alerts</div>
    <div style="font-size:13.5px; color:#64748B; margin-top:3px;">
        Review inventory exceptions, understand why they need attention, and take action.
    </div>
</div>
""", unsafe_allow_html=True)

    # ── 1. ALERT SUMMARY CARDS (STEP 14) ───────────────────────────
    try:
        alert_summary = load_alerts_summary(engine)
    except Exception:
        alert_summary = {"open_alerts": 0, "high_risk": 0, "medium_risk": 0, "resolved": 0, "reviewed": 0}

    c1, c2, c3, c4 = st.columns(4)
    custom_kpi_card(c1, "Open Alerts", f"{alert_summary['open_alerts']:,}", subtext="Needing manager review", top_color="#DC2626")
    custom_kpi_card(c2, "High Risk", f"{alert_summary['high_risk']:,}", subtext="Critical stockout exposure", top_color="#EF4444")
    custom_kpi_card(c3, "Medium Risk", f"{alert_summary['medium_risk']:,}", subtext="Elevated demand volatility", top_color="#F59E0B")
    custom_kpi_card(c4, "Resolved", f"{alert_summary['resolved']:,}", subtext="Closed after review / action", top_color="#10B981")

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # ── 2. PRE-FILLS FROM OTHER PAGES ─────────────────────────────
    pre_store = st.session_state.get("analyzed_store_id")
    if pre_store is None:
        raw_pre_store = st.session_state.get("analyzed_store")
        if raw_pre_store and str(raw_pre_store).startswith("Store "):
            try:
                pre_store = int(str(raw_pre_store).replace("Store ", "").strip())
            except ValueError:
                pre_store = None
    pre_sku = st.session_state.get("analyzed_product_id")

    # ── 3. FILTERS (STEP 13) ──────────────────────────────────────
    st.markdown("#### Filter Alerts")
    f1, f2, f3, f4, f5 = st.columns([1.2, 1.2, 1.2, 1.2, 1.4])

    with f1:
        status_choice = st.selectbox(
            "Status:",
            ["All", "Open", "Reviewed", "Resolved"],
            index=0,
            key="alerts_filter_status"
        )
        filter_status = None if status_choice == "All" else status_choice.upper()

    with f2:
        risk_choice = st.selectbox(
            "Risk Level:",
            ["All", "High Risk", "Medium Risk"],
            index=0,
            key="alerts_filter_risk"
        )
        filter_risk = None if risk_choice == "All" else ("HIGH" if "High" in risk_choice else "MEDIUM")

    with f3:
        priority_choice = st.selectbox(
            "Priority:",
            ["All Priorities", "🔴 Urgent", "🟡 Monitor", "🟢 Normal"],
            index=0,
            key="alerts_filter_priority"
        )
        filter_priority = None if priority_choice == "All Priorities" else (
            "HIGH" if "Urgent" in priority_choice else ("MEDIUM" if "Monitor" in priority_choice else "LOW")
        )

    with f4:
        try:
            stores_df = get_stores()
            avail_stores = sorted(stores_df["store_id"].unique().tolist())
            store_opts = ["All Stores"] + [f"Store {s}" for s in avail_stores]
        except Exception:
            store_opts = ["All Stores"] + [f"Store {s}" for s in range(50)]

        def_s_idx = 0
        if pre_store is not None:
            match_s = f"Store {pre_store}"
            if match_s in store_opts:
                def_s_idx = store_opts.index(match_s)

        store_choice = st.selectbox("Store Location:", store_opts, index=def_s_idx, key="alerts_filter_store")
        filter_store = None if store_choice == "All Stores" else int(store_choice.replace("Store ", ""))

    with f5:
        sku_search = st.text_input(
            "Filter by SKU (optional):",
            value=str(pre_sku) if pre_sku is not None else "",
            placeholder="e.g. 267",
            key="alerts_filter_sku"
        ).strip()
        filter_sku = None
        if sku_search:
            try:
                filter_sku = int(sku_search.replace("SKU", "").strip())
            except ValueError:
                filter_sku = -1

    # Reset filters button
    rst_c1, rst_c2 = st.columns([4.2, 1])
    with rst_c2:
        if st.button("Reset Filters", key="btn_reset_alerts_filters", use_container_width=True):
            st.session_state["alerts_filter_status"] = "All"
            st.session_state["alerts_filter_risk"] = "All"
            st.session_state["alerts_filter_priority"] = "All Priorities"
            st.session_state["alerts_filter_store"] = "All Stores"
            st.session_state["alerts_filter_sku"] = ""
            st.session_state.pop("analyzed_store_id", None)
            st.session_state.pop("analyzed_product_id", None)
            st.rerun()

    # ── 4. LOAD FILTERED ALERTS (STEP 5, 11, 12) ──────────────────
    try:
        alerts_df = load_actionable_alerts(
            engine,
            status=filter_status,
            risk_level=filter_risk,
            priority=filter_priority,
            store_id=filter_store,
            product_id=filter_sku,
            limit=200
        )
    except Exception as e:
        st.error("Unable to load alerts.")
        st.stop()

    if alerts_df.empty:
        st.info("No alerts match your active filters.")
        st.stop()

    # ── 5. FORMAT ALERT TABLE (STEP 5, 6, 7) ───────────────────────
    st.markdown("#### Alert Table")
    disp_alerts = alerts_df.copy()

    disp_alerts["Date"] = pd.to_datetime(disp_alerts["dt"]).dt.strftime("%Y-%m-%d")
    disp_alerts["Product"] = disp_alerts["product_id"].apply(lambda p: f"SKU {int(p)}")
    disp_alerts["Store"] = disp_alerts["store_id"].apply(lambda s: f"Store {int(s)}")

    def _format_alert_name(r):
        risk = str(r["stockout_risk"]).upper()
        if risk == "HIGH":
            return "🔴 High Stockout Risk"
        elif risk == "MEDIUM":
            return "🟡 Medium Stockout Risk"
        return "🟢 Low Stockout Risk"

    disp_alerts["Alert"] = disp_alerts.apply(_format_alert_name, axis=1)
    disp_alerts["Expected Demand"] = disp_alerts["predicted_sales"].apply(lambda d: f"{float(d):.1f} units")

    disp_alerts["Risk"] = disp_alerts["stockout_risk"].map({
        "HIGH": "🔴 High",
        "MEDIUM": "🟡 Medium",
        "LOW": "🟢 Low"
    }).fillna("🔴 High")

    disp_alerts["Priority"] = disp_alerts["replenishment_priority"].map({
        "HIGH": "🔴 Urgent",
        "MEDIUM": "🟡 Monitor",
        "LOW": "🟢 Normal"
    }).fillna("🔴 Urgent")

    disp_alerts["Suggested Reorder"] = disp_alerts["recommended_reorder_qty"].apply(lambda q: f"{float(q):,.0f} units")

    disp_alerts["Status"] = disp_alerts["action_status"].map({
        "OPEN": "⚪ Open",
        "REVIEWED": "🟡 Reviewed",
        "ACKNOWLEDGED": "🟡 Reviewed",
        "RESOLVED": "🟢 Resolved"
    }).fillna("⚪ Open")

    table_cols = [
        "Date", "Product", "Store", "Alert", "Expected Demand",
        "Risk", "Priority", "Suggested Reorder", "Status"
    ]
    st.dataframe(disp_alerts[table_cols], use_container_width=True, hide_index=True)
    st.caption(f"Showing **{len(disp_alerts):,} alerts** matching active filters.")

    # ── 6. ALERT DETAILS & ACTIONS (STEPS 8, 9, 15) ────────────────
    st.markdown("---")
    st.markdown("#### Selected Alert")

    alert_options = [
        f"SKU {int(r['product_id'])} at Store {int(r['store_id'])} — {r['Alert']} [{r['Status']}] ({r['Date']})"
        for _, r in disp_alerts.iterrows()
    ]
    selected_idx = st.selectbox(
        "Select an alert to inspect details and take action:",
        range(len(alert_options)),
        format_func=lambda i: alert_options[i],
        key="sel_alert_inspector_idx"
    )

    if selected_idx is not None and 0 <= selected_idx < len(alerts_df):
        sel_row = alerts_df.iloc[selected_idx]
        sel_pid = int(sel_row["product_id"])
        sel_sid = int(sel_row["store_id"])
        sel_risk = str(sel_row["stockout_risk"]).upper()
        sel_pri = str(sel_row["replenishment_priority"]).upper()
        sel_pred = float(sel_row["predicted_sales"])
        sel_reorder = float(sel_row["recommended_reorder_qty"])
        sel_status = str(sel_row["action_status"]).upper()
        sel_dt_str = pd.to_datetime(sel_row["dt"]).strftime("%Y-%m-%d")

        raw_why = str(sel_row.get("risk_explanation") or "").strip()
        if not raw_why:
            raw_why = f"Recent demand is {sel_pred:.1f} units/day with elevated stockout probability."

        st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:18px 20px; margin:10px 0 16px 0; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; border-bottom:1px solid #F1F5F9; padding-bottom:10px;">
        <div style="font-size:16px; font-weight:800; color:#0F172A;">
            SKU {sel_pid} &bull; Store {sel_sid}
        </div>
        <div>
            <span style="font-size:12px; font-weight:700; background:{'#FEE2E2' if sel_risk=='HIGH' else '#FEF3C7'}; color:{'#DC2626' if sel_risk=='HIGH' else '#D97706'}; padding:4px 10px; border-radius:6px; margin-right:6px;">
                {'High Stockout Risk' if sel_risk=='HIGH' else 'Medium Stockout Risk'}
            </span>
            <span style="font-size:12px; font-weight:700; background:{'#DCFCE7' if sel_status=='RESOLVED' else ('#FEF3C7' if sel_status in ['REVIEWED','ACKNOWLEDGED'] else '#F1F5F9')}; color:{'#15803D' if sel_status=='RESOLVED' else ('#B45309' if sel_status in ['REVIEWED','ACKNOWLEDGED'] else '#475569')}; padding:4px 10px; border-radius:6px;">
                Status: {'Resolved' if sel_status=='RESOLVED' else ('Reviewed' if sel_status in ['REVIEWED','ACKNOWLEDGED'] else 'Open')}
            </span>
        </div>
    </div>
    <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:12px; margin-bottom:14px;">
        <div>
            <div style="font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase;">Date</div>
            <div style="font-size:14px; font-weight:700; color:#0F172A; margin-top:2px;">{sel_dt_str}</div>
        </div>
        <div>
            <div style="font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase;">Expected Demand</div>
            <div style="font-size:14px; font-weight:700; color:#0F172A; margin-top:2px;">{sel_pred:.1f} units/day</div>
        </div>
        <div>
            <div style="font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase;">Priority</div>
            <div style="font-size:14px; font-weight:700; color:{'#DC2626' if sel_pri=='HIGH' else '#D97706'}; margin-top:2px;">
                {'Urgent' if sel_pri=='HIGH' else ('Monitor' if sel_pri=='MEDIUM' else 'Normal')}
            </div>
        </div>
        <div>
            <div style="font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase;">Suggested Reorder</div>
            <div style="font-size:14px; font-weight:800; color:#2563EB; margin-top:2px;">{sel_reorder:,.0f} units</div>
        </div>
    </div>
    <div style="margin-bottom:10px;">
        <div style="font-size:12px; font-weight:700; color:#0F172A; margin-bottom:3px;">Why this needs attention:</div>
        <div style="font-size:13px; color:#475569; line-height:1.5;">{raw_why}</div>
    </div>
    <div>
        <div style="font-size:12px; font-weight:700; color:#0F172A; margin-bottom:3px;">Recommended Action:</div>
        <div style="font-size:13px; color:#475569; line-height:1.5;">Review the replenishment recommendation to order stock buffer before the next inventory cycle.</div>
    </div>
</div>
""", unsafe_allow_html=True)

        # ── ACTION BUTTONS (STEPS 9 & 15) ──────────────────────────
        st.markdown("##### Actions")
        b_c1, b_c2, b_c3, b_c4, b_c5 = st.columns(5)

        with b_c1:
            if st.button("View Product", key=f"btn_alert_prod_{sel_sid}_{sel_pid}", use_container_width=True):
                st.session_state["nav_page"] = "Products"
                st.session_state["analyzed_product_id"] = sel_pid
                st.session_state["analyzed_store_id"] = sel_sid
                st.session_state["analyzed_store"] = f"Store {sel_sid}"
                st.session_state["curr_selected_store"] = sel_sid
                st.rerun()

        with b_c2:
            if st.button("View Store", key=f"btn_alert_store_{sel_sid}_{sel_pid}", use_container_width=True):
                st.session_state["nav_page"] = "Stores"
                st.session_state["analyzed_store_id"] = sel_sid
                st.rerun()

        with b_c3:
            if st.button("View Recommendation", key=f"btn_alert_repl_{sel_sid}_{sel_pid}", type="primary", use_container_width=True):
                st.session_state["nav_page"] = "Replenishment"
                st.session_state["repl_store_filter"] = sel_sid
                st.session_state["analyzed_store_id"] = sel_sid
                st.session_state["analyzed_product_id"] = sel_pid
                st.rerun()

        with b_c4:
            if sel_status in ["REVIEWED", "ACKNOWLEDGED"]:
                st.button("Marked Reviewed", disabled=True, key=f"btn_alert_rev_dis_{sel_sid}_{sel_pid}", use_container_width=True)
            else:
                if st.button("Mark Reviewed", key=f"btn_alert_rev_{sel_sid}_{sel_pid}", use_container_width=True):
                    res = save_alert_action(engine, sel_sid, sel_pid, sel_risk, action_status="REVIEWED", notes="Reviewed by manager")
                    if res.get("success"):
                        st.cache_data.clear()
                        st.success(f"Alert marked as Reviewed for SKU {sel_pid} at Store {sel_sid}.")
                        st.rerun()
                    else:
                        st.error(res.get("message", "Database error"))

        with b_c5:
            if sel_status == "RESOLVED":
                if st.button("Reopen Alert", key=f"btn_alert_reopen_{sel_sid}_{sel_pid}", use_container_width=True):
                    res = save_alert_action(engine, sel_sid, sel_pid, sel_risk, action_status="OPEN", notes="Reopened by manager")
                    if res.get("success"):
                        st.cache_data.clear()
                        st.info(f"Alert reopened for SKU {sel_pid} at Store {sel_sid}.")
                        st.rerun()
                    else:
                        st.error(res.get("message", "Database error"))
            else:
                if st.button("Mark Resolved", key=f"btn_alert_res_{sel_sid}_{sel_pid}", use_container_width=True):
                    res = save_alert_action(engine, sel_sid, sel_pid, sel_risk, action_status="RESOLVED", notes="Resolved by manager")
                    if res.get("success"):
                        st.cache_data.clear()
                        st.success(f"Alert marked as Resolved for SKU {sel_pid} at Store {sel_sid}.")
                        st.rerun()
                    else:
                        st.error(res.get("message", "Database error"))




# ══════════════════════════════════════════════════════════════
# PAGE: ADD INVENTORY DATA (OPERATIONAL INVENTORY UPDATES)
# ══════════════════════════════════════════════════════════════

elif page == "Add Inventory Data":
    st.title("Add Inventory Data")
    st.caption("Enter new daily inventory data.")

    # Clean Context Banner & Model Limitation Notice
    st.markdown("""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid #2563EB; border-radius:10px; padding:14px 18px; margin:8px 0 16px 0;">
    <div style="font-size:14px; font-weight:600; color:#0F172A;">Store Inventory Entry</div>
    <div style="font-size:13px; color:#64748B; margin-top:2px;">
        Record daily sales observations, shelf availability, and operational notes directly into the database.
    </div>
    <div style="font-size:12px; color:#475569; margin-top:8px; border-top:1px solid #F1F5F9; padding-top:6px;">
        <strong>Note:</strong> New data is stored in the database and can be used for future analysis and model updates.
    </div>
</div>
""", unsafe_allow_html=True)

    # Operational Summary Metrics
    try:
        op_summary = load_inventory_update_summary(engine)
    except Exception:
        op_summary = {
            "total_records": 0, "stores_covered": 0, "products_covered": 0,
            "total_sales_recorded": 0.0, "out_of_stock_count": 0,
            "low_stock_count": 0, "in_stock_count": 0
        }

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    custom_kpi_card(
        kpi_col1,
        label="Operational Records",
        value=f"{op_summary['total_records']:,}",
        subtext="Total records logged",
        top_color="#2563EB"
    )
    custom_kpi_card(
        kpi_col2,
        label="Stores Reporting",
        value=f"{op_summary['stores_covered']:,}",
        subtext="Active locations updated",
        top_color="#D97706"
    )
    custom_kpi_card(
        kpi_col3,
        label="Stockouts Logged",
        value=f"{op_summary['out_of_stock_count']:,}",
        subtext="Out-of-stock events",
        top_color="#DC2626"
    )
    custom_kpi_card(
        kpi_col4,
        label="Sales Volume Recorded",
        value=f"{op_summary['total_sales_recorded']:,.1f} units",
        subtext="Logged sales volume",
        top_color="#059669"
    )

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    # Load Reference Catalogs
    try:
        stores_df = get_stores_catalog()
        products_df = get_products_catalog()
    except Exception as e:
        st.error(f"Unable to load reference catalogs: {e}")
        st.stop()

    store_options = [
        f"Store {int(row['store_id']):03d} (City {int(row['city_id'])})"
        for _, row in stores_df.iterrows()
    ]
    store_id_map = {
        opt: int(row['store_id'])
        for opt, (_, row) in zip(store_options, stores_df.iterrows())
    }

    product_options = [
        f"SKU {int(row['product_id']):03d} — {DEPT_MAP.get(int(row['management_group_id']), 'Produce Department')}"
        for _, row in products_df.iterrows()
    ]
    product_id_map = {
        opt: int(row['product_id'])
        for opt, (_, row) in zip(product_options, products_df.iterrows())
    }

    # Input Form Container
    with st.container():
        st.markdown("""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:16px 20px; margin-bottom:16px;">
    <div style="font-size:15px; font-weight:700; color:#0F172A;">
        Enter Daily Inventory Record
    </div>
</div>
""", unsafe_allow_html=True)

        with st.form(key="add_inventory_form", clear_on_submit=False):
            # Section 1: Store & SKU Selection
            st.markdown("""
            <div style="font-size:13px; font-weight:700; color:#1E293B; margin-bottom:8px;">
                1. Store &amp; Product Selection
            </div>
            """, unsafe_allow_html=True)

            s1_col1, s1_col2, s1_col3 = st.columns([1, 1.5, 2])
            with s1_col1:
                input_date = st.date_input(
                    "Date *",
                    value=datetime.today().date(),
                    max_value=datetime.today().date(),
                    help="Observation date for this daily record"
                )
            with s1_col2:
                selected_store_label = st.selectbox(
                    "Store *",
                    options=store_options,
                    index=0,
                    help="Select store location from verified catalog"
                )
            with s1_col3:
                selected_product_label = st.selectbox(
                    "Product / SKU *",
                    options=product_options,
                    index=0,
                    help="Select product SKU from verified catalog"
                )

            st.markdown("<hr style='margin: 14px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

            # Section 2: Sales & Stock Observations
            st.markdown("""
            <div style="font-size:13px; font-weight:700; color:#1E293B; margin-bottom:8px;">
                2. Sales &amp; Stock Observations
            </div>
            """, unsafe_allow_html=True)

            s2_col1, s2_col2, s2_col3 = st.columns(3)
            with s2_col1:
                sales_qty = st.number_input(
                    "Daily Sales *",
                    min_value=0.0,
                    max_value=50000.0,
                    value=0.0,
                    step=1.0,
                    format="%.2f",
                    help="Registered sales quantity for the date (units sold)"
                )
            with s2_col2:
                stock_status = st.selectbox(
                    "Stock Status *",
                    options=["In Stock", "Low Stock", "Out of Stock"],
                    index=0,
                    help="Physical shelf availability status"
                )
            with s2_col3:
                discount_pct = st.number_input(
                    "Discount (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=0.5,
                    format="%.1f",
                    help="Markdown percentage on shelf (0% = standard price)"
                )

            st.markdown("<hr style='margin: 14px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

            # Section 3: Operational Context
            st.markdown("""
            <div style="font-size:13px; font-weight:700; color:#1E293B; margin-bottom:8px;">
                3. Operational Context
            </div>
            """, unsafe_allow_html=True)

            s3_col1, s3_col2, s3_col3 = st.columns([1, 1, 2])
            with s3_col1:
                is_holiday = st.radio(
                    "Holiday",
                    options=["No", "Yes"],
                    index=0,
                    horizontal=True,
                    help="Public holiday affecting store traffic"
                )
            with s3_col2:
                is_activity = st.radio(
                    "Activity",
                    options=["No", "Yes"],
                    index=0,
                    horizontal=True,
                    help="Promotional event or marketing activity"
                )
            with s3_col3:
                notes = st.text_input(
                    "Manager Notes (Optional)",
                    placeholder="e.g., Morning shipment delayed; steady customer demand.",
                    max_chars=250,
                    help="Operational observations or incident notes"
                )

            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

            # Duplicate Overwrite Option
            update_existing = st.checkbox(
                "Update existing record if already present for this date, store, and product",
                value=False,
                help="Check this box to update the record instead of blocking duplicates."
            )

            st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)

            btn_col1, btn_col2 = st.columns([1.3, 3])
            with btn_col1:
                submitted = st.form_submit_button(
                    "Save Inventory Record",
                    type="primary",
                    use_container_width=True
                )
            with btn_col2:
                st.markdown("""
                <div style="font-size:12px; color:#64748B; padding-top:8px;">
                    Records are saved directly into the PostgreSQL database.
                </div>
                """, unsafe_allow_html=True)

        if submitted:
            store_id = store_id_map.get(selected_store_label)
            product_id = product_id_map.get(selected_product_label)
            holiday_int = 1 if is_holiday == "Yes" else 0
            activity_int = 1 if is_activity == "Yes" else 0

            validation_errors = []
            if input_date is None:
                validation_errors.append("Reporting date is required.")
            elif input_date > datetime.today().date():
                validation_errors.append("Reporting date cannot be in the future.")

            if store_id is None:
                validation_errors.append("Please select a store.")
            if product_id is None:
                validation_errors.append("Please select a product.")

            if sales_qty < 0:
                validation_errors.append("Daily sales cannot be negative.")
            if discount_pct < 0 or discount_pct > 100:
                validation_errors.append("Please enter a valid discount.")

            if validation_errors:
                for err in validation_errors:
                    st.error(f"{err}")
            else:
                # Step 6: Duplicate Protection
                try:
                    exists = check_inventory_update_exists(engine, input_date, store_id, product_id)
                except Exception:
                    exists = False

                if exists and not update_existing:
                    st.warning("This record already exists.")
                else:
                    with st.spinner("Saving inventory update..."):
                        result = save_inventory_update(
                            engine=engine,
                            dt=input_date,
                            store_id=store_id,
                            product_id=product_id,
                            sale_amount=sales_qty,
                            stock_status=stock_status,
                            discount=discount_pct,
                            holiday_flag=holiday_int,
                            activity_flag=activity_int,
                            notes=notes
                        )

                    if result["success"]:
                        st.cache_data.clear()
                        st.success("Inventory record saved successfully.")
                        badge_title = "Record Saved" if result.get("is_new") else "Record Updated"
                        st.markdown(f"""
<div style="background:#F0FDF4; border:1px solid #BBF7D0; border-left:4px solid #16A34A; border-radius:10px; padding:14px 18px; margin:12px 0;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span style="background:#DCFCE7; color:#15803D; font-size:11px; font-weight:700; padding:2px 8px; border-radius:6px;">
            {badge_title} &bull; ID #{result['update_id']}
        </span>
    </div>
    <div style="font-size:14px; font-weight:600; color:#14532D; margin-bottom:6px;">
        {result['message']}
    </div>
    <div style="font-size:13px; color:#166534; display:grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap:8px; margin-top:8px;">
        <div><strong>Date:</strong> {input_date}</div>
        <div><strong>Store:</strong> {selected_store_label.split('(')[0].strip()}</div>
        <div><strong>Product:</strong> SKU {product_id}</div>
        <div><strong>Daily Sales:</strong> {sales_qty:,.2f} units</div>
        <div><strong>Stock Status:</strong> {stock_status}</div>
        <div><strong>Discount:</strong> {discount_pct:.1f}%</div>
    </div>
</div>
""", unsafe_allow_html=True)
                        st.toast("Inventory record saved successfully!", icon="💾")
                    else:
                        st.error(f"{result['message']}")

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Section 4: Recent Inventory Updates
    st.markdown("""
    <div style="margin-bottom:12px;">
        <h3 style="margin:0; font-size:17px; color:#0F172A;">Recent Inventory Updates</h3>
        <p style="margin:2px 0 0 0; font-size:13px; color:#64748B;">Latest operational records logged across store locations.</p>
    </div>
    """, unsafe_allow_html=True)

    try:
        recent_updates = load_recent_inventory_updates(engine, limit=10)
    except Exception as e:
        st.error("Could not load recent updates. Please check the database connection.")
        recent_updates = pd.DataFrame()

    if recent_updates.empty:
        st.info("No operational records logged yet. Enter your first daily record using the form above.")
    else:
        display_recent = recent_updates.copy()
        display_recent["Store"] = display_recent.apply(
            lambda r: f"Store {int(r['store_id']):03d} (City {int(r['city_id']) if pd.notna(r['city_id']) else '—'})", axis=1
        )
        display_recent["Product / SKU"] = display_recent.apply(
            lambda r: f"SKU {int(r['product_id']):03d} — {DEPT_MAP.get(int(r['management_group_id']) if pd.notna(r['management_group_id']) else 0, 'Produce')}", axis=1
        )
        display_recent["Daily Sales"] = display_recent["sale_amount"].apply(lambda v: f"{float(v):,.2f}")
        display_recent["Discount"] = display_recent["discount"].apply(lambda v: f"{float(v):.1f}%")
        display_recent["Holiday"] = display_recent["holiday_flag"].apply(lambda v: "Yes" if v == 1 else "No")
        display_recent["Activity"] = display_recent["activity_flag"].apply(lambda v: "Yes" if v == 1 else "No")

        cols_to_show = [
            "update_id", "dt", "Store", "Product / SKU",
            "Daily Sales", "stock_status", "Discount", "Holiday", "Activity", "notes"
        ]
        rename_cols = {
            "update_id": "Record ID",
            "dt": "Date",
            "stock_status": "Stock Status",
            "notes": "Manager Notes"
        }
        display_recent = display_recent[cols_to_show].rename(columns=rename_cols)

        st.dataframe(
            display_recent,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Record ID": st.column_config.NumberColumn(format="#%d"),
                "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "Stock Status": st.column_config.TextColumn("Stock Status"),
                "Manager Notes": st.column_config.TextColumn("Manager Notes", width="medium"),
            }
        )




# ══════════════════════════════════════════════════════════════
# PAGE: AI INVENTORY ASSISTANT
# ══════════════════════════════════════════════════════════════

elif page == "AI Inventory Assistant":
    st.title("AI Inventory Assistant")
    st.caption("Ask questions about products, demand, risk and replenishment.")

    # Clean Context Banner
    st.markdown("""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid #2563EB; border-radius:10px; padding:14px 18px; margin:8px 0 16px 0;">
    <div style="font-size:14px; font-weight:600; color:#0F172A;">Inventory Explanation Assistant</div>
    <div style="font-size:13px; color:#64748B; margin-top:2px;">
        Get clear, data-backed explanations for inventory risks, demand forecasts, and replenishment recommendations.
    </div>
</div>
""", unsafe_allow_html=True)

    from ai_assistant import answer_question

    # ──────────────────────────────────────────────────────────────
    # 1. SUGGESTED QUESTIONS (STEPS 6 & 21)
    # ──────────────────────────────────────────────────────────────
    st.markdown("##### Suggested Questions")

    if "active_ai_query" not in st.session_state:
        st.session_state["active_ai_query"] = "Which products need attention?"

    q_col1, q_col2, q_col3, q_col4 = st.columns(4)
    with q_col1:
        if st.button("Why is this product at risk?", use_container_width=True):
            st.session_state["active_ai_query"] = "Why is SKU 267 at Store 631 at high risk?"
        if st.button("How much should I reorder?", use_container_width=True):
            st.session_state["active_ai_query"] = "How much should I reorder?"
    with q_col2:
        if st.button("Which products need attention?", use_container_width=True):
            st.session_state["active_ai_query"] = "Which products need attention?"
        if st.button("Why was this reorder recommended?", use_container_width=True):
            st.session_state["active_ai_query"] = "Why was this reorder recommended?"
    with q_col3:
        if st.button("Which stores need attention?", use_container_width=True):
            st.session_state["active_ai_query"] = "Which stores need attention?"
        if st.button("Show high-risk products", use_container_width=True):
            st.session_state["active_ai_query"] = "Show high-risk products"
    with q_col4:
        if st.button("Show urgent recommendations", use_container_width=True):
            st.session_state["active_ai_query"] = "Show urgent recommendations"

    st.markdown("<hr style='margin:16px 0; border:none; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────
    # 2. ASK ABOUT YOUR INVENTORY (STEP 21)
    # ──────────────────────────────────────────────────────────────
    st.markdown("##### Ask about your inventory")

    # Optional Context Selectors
    try:
        stores_df = get_stores_catalog()
        products_df = get_products_catalog()
        store_opts = ["All Stores"] + [f"Store {int(r['store_id']):03d}" for _, r in stores_df.iterrows()]
        prod_opts = ["All Products"] + [f"SKU {int(r['product_id']):03d}" for _, r in products_df.iterrows()]
    except Exception:
        store_opts = ["All Stores"]
        prod_opts = ["All Products"]

    ctx_c1, ctx_c2 = st.columns([1, 1])
    with ctx_c1:
        sel_store_str = st.selectbox("Focus Store (Optional)", store_opts, index=0, help="Filter question context to a store location")
    with ctx_c2:
        sel_prod_str = st.selectbox("Focus Product (Optional)", prod_opts, index=0, help="Filter question context to a specific SKU")

    ctx_store_id = int(sel_store_str.split()[1]) if sel_store_str != "All Stores" else None
    ctx_prod_id = int(sel_prod_str.split()[1]) if sel_prod_str != "All Products" else None

    c_input, c_btn = st.columns([4.2, 1])
    with c_input:
        user_input_query = st.text_input(
            "Enter your inventory question:",
            placeholder="e.g. Why is SKU 267 at Store 631 at high risk? or Which stores need attention?",
            key="user_ai_query_input",
            label_visibility="collapsed"
        )
    with c_btn:
        ask_clicked = st.button("Ask", type="primary", use_container_width=True)
        if ask_clicked and user_input_query.strip():
            st.session_state["active_ai_query"] = user_input_query.strip()

    st.markdown("<hr style='margin:16px 0; border:none; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────
    # 3. ANSWER DISPLAY & ACTIONS (STEPS 20 & 21)
    # ──────────────────────────────────────────────────────────────
    active_query = st.session_state.get("active_ai_query", "Which products need attention?")
    st.markdown(f"**Question:** *\"{active_query}\"*")

    with st.spinner("Retrieving inventory records..."):
        result = answer_question(
            engine=engine,
            question=active_query,
            store_id=ctx_store_id,
            product_id=ctx_prod_id
        )

    # Short grounded response card
    answer_text = result.get("answer", "").replace("\n", "<br>")
    st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid #2563EB; padding:18px 22px; border-radius:10px; margin:12px 0 16px 0; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
    <div style="font-size:12px; font-weight:700; color:#2563EB; text-transform:uppercase; letter-spacing:0.6px; margin-bottom:8px;">
        Answer
    </div>
    <div style="font-size:14.5px; color:#0F172A; line-height:1.65;">
        {answer_text}
    </div>
</div>
""", unsafe_allow_html=True)

    if result.get("limitation"):
        st.markdown(f"""
<div style="background:#F8FAFC; border:1px solid #E2E8F0; border-left:3px solid #64748B; padding:10px 14px; border-radius:6px; margin-bottom:14px; font-size:12.5px; color:#475569;">
    <strong>Data Context:</strong> {result['limitation']}
</div>
""", unsafe_allow_html=True)

    # Relevant Data Table
    if result.get("data") is not None and not result["data"].empty:
        df_evidence = result["data"]
        st.markdown(f"**Relevant Data ({len(df_evidence)} records)**")
        st.dataframe(df_evidence, use_container_width=True, hide_index=True)

    # ──────────────────────────────────────────────────────────────
    # 4. ACTION BUTTONS / NAVIGATION (STEP 20)
    # ──────────────────────────────────────────────────────────────
    target_pid = result.get("product_id") or ctx_prod_id
    target_sid = result.get("store_id") or ctx_store_id

    st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
    st.markdown("##### Actions")
    act_col1, act_col2, act_col3, act_col4 = st.columns(4)

    with act_col1:
        if st.button("View Product", key="btn_ai_nav_prod", use_container_width=True):
            st.session_state["nav_page"] = "Products"
            if target_pid is not None:
                st.session_state["analyzed_product_id"] = int(target_pid)
            if target_sid is not None:
                st.session_state["analyzed_store_id"] = int(target_sid)
                st.session_state["curr_selected_store"] = int(target_sid)
            st.rerun()

    with act_col2:
        if st.button("View Store", key="btn_ai_nav_store", use_container_width=True):
            st.session_state["nav_page"] = "Stores"
            if target_sid is not None:
                st.session_state["analyzed_store_id"] = int(target_sid)
                st.session_state["curr_selected_store"] = int(target_sid)
            st.rerun()

    with act_col3:
        if st.button("View Recommendation", key="btn_ai_nav_repl", use_container_width=True):
            st.session_state["nav_page"] = "Replenishment"
            if target_sid is not None:
                st.session_state["repl_selected_store"] = int(target_sid)
            if target_pid is not None:
                st.session_state["repl_search_sku"] = int(target_pid)
            st.rerun()

    with act_col4:
        if st.button("View Risk", key="btn_ai_nav_risk", use_container_width=True):
            st.session_state["nav_page"] = "Inventory Risk"
            st.rerun()



# ══════════════════════════════════════════════════════════════
# GLOBAL FOOTERS
# ══════════════════════════════════════════════════════════════



st.markdown("""
<div style="text-align:center; padding:24px 0 16px 0; color:#64748B; font-size:12.5px; border-top:1px solid #E2E8F0; margin-top:40px;">
    SmartStock AI &bull; Inventory Intelligence
</div>
""", unsafe_allow_html=True)