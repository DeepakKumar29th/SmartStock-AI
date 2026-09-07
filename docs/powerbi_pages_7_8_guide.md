# SmartStock AI — Power BI Pages 7 & 8: Build Guide

> **Prerequisites:** Power BI Desktop open with the existing `Page 1- Executive Overview.pbix` file.
> PostgreSQL is running on `localhost:5433`, database `smartstock`.

---

## Step 0: Verify PostgreSQL Connection in Power BI

In your existing PBIX, go to:
**Home → Transform Data → Data Source Settings**

Confirm connection:
- Server: `localhost:5433`
- Database: `smartstock`
- Authentication: Database (postgres / your_password)

If not connected yet:
**Home → Get Data → PostgreSQL database**
- Server: `localhost`
- Port: `5433`
- Database: `smartstock`

---

## Step 0B: Load New Tables

Go to **Home → Transform Data** (Power Query Editor).

Add these 4 new queries (New Source → PostgreSQL):

### Query 1: `ProductReorderBehavior`
```sql
SELECT
    product_id,
    product_name,
    aisle,
    department,
    purchase_count,
    reorder_count,
    reorder_rate_pct,
    unique_users,
    avg_cart_position,
    popularity_rank,
    reorder_signal
FROM ml.product_reorder_behavior
ORDER BY purchase_count DESC
```

### Query 2: `MarketBasketRules`
```sql
SELECT
    antecedent_product,
    consequent_product,
    ROUND(support::numeric, 4)    AS support,
    ROUND(confidence::numeric, 3) AS confidence,
    ROUND(lift::numeric, 3)       AS lift,
    sample_users,
    top_n_products_analysed,
    min_support_threshold,
    n_transactions
FROM ml.market_basket_rules
ORDER BY lift DESC
```

### Query 3: `DepartmentSummary`
```sql
SELECT
    department,
    COUNT(*)                              AS product_count,
    SUM(purchase_count)                   AS total_purchases,
    ROUND(AVG(reorder_rate_pct)::numeric, 2) AS avg_reorder_rate,
    SUM(reorder_count)                    AS total_reorders
FROM ml.product_reorder_behavior
GROUP BY department
ORDER BY total_purchases DESC
```

### Query 4: `UnifiedIntelligence`
```sql
SELECT
    product_id,
    ROUND(high_risk_pct::numeric, 2)   AS high_risk_pct,
    inventory_risk_level,
    replenishment_priority,
    ROUND(avg_reorder_qty::numeric, 1) AS avg_reorder_qty,
    ROUND(predicted_sales::numeric, 2) AS predicted_sales,
    urgent_reorders,
    instacart_reorder_signal,
    ROUND(instacart_dept_reorder_rate::numeric, 2) AS instacart_dept_reorder_rate,
    LEFT(business_recommendation, 120) AS business_recommendation,
    integration_note
FROM analytics.unified_product_intelligence
ORDER BY high_risk_pct DESC
```

Click **Close & Apply**.

---

## PAGE 7: Customer & Market Basket Intelligence

### Page Setup
- Right-click on a tab at the bottom → **Insert Page** → rename: `Customer & Basket Intelligence`
- Page background: Dark blue `#0F1923` (or match your existing theme)
- Canvas size: 1280 × 720 (widescreen)

---

### 7A. Page Title Banner
- **Insert → Text Box**
- Text: `🛒 Customer & Market Basket Intelligence`
- Font: Segoe UI Bold, 22pt, White
- Subtext (smaller box): `Source: Instacart Market Basket Analysis | Complementary behavioral evidence — not FreshRetailNet data`
- Font: Segoe UI, 10pt, Grey `#A0A0A0`
- Position: Top of page, full width

---

### 7B. KPI Cards Row (4 cards, across the top)

Insert 4 **Card** visuals using table `ProductReorderBehavior`:

