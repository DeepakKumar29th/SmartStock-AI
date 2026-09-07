# SmartStock AI — Viva & Presentation Q&A Guide

> **Comprehensive Defense & Examination Guide**  
> *Prepares you for technical and viva questions on data architecture, feature engineering, machine learning, business rationale, and project boundaries.*

---

### Q1: Why did you choose FreshRetailNet-50K?
**Answer:**  
FreshRetailNet-50K is a publicly available, research-grade grocery retail dataset released by Dingdong Inc. and documented in peer-reviewed research ([arXiv:2505.16319](https://arxiv.org/abs/2505.16319)). Unlike synthetic or toy benchmark datasets, it provides 4.5 million real-world daily transaction records across 898 stores and 865 SKUs over 90 days. Critically, it includes operational attributes rarely found in public datasets: hourly stockout duration, localized weather measurements (rainfall, temperature), and item discounts. This allows us to model real-world retail phenomena such as stockouts, weather-driven surges, and promotion elasticity in a realistic and academically defensible manner.

---

### Q2: Why did you choose the Instacart dataset?
**Answer:**  
The Instacart Market Basket Analysis dataset (from Kaggle) is a benchmark grocery transaction dataset comprising 3.4 million real customer orders and 32.4 million item selections across 49,688 products. We selected it to introduce a complementary customer-behavior intelligence layer. While FreshRetailNet provides store-level aggregated sales and inventory stockouts, it contains no transaction basket details or customer reorder histories. Instacart provides transaction-level co-occurrence data, enabling market-basket analysis (frequently bought together rules) and customer repeat purchase loyalty scoring.

---

### Q3: Why are two datasets used?
**Answer:**  
Retail decision-making requires two complementary perspectives:
1. **Supply & Inventory Layer (FreshRetailNet):** Answers *"How much will this store sell tomorrow?"* and *"Is this SKU at risk of stocking out?"*
2. **Customer Behavior Layer (Instacart):** Answers *"Which items do shoppers frequently put in the same basket?"* and *"Which products have high reorder retention?"*

Neither dataset alone can answer both operational supply questions and customer basket dynamics. By maintaining both datasets in a unified analytics platform, SmartStock AI equips managers with operational supply forecasts and cross-sell merchandise intelligence simultaneously.

---

### Q4: Can these datasets be joined?
**Answer:**  
**No. They cannot and must not be joined directly.**  
FreshRetailNet and Instacart originate from completely different companies, geographic markets, and retail environments. They share no common primary keys, SKU IDs, store IDs, or customer IDs. Forcing a direct join (e.g., joining FreshRetailNet SKU 267 with Instacart Product 267) would be academically dishonest and technically invalid.  
Instead, SmartStock AI employs a **multi-dataset analytical architecture**: each dataset is ingested into dedicated database schemas (`core`/`ml` for FreshRetailNet, `instacart` for Instacart). Instacart findings are presented strictly as *complementary market-basket benchmarks* to inform merchandising, without contaminating store-level inventory data.

---

### Q5: Why PostgreSQL?
**Answer:**  
PostgreSQL was selected because it is an enterprise-grade, ACID-compliant relational database management system capable of handling multi-million-row analytical tables efficiently. Key reasons include:
1. **Advanced SQL Window Functions:** Essential for computing rolling statistics (`AVG() OVER (PARTITION BY store_id, product_id ORDER BY dt ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)`), time-series lags (`LAG()`), and forward targets (`LEAD()`).
2. **Schema Separation:** Enables clean data governance across `raw`, `core`, `ml`, `app`, `instacart`, and `analytics` schemas.
3. **Transactional Integrity & Concurrency:** Guarantees atomic, ACID-compliant writes when store managers submit replenishment decisions (`app.replenishment_decisions`) or daily inventory intakes (`app.inventory_updates`).
4. **B-Tree Indexing:** Enables sub-second retrieval across 4.5M rows for interactive Streamlit queries.

---

### Q6: Why Random Forest?
**Answer:**  
Random Forest Regressor was chosen for demand forecasting for several technical and operational reasons:
1. **Non-Linear Interactions:** It naturally captures non-linear relationships and feature interactions (e.g., high discount combined with bad weather or weekend effects) without requiring manual interaction terms.
2. **Robustness to Overfitting:** Ensemble averaging across 100 decision trees mitigates overfitting across 898 stores and 865 SKUs.
3. **Interpretability via Feature Importance:** Random Forest provides Mean Decrease in Impurity (MDI), allowing us to demonstrate that `rolling_7_mean` accounts for 85.4% of predictive power.
4. **Strong Empirical Performance:** On our 300,000-row held-out test set, Random Forest achieved an $R^2$ of 0.8814 and an MAE of 0.3889 units/day, providing an accurate, stable baseline.

---

### Q7: Why a time-based train/test split?
**Answer:**  
In time series forecasting, random k-fold cross-validation or random train/test splitting is methodologically flawed because it leaks future information into the past (lookahead bias). For example, training on June 20th data to predict June 10th demand would never occur in real retail operations.  
To simulate real deployment, we enforced a strict **chronological split**:
- **Training Set (Past):** Days 1 to 84 (March 26, 2024 to June 18, 2024; ~4,150,000 records).
- **Testing Set (Future):** Days 85 to 90 (June 19, 2024 to June 24, 2024; ~300,000 records).  
The model is evaluated only on out-of-sample future dates it has never seen during training.

---

### Q8: How did you prevent data leakage?
**Answer:**  
Data leakage was rigorously prevented at three stages:
1. **Target Construction:** The forecast target `target_next_day_sales` was generated using `LEAD(sale_amount, 1)` ordered chronologically. Tomorrow's sales value is strictly isolated as the target and is never included in the input feature matrix $X$.
2. **Causal Rolling & Lag Windows:** All historical features aggregate backwards in time (`ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` for rolling metrics; `LAG(sale_amount, 1)`, `3`, and `7` for lag features). No future rows enter any calculation.
3. **Operational Timing Assumption:** We assume predictions for day $T+1$ are computed at the close of day $T$, when day $T$'s final sales, stockout hours, and discounts are fully settled.

---

### Q9: How is stockout risk defined?
**Answer:**  
Stockout risk is classified using an explainable, transparent rule-based algorithm rather than a black-box model. It evaluates recent stockout severity combined with sales velocity on the test set:
- **HIGH RISK:** The product experienced $\ge 5$ stockout days in the past 7 days AND has high sales velocity (`rolling_7_mean` $\ge 1.5$ units/day).
- **MEDIUM RISK:** The product experienced $\ge 3$ stockout days in the past 7 days OR has moderate velocity (`rolling_7_mean` $\ge 1.0$ unit/day).
- **LOW RISK:** Minimal recent stockout history ($< 3$ days) and stable demand.

This approach provides store managers with an immediate plain-English explanation (e.g., *"Elevated risk due to 5 stockout days in the last week with high customer demand"*).

---

### Q10: What is censored demand?
**Answer:**  
Censored demand occurs when actual customer purchase intent is artificially suppressed because a product is out of stock. If a store has 0 units of milk on the shelf, recorded sales will be 0, even if 50 customers wanted to buy milk.  
In standard regression, training directly on observed sales during stockouts teaches the model that demand was zero, leading to under-forecasting. In FreshRetailNet, the presence of `stockout_hours` allows us to identify when demand was censored. While our baseline model utilizes `stockout_hours` as an explicit input feature, true demand un-censoring (latent demand imputation via Tobit models or Poisson hazard models) is documented as an important future production enhancement.

---

### Q11: What are support, confidence, and lift?
**Answer:**  
These are the three foundational metrics used in Association Rule Mining (FP-Growth):
1. **Support:** The proportion of total transactions that contain both items $A$ and $B$:
   $$\text{Support}(A \rightarrow B) = \frac{\text{Transactions containing } A \text{ and } B}{\text{Total Transactions}}$$
2. **Confidence:** The conditional probability that a basket contains $B$ given that it already contains $A$:
   $$\text{Confidence}(A \rightarrow B) = \frac{\text{Support}(A \cup B)}{\text{Support}(A)}$$
3. **Lift:** The ratio of observed co-occurrence to the expected co-occurrence if $A$ and $B$ were completely independent:
   $$\text{Lift}(A \rightarrow B) = \frac{\text{Confidence}(A \rightarrow B)}{\text{Support}(B)}$$
   - $\text{Lift} > 1$: Positive association (items purchased together more frequently than chance).
   - $\text{Lift} = 1$: Independence.
   - $\text{Lift} < 1$: Negative association (substitutes).

---

### Q12: How is replenishment calculated?
**Answer:**  
In SmartStock AI, the recommended reorder quantity is computed as a **7-day demand cover**:
$$\text{recommended\_reorder\_qty} = \text{predicted\_sales} \times 7$$
This ensures that the store orders sufficient inventory to cover anticipated sales for the upcoming week based on ML demand forecasts.  
*Operational Context:* Because FreshRetailNet provides daily store sales and stockout hours rather than real-time stock-on-hand telemetry, the system calculates gross 7-day requirements. The interactive Replenishment page empowers the store manager to adjust or modify this quantity based on their physical shelf audit before persisting the decision to the database.

---

### Q13: What are the project limitations?
**Answer:**  
1. **No Real-Time Inventory Telemetry:** FreshRetailNet does not provide real-time shelf inventory-on-hand (IOH) or warehouse stock; replenishment is therefore a demand-cover recommendation.
2. **Independent Datasets:** Instacart and FreshRetailNet reflect different retail environments and cannot be directly linked at the SKU or customer level.
3. **MAPE Metric Inflation:** With grocery items, many store-day sales are 0 or 1. In MAPE calculations, dividing by very small values inflates the error (53.90%), making MAE (0.3889) and $R^2$ (0.8814) the reliable performance indicators.
4. **Deterministic Intent Classifier:** The AI Inventory Assistant relies on keyword intent extraction mapped to parameterized SQL queries to guarantee zero hallucination, meaning it only handles supported analytical intents.
5. **Historical Simulation:** Alerts (n8n) and manager approvals simulate an enterprise production environment on historical research data.

---

### Q14: How does Add Inventory Data work, and does it retrain the model?
**Answer:**  
**Add Inventory Data** provides an operational data-intake interface allowing managers to record daily store sales, shelf stock status, discount percentage, holiday/activity flags, and operational notes directly into PostgreSQL (`app.inventory_updates`).
- **Validation & Integrity:** Enforces non-negative sales, valid discount ranges (0–100%), past/present dates, and strict duplicate prevention on `Date + Store + Product` (returning *"This record already exists"* if duplicate).
- **Model Boundary:** Saving a record **does not** automatically retrain the machine learning model. Retraining in enterprise production requires time-series feature engineering, historical aggregation, and validation checks before deployment. The correct explanation is: *"New data is stored in the database and can be used for future analysis and model updates."*
