---STEP 5.9 — Demand & Stockout Relationship

--5.9.1 — Demand Level vs Stockout Rate

-- ============================================================
-- SMARTSTOCK AI
-- STEP 5.9.1 - DEMAND VS STOCKOUT
-- ============================================================

WITH demand_groups AS (
    SELECT
        product_id,

        AVG(sale_amount) AS avg_demand,

        AVG(
            CASE
                WHEN stockout_flag = TRUE THEN 1.0
                ELSE 0.0
            END
        ) AS stockout_rate

    FROM core.fact_daily_sales

    GROUP BY product_id
),

classified AS (
    SELECT
        *,
        NTILE(5) OVER (
            ORDER BY avg_demand
        ) AS demand_group
    FROM demand_groups
)

SELECT
    demand_group,

    COUNT(*) AS products,

    ROUND(AVG(avg_demand)::numeric, 4)
        AS avg_demand,

    ROUND(
        100.0 * AVG(stockout_rate)::numeric,
        2
    ) AS stockout_rate_pct

FROM classified

GROUP BY demand_group

ORDER BY demand_group;

--5.9.2 — Correlation
SELECT
    ROUND(
        CORR(
            avg_demand,
            stockout_rate
        )::numeric,
        4
    ) AS demand_stockout_correlation
FROM (
    SELECT
        product_id,

        AVG(sale_amount) AS avg_demand,

        AVG(
            CASE
                WHEN stockout_flag = TRUE THEN 1.0
                ELSE 0.0
            END
        ) AS stockout_rate

    FROM core.fact_daily_sales

    GROUP BY product_id
) x;



