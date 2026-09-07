# SmartStock AI: Retail Inventory Intelligence & Demand Forecasting

> **End-to-End Retail Decision-Support System**  
> *Data Analytics Capstone Project combining FreshRetailNet-50K (Supply & Inventory Layer) and Instacart Market Basket Analysis (Customer Behavior Layer)*

---
![SmartStock AI Banner](assets/smartstock-banner.png)
## 1. Project Overview

**SmartStock AI** is a full-stack retail decision-support platform designed to help grocery store managers, category planners, and supply chain analysts optimize inventory replenishment, anticipate stockout risks, and understand product-level demand drivers. 

Rather than functioning as a passive dashboard that merely displays historical charts, SmartStock AI implements an active operational workflow:
$$\text{DATA} \longrightarrow \text{ANALYSIS} \longrightarrow \text{FORECAST} \longrightarrow \text{RISK} \longrightarrow \text{RECOMMENDATION} \longrightarrow \text{MANAGER DECISION} \longrightarrow \text{DATABASE UPDATE}$$

The application allows store managers to inspect ML-generated demand forecasts, review stockout risk tiers, evaluate automated reorder recommendations, record authoritative approval/modification/rejection decisions directly to a PostgreSQL database, capture daily operational intake records, and interact with a grounded AI Inventory Assistant for instant data explanation.

---

## 2. Problem Statement

Retail grocery operations face two opposing pressures:
1. **Stockouts (Understocking):** When popular items run out of stock, retailers suffer lost revenue, damaged customer loyalty, and distorted demand signals (*censored demand*). Perishable items and staple goods require rapid replenishment before shelves empty.
2. **Overstocking:** Holding excess perishable inventory leads to spoilage, waste, and trapped working capital.

Traditional replenishment relies on manual spreadsheets, static reorder points, or gut feeling, which fail to capture day-of-week seasonality, promotion lifts, weather anomalies, and stockout history. SmartStock AI bridges this gap by combining machine-learning demand forecasting with an interactive human-in-the-loop decision-support interface.

---

## 3. Project Objectives

- **Accurate Next-Day Demand Forecasting:** Predict store-product daily sales using machine learning trained on multi-store grocery sales history.
- **Explainable Stockout Risk Classification:** Categorize inventory risk into transparent, rule-based tiers (High, Medium, Low) with actionable plain-English root causes.
- **Actionable Replenishment Recommendations:** Compute 7-day demand-cover reorder quantities to support timely ordering before stockouts occur.
- **Human-in-the-Loop Decision Capture:** Empower managers to approve, adjust, or reject system recommendations, persisting all decisions with timestamps and notes into PostgreSQL (`app.replenishment_decisions`).
- **Operational Daily Intake:** Provide a clean data intake form for store staff to log daily sales, stock status, discounts, and event flags (`app.inventory_updates`).
- **Complementary Basket Intelligence:** Discover co-purchase affinity and repeat reorder patterns from real-world grocery transaction baskets.
- **Grounded AI Explanation:** Provide natural-language explanations of existing predictions and risk factors without LLM hallucination.

---

## 4. Data Sources

The project utilizes two distinct, publicly available, research-grade datasets. **They are intentionally maintained as separate layers and are not joined together.**

