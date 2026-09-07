# ============================================================
# SMARTSTOCK AI
# streamlit/components.py — Reusable UI Components
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# COLOUR PALETTE
# ============================================================

RISK_COLORS = {
    "HIGH":   "#e74c3c",
    "MEDIUM": "#f39c12",
    "LOW":    "#2ecc71"
}

PRIORITY_COLORS = {
    "HIGH":   "#c0392b",
    "MEDIUM": "#e67e22",
    "LOW":    "#27ae60"
}


# ============================================================
# KPI CARD HELPERS
# ============================================================

def kpi_card(col, label: str, value: str, delta: str = None, help_text: str = None):
    """Render a single KPI metric card inside the provided Streamlit column."""
    col.metric(label=label, value=value, delta=delta, help=help_text)


def custom_kpi_card(
    col,
    label: str,
    value: str,
    subtext: str = "",
    help_text: str = "",
    top_color: str = "#2563EB",
    badge: str = ""
):
    badge_html = f'<span style="font-size:10px; font-weight:800; background:{top_color}; color:#FFFFFF !important; padding:2px 9px; border-radius:12px; letter-spacing:0.5px; display:inline-block;">{badge}</span>' if badge else ""
    help_attr = f'title="{help_text}"' if help_text else ""
    subtext_html = f'<div style="font-size:12px; color:#475569; margin-top:5px; line-height:1.35;">{subtext}</div>' if subtext else ""
    html = (
        f'<div {help_attr} style="background:#FFFFFF; border:1px solid #E2E8F0; border-top:3.5px solid {top_color}; border-radius:12px; padding:15px 18px; box-shadow:0 1px 3px rgba(0,0,0,0.03); transition:transform 0.18s ease; height:100%;">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">'
        f'<div style="font-size:11.5px; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.6px;">{label}</div>'
        f'{badge_html}'
        f'</div>'
        f'<div style="font-size:20px; font-weight:800; color:#0F172A; line-height:1.25; letter-spacing:-0.3px;">{value}</div>'
        f'{subtext_html}'
        f'</div>'
    )
    if hasattr(col, "html"):
        col.html(html)
    else:
        col.markdown(html, unsafe_allow_html=True)


def render_kpi_row(kpi: dict):
    """Render the standard 4-column KPI row from ml.business_kpis with domain colors."""
    c1, c2, c3, c4 = st.columns(4)
    custom_kpi_card(c1, "Total Predictions", f"{int(kpi['total_predictions']):,}", subtext="Forward evaluations", top_color="#2563EB")
    custom_kpi_card(c2, "High-Risk Records", f"{int(kpi['high_risk_products']):,}", subtext="Stockout probability elevated", top_color="#DC2626")
    custom_kpi_card(c3, "Avg Expected Demand", f"{float(kpi['avg_predicted_sales']):.2f}", subtext="Daily units / store-SKU", top_color="#7C3AED")
    custom_kpi_card(c4, "Avg Reorder Qty", f"{float(kpi['avg_reorder_qty']):.1f}", subtext="7-day buffer allocation", top_color="#D97706")


# ============================================================
# CHART HELPERS
# ============================================================

def risk_donut(kpi: dict, title: str = "Stockout Risk Distribution") -> go.Figure:
    """Return a donut chart of HIGH / MEDIUM / LOW risk counts."""
    labels = ["HIGH", "MEDIUM", "LOW"]
    values = [
        kpi["high_risk_products"],
        kpi["medium_risk_products"],
        kpi["low_risk_products"]
    ]
    colors = [RISK_COLORS[l] for l in labels]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.48,
        marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
        textinfo="label+percent",
        textfont=dict(color="#1A2B1F", size=12),
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(color="#1A2B1F", size=14)),
        showlegend=True,
        height=350,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        legend=dict(font=dict(color="#1A2B1F")),
        margin=dict(t=50, b=20, l=20, r=20),
    )
    return fig


