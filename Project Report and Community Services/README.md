![SmartStock AI Banner](https://github.com/DeepakKumar29th/SmartStock-AI/blob/996e9cf6138c8dbf04c7cdf2e924baedf8e4e187/assets/smartstock-banner.png)

# SmartStock AI

> **Data-Driven Inventory Replenishment & Stock Optimization**

SmartStock AI is a retail inventory analytics and decision-support project.

It uses historical retail data to analyze demand, forecast next-day sales, identify stockout risk, and support replenishment decisions.

**Project Flow**

`DATA → ANALYSIS → FORECAST → RISK → REPLENISHMENT → DECISION`

---

## 🌐 Live Demo

**[Open SmartStock AI](https://smartstock-inventory-ai.streamlit.app/)**

---

## 📌 Problem Statement

Retail stores need to maintain the right amount of inventory.

Low inventory can cause stockouts and lost sales, while excess inventory can increase waste and costs.

SmartStock AI helps identify demand patterns, inventory risk, and products that may need replenishment.

---

## 🎯 Objectives

- Analyze historical retail sales
- Understand product and store demand
- Forecast next-day demand
- Identify stockout risk
- Generate replenishment recommendations
- Store inventory updates
- Provide clear business insights

---

## 📊 Datasets

| Dataset | Purpose | Coverage | Main Use |
|---|---|---|---|
| **FreshRetailNet-50K** | Inventory & Demand | 4.5M training records, 50,000 store-product pairs, 898 stores, 865 products, 90 days | Demand forecasting, stockout risk and replenishment |
| **Instacart Market Basket Analysis** | Purchase Behavior | 3.4M orders, 206,209 shoppers, 49,688 products | Purchase and reorder behavior |

**Sources:**

- [FreshRetailNet-50K](https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K)
- [Instacart Market Basket Analysis](https://www.kaggle.com/datasets/psparks/instacart-market-basket-analysis)
- [FreshRetailNet-50K Research Paper](https://arxiv.org/abs/2505.16319)

> The datasets represent different retail environments and are kept separate.

---

## 🛠️ Technology Stack

| Area | Technology |
|---|---|
| Programming | Python |
| Data Analysis | Pandas, NumPy |
| Database | PostgreSQL |
| Machine Learning | Scikit-Learn |
| Web Application | Streamlit |
| Visualization | Plotly |
| Business Intelligence | Power BI |
| AI Assistant | Google Gemini API |
| Testing | Pytest |
| Version Control | Git & GitHub |

---

## 🔄 How It Works
```
Retail Data
     ↓
Data Cleaning
     ↓
PostgreSQL
     ↓
Feature Engineering
     ↓
Demand Forecast
     ↓
Stockout Risk
     ↓
Replenishment Recommendation
     ↓
Manager Decision 
```

---

## 🚀 Application

SmartStock AI includes 8 pages:

| Page | Purpose |
|---|---|
| Dashboard | Overall inventory summary |
| Products | Product demand and risk |
| Stores | Store performance and risk |
| Demand & Forecast | Demand and forecast analysis |
| Inventory Risk | Stockout risk analysis |
| Replenishment | Reorder recommendations |
| Add Inventory Data | Add inventory information |
| AI Inventory Assistant | Explain project results |

---

## 🤖 Machine Learning

A **Random Forest Regressor** is used for next-day demand forecasting.

The model uses historical sales, recent demand, stockout history, calendar information, discounts, and weather-related features.

### Results

| Metric | Value |
|---|---:|
| MAE | 0.3889 |
| RMSE | 0.6451 |
| R² | 0.8814 |
| MAPE | 53.90% |

A time-based train/test split is used to prevent future data from being used for earlier predictions.

> MAPE is relatively high because the dataset contains many low and zero-sales observations.


---

## 📦 Replenishment Logic

The project uses predicted demand to create a simple 7-day demand-cover recommendation.

```text
Suggested Reorder Quantity = Predicted Demand × 7
```



---

## ☁️ Database & Deployment

SmartStock AI uses **PostgreSQL** to store and manage project data, analysis results, forecasts, risk information, and inventory decisions.

The project uses PostgreSQL in both development and deployment:

- **Development:** PostgreSQL running locally for data processing and testing
- **Production:** [Neon PostgreSQL](https://neon.com/gad_source=1&gad_campaignid=21329093217&gbraid=0AAAAAqiR81pnwVonGqpXvsJb3eQyjFesY&gclid=CjwKCAjwwfnUBhAtEiwAfQpAYsDupQXDUznIgMxddlk2lnhKILAcyibG9oGQpbvzJJW1z1ccR7D2RoCeKYQAvD_BwE) as the cloud database
- **Application:** Streamlit Community Cloud
- **Source Code:** GitHub

### Deployment Architecture

```text
GitHub Repository
       ↓
Streamlit Community Cloud
       ↓
SmartStock AI Application
       ↓
Neon PostgreSQL
       ↓
Project Data & Results
```

---

## 📊 Power BI

Power BI is used for business reporting and visualization.

The dashboards cover:

- Sales and demand
- Stockout analysis
- Store performance
- Product performance
- Category analysis
- Replenishment insights

---

## ⚠️ Limitations

- The main dataset is historical, not live retail data.
- Real-time warehouse inventory is not available.
- Supplier lead times and purchase orders are not included.
- The two datasets are not joined.
- Forecast performance can vary for low and zero-sales products.
- Replenishment results are recommendations, not exact purchase orders.

---

## 📁 Project Structure

```text
SmartStock-AI/
├── data/
├── database/
├── models/
├── python/
├── streamlit/
├── powerbi/
├── tests/
├── docs/
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🎓 Internship & Capstone Project

SmartStock AI was developed as the **final project of my Data Analytics internship and capstone program with SURE ProEd (formerly SURE Trust)**.

The internship focused on developing practical skills in **data analysis, SQL, Python, data visualization, business intelligence, and machine learning**. During the program, I worked on different stages of the data analytics process, including data preparation, database management, exploratory analysis, feature engineering, machine learning, and dashboard development.

As the final capstone project, these skills were combined into **SmartStock AI**, a complete inventory analytics solution that takes historical retail data and turns it into demand forecasts, stockout risk insights, and replenishment recommendations.

### Skills Applied

**Data Analysis | SQL & PostgreSQL | Python | Machine Learning | Power BI | Streamlit | Business Intelligence**

**Program:** Sure Trust Data Analytics Internship & Capstone Program

- [Sure Trust Data Analytics Repository](https://github.com/sure-trust/DEEPAK-KUMAR-S-g1-data-analytics)
- [Sure Trust Wesite](https://www.suretrustforruralyouth.com/)
---