### Dataset 1: FreshRetailNet-50K (Primary — Supply & Inventory Layer)
- **Source:** Dingdong Inc. / [Hugging Face](https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K)
- **Research Paper:** [arXiv:2505.16319](https://arxiv.org/abs/2505.16319)
- **Scope:** 4.5 million records across 898 physical stores, 865 SKUs, 18 cities, and 90 continuous days (March–June 2024).
- **Attributes:** Daily sales volume, daily stockout hours, item discounts, calendar flags (weekdays, holidays), and localized weather metrics (temperature, rainfall).
- **Role in SmartStock AI:** Forms the core data warehouse (`raw`, `core`, and `ml` schemas) used for feature engineering, Random Forest demand forecasting, stockout risk scoring, and replenishment calculations.

### Dataset 2: Instacart Market Basket Analysis (Complementary — Customer Behavior Layer)
- **Source:** [Kaggle Instacart Market Basket Analysis](https://www.kaggle.com/datasets/psparks/instacart-market-basket-analysis)
- **Scope:** 3.4 million grocery checkout orders, 206,209 shoppers, 49,688 products across 134 aisles and 21 departments.
- **Attributes:** Order sequence, product co-occurrence, aisle/department categories, reorder indicators.
- **Role in SmartStock AI:** Powers the Customer Insights module (`instacart` schema) using the FP-Growth association algorithm to identify cross-sell affinity and customer reorder loyalty.

> **Data Governance Notice:** These datasets originate from entirely different retail environments and share no product IDs, store IDs, or customer identifiers. Instacart findings serve strictly as *complementary market-basket benchmarks* and are never joined or merged with FreshRetailNet store sales.

---

## 5. Technology Stack

- **Backend & Database:** PostgreSQL 15+ (`raw`, `core`, `ml`, `app`, `instacart`, `analytics` schemas) with SQLAlchemy and psycopg2.
- **Machine Learning & Analytics:** Scikit-Learn (Random Forest Regressor), Pandas, NumPy, mlxtend (FP-Growth & Association Rules).
- **User Interface:** Streamlit (custom operational warehouse theme), Plotly (interactive data visualizations).
- **LLM Explanation:** Google Gemini API (gemini-1.5-flash / gemini-2.5) with controlled SQL query retrieval.
- **Workflow Automation:** n8n scheduled webhook workflows (`n8n/smartstock_daily_alert.json`).
- **Quality & Testing:** Pytest (13 test modules covering 173 automated end-to-end and component tests).

---

## 6. Project Workflow

The application is architected around a strict 7-stage operational flow:

```
[1. DATA WAREHOUSE]
  FreshRetailNet-50K raw parquet -> PostgreSQL core star schema (dim_store, dim_product, fact_daily_sales)
       │
       ▼
[2. FEATURE ENGINEERING]
  19 features computed: 7-day rolling means, stockout history, lags (1d, 3d, 7d), weather, discounts
       │
       ▼
[3. DEMAND FORECASTING]
  Random Forest Regressor predicts next-day sales (target_next_day_sales) using time-based split
       │
       ▼
[4. RISK CLASSIFICATION]
  Rule-based stockout risk assignment (HIGH / MEDIUM / LOW) based on stockout frequency and velocity
       │
       ▼
[5. REPLENISHMENT RECOMMENDATION]
  Suggested reorder calculated as 7-day demand cover (predicted_sales × 7)
       │
       ▼
[6. MANAGER DECISION SUPPORT]
  Store manager reviews recommendation in Streamlit -> Approves, Modifies, or Rejects
       │
       ▼
[7. DATABASE AUDIT LOG]
  Decision written to PostgreSQL app.replenishment_decisions with manager ID, timestamp, and reasoning
```

---

## 7. Main Features (7 Core Pages)

1. **Dashboard:** High-level inventory overview answering *"How is inventory performing and what needs attention?"* featuring network KPIs (total stores, total products, expected demand, high-risk items), inventory health tiers, top products needing attention, and top stores needing attention.
2. **Products (with Product 360):** Interactive product analysis workspace allowing store managers to select a SKU, optionally select a store, and inspect expected demand, stockout risk, replenishment priority, suggested reorder quantity, and clear reasons.
3. **Stores (with Store 360):** Store-level cockpit displaying total carried products, expected store demand, high-risk counts, and prioritized lists of products requiring attention.
4. **Demand & Forecast:** Focused demand workspace allowing product and store selection to inspect historical sales trends, expected demand, and forecast vs. actual sales without technical jargon.
5. **Inventory Risk:** Clear risk triage workspace displaying items needing attention with standard color-coding (🟢 Low Risk, 🟡 Medium Risk, 🔴 High Risk) and plain-English explanations.
6. **Replenishment:** Core operational decision desk answering *"What should I reorder?"* with 7-day demand cover recommendations and verified manager decisions (**Approve**, **Modify Quantity**, or **Reject**) saved to PostgreSQL.
7. **Add Inventory Data:** Operational data intake workspace allowing managers to enter verified daily sales, shelf stock status, discount, holiday/activity flags, and notes into PostgreSQL with duplicate protection.
8. **AI Inventory Assistant:** Grounded business explanation assistant answering queries like *"Why is this product at risk?"*, *"Which products need attention?"*, and *"Why was this reorder recommended?"* using verified project data.

---

## 8. Machine Learning Approach

### Model Architecture
- **Algorithm:** Random Forest Regressor (`n_estimators=100`, `max_depth=16`, `n_jobs=-1`, `random_state=42`).
- **Target Variable:** `target_next_day_sales` (computed using SQL `LEAD(sale_amount, 1)` ordered by store, product, and date).
- **Features (19 Total):**
  - *Sales History:* `sale_amount`, `lag_1_sales`, `lag_3_sales`, `lag_7_sales`, `rolling_7_mean`, `rolling_14_mean`, `rolling_7_std`.
  - *Stockout Signals:* `stockout_hours`, `rolling_7_stockout_days`.
  - *Pricing & Promotions:* `discount`, `discount_depth`, `promotion_flag`.
  - *Calendar & Events:* `day_of_week`, `is_weekend`, `holiday_flag`, `activity_flag`.
  - *Weather:* `temperature`, `rainfall`, `bad_weather_flag`.
- **Top Feature:** `rolling_7_mean` accounts for **85.4%** of feature importance, demonstrating that recent local demand velocity is the dominant driver of next-day sales.

### Split Methodology & Data Leakage Prevention
- **Time-Based Split:** Standard random splitting introduces data leakage in time series. A strict chronological cut was enforced:
  - **Training Set:** First 84 days (March 26, 2024 &ndash; June 18, 2024), comprising ~4,150,000 records.
  - **Testing Set:** Final 6 days (June 19, 2024 &ndash; June 24, 2024), comprising ~300,000 out-of-sample records.
- **Leakage Prevention:** Features only aggregate backwards in time (`ROWS BETWEEN 6 PRECEDING AND CURRENT ROW`). Predictions are made at day's close for the following day.

### Model Evaluation Metrics
Evaluated strictly on the held-out 300,000-row test dataset:

| Metric | Value | Interpretation |
|---|---|---|
| **MAE (Mean Absolute Error)** | **0.3889** | On average, predictions deviate by less than 0.4 units from actual daily store sales. |
| **RMSE (Root Mean Squared Error)** | **0.6451** | Low penalty on large errors, indicating stable predictions across diverse store volumes. |
| **$R^2$ (Coefficient of Determination)** | **0.8814** | Model explains 88.14% of the variance in next-day sales. *(Note: $R^2$ is not a percentage accuracy).* |
| **MAPE (Mean Absolute Percentage Error)** | **53.90%** | Expectedly elevated due to the mathematical denominator effect of many low/fractional sales values ($y \in [0, 1]$). |

---

## 9. Project Limitations

1. **No Real-Time Warehouse Telemetry:** FreshRetailNet provides daily store sales and stockout hours, but does not provide real-time shelf inventory-on-hand (IOH) or in-transit warehouse quantities. Replenishment recommendations represent a 7-day demand cover benchmark.
2. **Distinct Retail Environments:** Instacart customer basket patterns and FreshRetailNet store sales are from different retail domains. Market basket rules describe observed co-purchase affinity in online grocery orders and are not merged with physical store transactions.
3. **Denominator Sensitivity in MAPE:** Grocery demand datasets contain many days where SKU sales are zero or close to zero. Dividing by near-zero numbers inflates percentage error (MAPE = 53.90%), which is why MAE (0.3889) and $R^2$ (0.8814) are the primary evaluative criteria.
4. **Keyword & Deterministic Intent Routing:** The AI Assistant relies on a curated intent-matching parser mapped to parameter-bound SQL queries rather than unrestricted text-to-SQL generation. This ensures 100% zero-hallucination accuracy, but handles only pre-configured query intents.
5. **Simulated Production Operations:** Automated notifications (n8n) and manager decision logs (`app.replenishment_decisions`) simulate production enterprise workflows on historical research data.

---

## 10. How to Run

### 1. Prerequisites
- **Python:** 3.10, 3.11, or 3.12
- **Database:** PostgreSQL 15+ running locally on port `5433` (or configured via `.env`)
- **Git**

### 2. Environment Setup
```bash
# Clone repository
git clone https://github.com/DeepakKumar29th/SmartStock-AI.git
cd SmartStock-AI

# Create and activate virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database & Secret Configuration
Copy `.env.example` to `.env` and configure your database credentials:
```bash
copy .env.example .env
```
Inside `.env`:
```ini
# Local PostgreSQL
DB_HOST=localhost
DB_PORT=5433
DB_NAME=smartstock
DB_USER=postgres
DB_PASSWORD=your_secure_password

# Neon Cloud PostgreSQL (Optional — overrides local DB if set)
# NEON_DATABASE_URL=postgresql://username:password@host/database?sslmode=require

# Google Gemini API key (Optional — for AI Inventory Assistant)
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Run Automated Test Suite
Verify application integrity and end-to-end workflows across all 13 test modules:
```bash
pytest -v
```
*(All 173 tests should pass).*

### 5. Launch Application
Start the Streamlit application:
```bash
streamlit run streamlit/app.py
```
Open your browser at `http://localhost:8501`.

---

## Viva & Interview Questions
For an exhaustive list of viva/presentation questions, technical rationales, and defense points, refer to [`docs/viva_qa.md`](docs/viva_qa.md).