def priority_donut(kpi: dict, title: str = "Replenishment Priority") -> go.Figure:
    """Return a donut chart of HIGH / MEDIUM / LOW priority counts."""
    labels = ["HIGH", "MEDIUM", "LOW"]
    values = [
        kpi["high_priority_reorders"],
        kpi["medium_priority_reorders"],
        kpi["low_priority_reorders"]
    ]
    colors = [PRIORITY_COLORS[l] for l in labels]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.48,
        marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
        textinfo="label+percent",
        textfont=dict(color="#1A2B1F", size=12),
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(color="#1A2B1F", size=14)),
        showlegend=True,
        height=350,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        legend=dict(font=dict(color="#1A2B1F")),
        margin=dict(t=50, b=20, l=20, r=20),
    )
    return fig


def horizontal_bar(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    color_col: str = None,
    color_map: dict = None,
    n: int = 10
) -> go.Figure:
    """Return a horizontal bar chart from a DataFrame."""
    df_plot = df.nlargest(n, x_col)

    kwargs = dict(
        x=x_col,
        y=y_col,
        orientation="h",
        title=title,
        labels={x_col: x_col.replace("_", " ").title(),
                y_col: y_col.replace("_", " ").title()}
    )
    if color_col and color_map:
        kwargs["color"] = color_col
        kwargs["color_discrete_map"] = color_map

    fig = px.bar(df_plot, **kwargs)
    fig.update_layout(
        height=400,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FAF8F3",
        font=dict(color="#1A2B1F"),
        title=dict(font=dict(color="#1A2B1F", size=14)),
        xaxis=dict(gridcolor="#E2E8E4", linecolor="#E2E8E4",
                   tickfont=dict(color="#4A5568"), title_font=dict(color="#4A5568")),
        yaxis=dict(autorange="reversed", gridcolor="#E2E8E4", linecolor="#E2E8E4",
                   tickfont=dict(color="#4A5568"), title_font=dict(color="#4A5568")),
        legend=dict(font=dict(color="#1A2B1F")),
        margin=dict(t=50, b=20, l=20, r=20),
    )
    return fig



def risk_badge(risk: str) -> str:
    """Return a coloured HTML badge string for a risk level."""
    colors = {"HIGH": "#e74c3c", "MEDIUM": "#e67e22", "LOW": "#2ecc71"}
    color = colors.get(risk, "#95a5a6")
    return f'<span style="background:{color};color:white;padding:3px 10px;border-radius:12px;font-size:0.85em;font-weight:600;">{risk}</span>'

# ============================================================
# TABLE HELPERS
# ============================================================