| Card | Field | Aggregation | Label |
|---|---|---|---|
| Card 1 | `product_id` | Count | Total Products Analysed |
| Card 2 | `purchase_count` | Sum | Total Purchase Events |
| Card 3 | `reorder_rate_pct` | Average | Avg Reorder Rate % |
| Card 4 | `unique_users` | Max (use MarketBasketRules.sample_users) | Users Sampled |

**Format each card:**
- Background: `#1A2A3A`
- Font: White, Bold, 24pt value, 11pt label
- No border

---

### 7C. Top 15 Most Purchased Products (Horizontal Bar Chart)

- **Visual:** Clustered Bar Chart (horizontal)
- **Table:** `ProductReorderBehavior`
- **Y-axis:** `product_name` (top 15 — apply Top N filter: Top 15 by `purchase_count`)
- **X-axis:** `purchase_count` (Sum)
- **Color:** Gradient — light blue `#3498DB` to dark `#1A5276`
- **Title:** `Top 15 Most Purchased Products`
- **Size:** Left half of page, middle section
- **Data labels:** On, white, 10pt

> Sort: Sort axis → `purchase_count` Descending

---

### 7D. Top 15 Highest Reorder Rate Products (Horizontal Bar Chart)

- **Visual:** Clustered Bar Chart (horizontal)
- **Table:** `ProductReorderBehavior`
- **Filter:** `purchase_count` >= 1000 (add Visual-level filter)
- **Y-axis:** `product_name` (Top 15 by `reorder_rate_pct`)
- **X-axis:** `reorder_rate_pct` (Average)
- **Color:** by `reorder_signal` field:
  - HIGH = `#E74C3C` (red)
  - MEDIUM = `#F39C12` (orange)
  - LOW = `#2ECC71` (green)
- **Legend:** Show (Reorder Signal)
- **Title:** `Top 15 Products by Reorder Rate (min 1,000 purchases)`
- **Size:** Right half of page, middle section

---

### 7E. Purchases by Department (Treemap)

- **Visual:** Treemap
- **Table:** `DepartmentSummary`
- **Category:** `department`
- **Values:** `total_purchases`
- **Tooltips:** Add `avg_reorder_rate`
- **Title:** `Purchase Volume by Department`
- **Colors:** Diverging — use Power BI default palette
- **Size:** Bottom-left quarter

---

### 7F. Association Rules Scatter Plot

