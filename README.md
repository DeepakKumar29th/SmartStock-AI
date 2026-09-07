![SmartStock AI Banner](assets/smartstock-banner.png)

# SmartStock AI

> **Data-Driven Inventory Replenishment & Stock Optimization**

SmartStock AI is a retail inventory analytics and decision-support system built as a **Data Analytics Capstone Project**.

It uses historical grocery sales data to understand demand, forecast next-day sales, identify stockout risk, and provide replenishment recommendations.

The project combines **Python, PostgreSQL, Machine Learning, Streamlit, Power BI, and an AI Inventory Assistant** into one complete workflow.

### Project Flow

**DATA → ANALYSIS → FORECAST → RISK → REPLENISHMENT → DECISION**

---

## 📌 Problem

Managing inventory is a common challenge for retail stores.

If a product is understocked, it can lead to stockouts and lost sales. If too much stock is kept, it can increase waste and holding costs.

SmartStock AI uses historical sales and stockout data to identify demand patterns, highlight products that may need attention, and support better replenishment decisions.

---

## 🎯 Objectives

- Analyze historical retail sales data
- Understand product and store demand
- Forecast next-day demand
- Identify stockout risk
- Generate replenishment recommendations
- Store new inventory information in PostgreSQL
- Provide interactive business dashboards
- Explain inventory insights using an AI assistant

---

## 📊 Datasets

SmartStock AI uses two publicly available datasets. Each dataset is used for a different purpose.

| Dataset | Purpose | Main Use | Source |
|---|---|---|---|
| **FreshRetailNet-50K** | Inventory & Demand | Sales analysis, stockout analysis, demand forecasting, risk analysis and replenishment | [Hugging Face](https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K) |
| **Instacart Market Basket Analysis** | Purchase Behavior | Product reorder behavior, purchase patterns and market basket analysis | [Kaggle](https://www.kaggle.com/datasets/psparks/instacart-market-basket-analysis) |

### FreshRetailNet-50K

The main dataset used in SmartStock AI.

- **4.5 million** training records
- **50,000** store-product pairs
- **898** stores
- **865** products
- **90 days** of historical data

**Research Paper:** [FreshRetailNet-50K on arXiv](https://arxiv.org/abs/2505.16319)

### Instacart Market Basket Analysis

A supporting dataset used to study grocery purchase and reorder patterns.

It is used for:

- Product purchase behavior
- Product reorder behavior
- Market basket analysis

> **Important:** These datasets represent different retail environments and are kept separate. They are not joined together.

---

## 🛠️ Technology Stack

| Area | Technology |
|---|---|
| Programming | Python |
| Data Analysis | Pandas, NumPy |
| Database | PostgreSQL |
| Machine Learning | Scikit-Learn |
| Market Basket Analysis | mlxtend |
| Web Application | Streamlit |
| Visualization | Plotly |
| Business Intelligence | Power BI |
| AI Assistant | Google Gemini API |
| Testing | Pytest |
| Version Control | Git & GitHub |

---

## 🔄 How the Project Works

```text
Retail Data
     ↓
Data Cleaning & Database
     ↓
Feature Engineering
     ↓
Demand Forecasting
     ↓
Stockout Risk Analysis
     ↓
Replenishment Recommendation
     ↓
Manager Decision
     ↓
Database Update