def paginated_table(
    df: pd.DataFrame,
    page_size: int = 50,
    key: str = "page",
    column_config: dict = None,
    **kwargs
):
    """Display a large DataFrame with simple pagination and optional column formatting."""
    total = len(df)
    n_pages = max(1, (total - 1) // page_size + 1)
    page = st.number_input(
        f"Page (1 – {n_pages})",
        min_value=1,
        max_value=n_pages,
        value=1,
        step=1,
        key=key
    )
    start = (page - 1) * page_size
    end   = start + page_size
    st.caption(f"Showing rows {start+1}–{min(end, total)} of {total:,}")
    st.dataframe(
        df.iloc[start:end],
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        **kwargs
    )


# ============================================================
# ERROR / EMPTY STATE HELPERS
# ============================================================

def no_data_message(context: str = "this selection"):
    st.info(f"No data found for {context}.")


def db_error_message(detail: str = ""):
    st.error("Could not load the data. Please check the database connection and try again.")


def ai_unsupported_message():
    st.warning(
        "I can answer questions about demand, stockout risk, replenishment, "
        "stores, products, categories, and market-basket insights. "
        "Please rephrase your question or try one of the example queries above."
    )


# ============================================================
# SIDEBAR HELPERS
# ============================================================

def sidebar_store_filter(store_ids: list) -> str:
    """Render a store selector and return the selected value."""
    options = ["All Stores"] + [str(s) for s in sorted(store_ids)]
    return st.sidebar.selectbox("Store", options)


def sidebar_risk_filter() -> list:
    """Render a risk-level multi-select and return selected values."""
    return st.sidebar.multiselect(
        "Stockout Risk",
        ["HIGH", "MEDIUM", "LOW"],
        default=["HIGH", "MEDIUM", "LOW"]
    )


def sidebar_priority_filter() -> list:
    """Render a priority multi-select and return selected values."""
    return st.sidebar.multiselect(
        "Replenishment Priority",
        ["HIGH", "MEDIUM", "LOW"],
        default=["HIGH"]
    )


# ============================================================
# RECOMMENDATION / ALERT CARD
# ============================================================

def recommendation_card(
    container,
    status: str,
    title: str,
    subtitle: str = "",
    demand: str = "",
    reorder: str = "",
    why: str = "",
    action: str = ""
):
    """Render a clean, professional action card for recommendations and alerts."""
    status_upper = str(status).upper()
    if "HIGH" in status_upper or "ACTION" in status_upper or "URGENT" in status_upper:
        border_color = "#DC2626"
        badge_bg = "#FEF2F2"
        badge_color = "#B91C1C"
        badge_text = "🔴 URGENT REORDER"
    elif "MEDIUM" in status_upper or "MONITOR" in status_upper:
        border_color = "#D97706"
        badge_bg = "#FFFBEB"
        badge_color = "#B45309"
        badge_text = "🟡 SCHEDULED BUFFER"
    else:
        border_color = "#0284C7"
        badge_bg = "#F0F9FF"
        badge_color = "#0369A1"
        badge_text = "🔵 ROUTINE COVER"

    metrics_html = ""
    if demand or reorder:
        d_html = f'<div><span style="color:#64748B;">Expected Demand:</span> <strong style="color:#0F172A; font-weight:700;">{demand}</strong></div>' if demand else ""
        r_html = f'<div><span style="color:#64748B;">Recommended Reorder:</span> <strong style="color:{border_color}; font-weight:800;">{reorder}</strong></div>' if reorder else ""
        metrics_html = f'<div style="display:flex; gap:18px; margin:10px 0 6px 0; font-size:12.5px; flex-wrap:wrap;">{d_html}{r_html}</div>'

    why_html = ""
    if why:
        why_html = f'<div style="font-size:12.5px; color:#334155; line-height:1.5; margin-top:8px; background:#F8FAFC; padding:9px 13px; border-radius:7px; border:1px solid #E2E8F0;"><strong style="color:#0F172A;">Reason:</strong> {why}</div>'

    action_html = ""
    if action:
        action_html = f'<div style="margin-top:10px; text-align:right;"><span style="display:inline-block; font-size:11px; font-weight:700; color:#FFFFFF !important; background:{border_color}; padding:5px 12px; border-radius:6px; letter-spacing:0.5px; text-transform:uppercase; box-shadow:0 1px 4px rgba(0,0,0,0.15);">{action}</span></div>'

    subtitle_html = f'<div style="font-size:12px; color:#64748B; margin-top:2px;">{subtitle}</div>' if subtitle else ""

    html = (
        f'<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid {border_color}; border-radius:10px; padding:15px 18px; margin-bottom:12px; box-shadow:0 1px 3px rgba(0,0,0,0.03);">'
        f'<div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">'
        f'<div>'
        f'<div style="font-size:14.5px; font-weight:700; color:#0F172A; letter-spacing:-0.2px;">{title}</div>'
        f'{subtitle_html}'
        f'</div>'
        f'<span style="font-size:10.5px; font-weight:700; color:{badge_color}; background:{badge_bg}; padding:3px 10px; border-radius:20px; white-space:nowrap; border:1px solid {border_color}33;">{badge_text}</span>'
        f'</div>'
        f'{metrics_html}'
        f'{why_html}'
        f'{action_html}'
        f'</div>'
    )
    if hasattr(container, "html"):
        container.html(html)
    else:
        container.markdown(html, unsafe_allow_html=True)