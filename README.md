![SmartStock AI Banner](assets/smartstock-banner.png)

# SmartStock AI

> **Data-Driven Inventory Replenishment & Stock Optimization**

SmartStock AI is a retail inventory analytics and decision-support system built as a Data Analytics Capstone Project.

It uses historical grocery sales data to understand demand, forecast next-day sales, identify stockout risk, and provide replenishment recommendations.

The project combines **Python, PostgreSQL, Machine Learning, Streamlit, Power BI, and an AI Inventory Assistant** into one complete workflow.

### Project Flow

**DATA → ANALYSIS → FORECAST → RISK → REPLENISHMENT → DECISION**

---

## 📌 Problem

Managing inventory is difficult for retail stores.

If a product is understocked, it can lead to stockouts and lost sales. If too much stock is kept, it can increase waste and holding costs.

SmartStock AI uses historical sales and stockout data to help identify demand patterns, find products that may need attention, and support better replenishment decisions.

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

### FreshRetailNet-50K

This is the **main dataset** used for inventory analysis and demand forecasting.

**Source:** [Hugging Face](https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K)

**Research Paper:** [arXiv](https://arxiv.org/abs/2505.16319)

The dataset contains:

- 4.5 million training records
- 50,000 store-product pairs
- 898 stores
- 865 products
- 90 days of historical data

It is used for:

- Sales analysis
- Stockout analysis
- Demand forecasting
- Risk analysis
- Replenishment recommendations

### Instacart Market Basket Analysis

This dataset is used as a **supporting source** for understanding product purchase and reorder patterns.

**Source:** [Kaggle](https://www.kaggle.com/datasets/psparks/instacart-market-basket-analysis)

It is used for:

- Product reorder behavior
- Product purchase patterns
- Market basket analysis

> **Important:** FreshRetailNet-50K and Instacart represent different retail environments. They are kept as separate datasets and are not joined together.

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