- **Visual:** Scatter Chart
- **Table:** `MarketBasketRules`
- **X-axis:** `support` (don't aggregate — use First/Min)
- **Y-axis:** `confidence`
- **Size:** `lift`
- **Tooltips:** Add `antecedent_product`, `consequent_product`, `lift`
- **Title:** `Association Rules: Support vs Confidence (bubble size = Lift)`
- **Size:** Bottom-right quarter

> This chart makes a great visual for your viva — it shows the trade-off between how common a rule is (support) and how reliable it is (confidence), with lift showing the strength of the association.

---

### 7G. Top 10 Association Rules Table

- **Visual:** Table
- **Table:** `MarketBasketRules`
- **Columns:** `antecedent_product`, `consequent_product`, `support`, `confidence`, `lift`
- **Filter:** Top N = 10 by `lift`
- **Conditional formatting on `lift`:** Color scale from light yellow (lift=1) to dark red (lift=32)
- **Title:** `Top 10 Rules by Lift`
- **Size:** Below scatter plot or bottom center

---

### 7H. Data Governance Notice (Text Box)

- **Insert → Text Box**
- Text:
  ```
  ℹ️ DATA GOVERNANCE NOTE
  This page presents findings from the Instacart Market Basket Analysis dataset
  (Kaggle). These represent customer purchasing patterns from a different retail
  environment and are presented as complementary behavioral evidence only.
  Instacart product IDs and FreshRetailNet product IDs are not equivalent and
  have not been merged at the record level.
  ```
- Font: 9pt, Italic, Grey `#AAAAAA`
- Background: Transparent or very dark
- Position: Bottom of page

---

## PAGE 8: Unified Inventory + Customer Intelligence

### Page Setup
- Right-click tab → **Insert Page** → rename: `Unified Intelligence`
- Same background and canvas settings as Page 7

---

### 8A. Page Title Banner

- Text: `🔗 Unified Inventory + Customer Intelligence`
- Subtext: `FreshRetailNet inventory risk signals × Instacart behavioral signals | Analytical integration — not a record-level merge`

---

### 8B. KPI Cards Row (4 cards)

Using table `UnifiedIntelligence`:

| Card | Measure | Label |
|---|---|---|
| Card 1 | Count of `product_id` where `inventory_risk_level = HIGH` | HIGH Risk Products |
| Card 2 | Average `high_risk_pct` | Avg Inventory Risk % |
| Card 3 | Average `instacart_dept_reorder_rate` | Instacart Reorder Rate (Produce) |
| Card 4 | Count where `replenishment_priority = HIGH` | Urgent Replenishment Items |

---

### 8C. Risk Matrix Scatter Plot (Centerpiece Visual)

- **Visual:** Scatter Chart
- **Table:** `UnifiedIntelligence`
- **X-axis:** `instacart_dept_reorder_rate` (Average) — label: "Instacart Behavioral Signal (Reorder Rate %)"
- **Y-axis:** `high_risk_pct` (Average) — label: "Inventory Risk % (FreshRetailNet)"
- **Size:** `avg_reorder_qty`
- **Color (Play axis or Legend):** `inventory_risk_level`
  - HIGH = `#E74C3C`
  - MEDIUM = `#F39C12`
  - LOW = `#2ECC71`
- **Tooltips:** `product_id`, `high_risk_pct`, `replenishment_priority`, `business_recommendation`
- **Title:** `Inventory Risk vs. Customer Reorder Signal`
- **Reference Lines:**
  - Horizontal: Y = 50 (HIGH risk threshold) — Red dashed
  - Vertical: X = 41 (Produce avg reorder rate) — Blue dashed
- **Size:** Large, center-left of page

> **This is the signature visualization of the dual-dataset architecture.** Products in the top-right quadrant (high inventory risk AND strong behavioral signal) are the most urgent. This chart is what you show first in your viva.

**Add 4 Quadrant Labels (Text Boxes):**
- Top-right: `URGENT — High Risk + Strong Signal` (red)
- Top-left: `AT RISK — High inventory risk` (orange)
- Bottom-right: `MONITOR — Strong signal, low risk` (blue)
- Bottom-left: `STABLE — Low risk, low signal` (green)

---

### 8D. Recommendation Text Table

- **Visual:** Table
- **Table:** `UnifiedIntelligence`
- **Filter:** `inventory_risk_level = HIGH`
- **Columns:** `product_id`, `high_risk_pct`, `replenishment_priority`, `avg_reorder_qty`, `instacart_reorder_signal`, `business_recommendation`
- **Sort:** `high_risk_pct` Descending
- **Conditional formatting on `high_risk_pct`:** Red gradient
- **Title:** `High-Risk Products — Business Recommendations`
- **Size:** Right side of page, top half

---

### 8E. Risk Distribution Donut Charts (side by side)

**Donut 1 — Inventory Risk (FreshRetailNet)**
- **Visual:** Donut Chart
- **Table:** `UnifiedIntelligence`
- **Legend:** `inventory_risk_level`
- **Values:** Count of `product_id`
- **Colors:** HIGH=red, MEDIUM=orange, LOW=green
- **Title:** `Inventory Risk Distribution`

**Donut 2 — Instacart Reorder Signal**
- **Visual:** Donut Chart
- **Table:** `UnifiedIntelligence`
- **Legend:** `instacart_reorder_signal`
- **Values:** Count of `product_id`
- **Colors:** HIGH=`#E74C3C`, MEDIUM=`#F39C12`, LOW=`#2ECC71`
- **Title:** `Instacart Reorder Signal`

---

### 8F. Integration Architecture Diagram (Text/Image)

- **Insert → Image** (or Text Box with styled content)
- Content to show:

```
FreshRetailNet-50K          Instacart Dataset
(Inventory / Demand)        (Customer Behavior)
        │                          │
        ▼                          ▼
  Inventory Risk Score    Department Reorder Rate
  (% high-stockout days)  (avg reorder rate in category)
        │                          │
        └──────────┬───────────────┘
                   ▼
        Unified Product Intelligence
        (analytics schema — READ ONLY VIEW)
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   Power BI   Streamlit    AI Assistant
```

- **Title:** `Dual-Dataset Integration Architecture`
- **Position:** Bottom of page

---

### 8G. Data Governance Notice

Same as Page 7, adapted:
```
ℹ️ INTEGRATION NOTE
The Instacart reorder signal shown here is sourced from the produce
department (the closest behavioral proxy for FreshRetailNet's perishable SKUs).
This is an analytical approximation — not a direct product-level match.
FreshRetailNet and Instacart product IDs are from different retail environments
and have NOT been merged at the record level.
```

---

## Final Steps in Power BI

### 1. Add to Navigation (if your existing PBIX has a navigation bar)
Add buttons or bookmarks for Pages 7 and 8.

### 2. Set Page Tooltips
For the scatter charts, enable **Tooltip Page** behavior so hovering shows the product recommendation.

### 3. Publish / Export
- **File → Export → PDF** — export all 8 pages as a single PDF for submission
- **File → Save As** — save as `SmartStock AI - Full Dashboard.pbix`

### 4. Rename existing PBIX
Rename `Page 1- Executive Overview.pbix` → `SmartStock AI - Full Dashboard.pbix` after all pages are built.

---

## DAX Measures to Create

Go to **Modeling → New Measure** and add these to the `ProductReorderBehavior` table:

```dax
-- Total Basket Rules
Total Rules = COUNTROWS(MarketBasketRules)

-- Avg Lift
Avg Lift = AVERAGE(MarketBasketRules[lift])

-- Max Lift
Max Lift = MAX(MarketBasketRules[lift])

-- High Reorder Products
High Reorder Products =
COUNTROWS(
    FILTER(ProductReorderBehavior, ProductReorderBehavior[reorder_signal] = "HIGH")
)

-- Pct High Risk (Unified)
Pct High Risk =
DIVIDE(
    COUNTROWS(FILTER(UnifiedIntelligence, UnifiedIntelligence[inventory_risk_level] = "HIGH")),
    COUNTROWS(UnifiedIntelligence)
) * 100
```

---

## Viva Talking Points for Pages 7 & 8

**When asked about the scatter plot on Page 8:**
> "This visualization is the core contribution of our dual-dataset architecture. The Y-axis represents inventory stockout risk from FreshRetailNet — how often a product was at high risk during the forecast window. The X-axis represents the reorder rate from the Instacart dataset — a complementary signal showing how habitually customers repurchase products in this category. Products in the top-right quadrant face both high inventory risk AND high customer demand pressure, making them the most critical replenishment targets."

**When asked why you didn't join the datasets:**
> "These datasets come from entirely different retail environments with no shared customer, store, or product identifiers. A record-level join would be academically invalid — it would imply that product 267 in FreshRetailNet is the same real-world product as product 267 in Instacart, which is arbitrary. Instead, we use a cross-dataset analytical architecture where each dataset contributes a distinct signal layer, combined at the analytical level. This is documented explicitly in our integration_note column and labeled on every visualization."

**When asked about the association rules:**
> "We used the FP-Growth algorithm, which is more memory-efficient than Apriori for large datasets. We analyzed the top 300 most popular products across 794,402 transactions, generating 204 association rules. The strongest rule — Greek yogurt variants with lift 32 — means customers are 32 times more likely to purchase these two products together than by chance. These patterns support cross-selling recommendations and planogram decisions."
