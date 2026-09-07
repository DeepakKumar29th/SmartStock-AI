![SmartStock AI Banner](assets/smartstock-banner.png)

# SmartStock AI

> **Data-Driven Inventory Replenishment & Stock Optimization**

SmartStock AI is a retail inventory analytics and decision-support system developed as a **Data Analytics Capstone Project**.

The system uses historical grocery retail data to analyze demand patterns, forecast next-day sales, identify potential stockout risk, and generate inventory replenishment recommendations.

The project combines **Python, PostgreSQL, Machine Learning, Streamlit, Power BI, and an AI Inventory Assistant** into an end-to-end analytics workflow.

### Project Flow

**DATA → ANALYSIS → FORECAST → RISK → REPLENISHMENT → DECISION**

---

## 📌 Problem Statement

Inventory management is a major challenge for retail businesses.

If a product is understocked, it can result in **stockouts, missed sales, and reduced customer satisfaction**. On the other hand, excessive inventory can increase **holding costs, waste, and operational inefficiency**.

SmartStock AI addresses this problem by analyzing historical sales and inventory-related data to identify demand patterns, estimate future demand, assess stockout risk, and support better replenishment decisions.

The system is designed as a **decision-support tool**, helping managers make more informed inventory decisions rather than replacing human judgment.

---

## 🎯 Objectives

The main objectives of SmartStock AI are to:

- Analyze historical retail sales data
- Understand product and store-level demand patterns
- Perform exploratory data analysis and identify important trends
- Engineer features for demand forecasting
- Forecast next-day product demand
- Identify products with potential stockout risk
- Generate replenishment recommendations
- Store inventory and application data in PostgreSQL
- Provide interactive analytics through Streamlit
- Build business intelligence dashboards using Power BI
- Provide explainable inventory insights through an AI assistant
- Support managers in making data-driven inventory decisions

---

# 📊 Datasets

SmartStock AI uses **two publicly available datasets**. Each dataset serves a different analytical purpose.

| Dataset | Purpose | Main Use | Source |
|---|---|---|---|
| **FreshRetailNet-50K** | Retail Inventory & Demand | Sales analysis, stockout analysis, demand forecasting, risk analysis and replenishment | [Hugging Face](https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K) |
| **Instacart Market Basket Analysis** | Grocery Purchase Behavior | Purchase behavior, reorder patterns and market basket analysis | [Kaggle](https://www.kaggle.com/datasets/psparks/instacart-market-basket-analysis) |

> **Important:** The two datasets represent different retail environments and are analyzed separately. They are **not joined or merged together**.

---

## FreshRetailNet-50K

**FreshRetailNet-50K** is the primary dataset used for SmartStock AI's inventory and demand analysis.

The dataset contains retail store-product observations that can be used to study sales, inventory availability, stockout behavior and demand forecasting.

### Dataset Characteristics

- Approximately **4.5 million training records**
- **50,000 store-product pairs**
- **898 stores**
- **865 products**
- **90 days** of historical observations

### Research Paper

**FreshRetailNet-50K: A Large-Scale, Fine-Grained Benchmark for Retail Demand Forecasting**

[Read the research paper on arXiv](https://arxiv.org/abs/2505.16319)

---

## Instacart Market Basket Analysis

The **Instacart Market Basket Analysis** dataset is used as a supporting dataset for understanding grocery purchasing behavior.

It is used for analyses such as:

- Product purchase frequency
- Product reorder behavior
- Customer purchase patterns
- Frequently purchased product combinations
- Market basket analysis
- Association rule mining

The Instacart dataset is treated as a **separate analytical dataset** and is not combined with FreshRetailNet-50K.

---

# 🗄️ Database & Cloud Deployment

## PostgreSQL

PostgreSQL is used as the primary relational database for SmartStock AI.

The project was initially developed and tested using **PostgreSQL locally** and was later connected to **Neon**, a cloud-hosted PostgreSQL platform, for deployment.

The database is used to store and manage application data such as:

- Store information
- Product information
- Forecast results
- Inventory risk indicators
- Replenishment recommendations
- Inventory updates
- Manager decisions

This database layer allows the Streamlit application to work with persistent data instead of relying only on local files.

---

## ☁️ Neon PostgreSQL

SmartStock AI uses **Neon** as its cloud PostgreSQL database for the deployed application.

### Neon Console

[Open Neon Console](https://console.neon.tech/)

The cloud database allows the deployed Streamlit application to access the required project data without depending on a local PostgreSQL installation.

### 🔐 Security

Database credentials, API keys, and other sensitive configuration values are **not stored directly in the source code**.

They are managed using:

- Environment variables
- Streamlit Secrets
- Deployment-specific secret management mechanisms

---

# 🚀 Deployment

SmartStock AI is deployed using **Streamlit Community Cloud**.

### 🌐 Live Application

[Open SmartStock AI](https://smartstock-inventory-ai.streamlit.app/)

### Deployment Architecture

```text
GitHub Repository
       ↓
Streamlit Community Cloud
       ↓
Streamlit Application
       ↓
Neon PostgreSQL
       ↓
Project Data & Results
