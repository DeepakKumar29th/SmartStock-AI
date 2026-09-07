-- ============================================================
-- SMARTSTOCK AI
-- STEP 5.10 - REPLENISHMENT RISK CANDIDATES
-- ============================================================

WITH product_metrics AS (

    SELECT
        product_id,

        COUNT(*) AS observations,

        ROUND(AVG(sale_amount)::numeric, 4)
            AS avg_demand,

        ROUND(SUM(sale_amount)::numeric, 2)
            AS total_sales,

        SUM(total_stockout_hours)
            AS total_stockout_hours,

        ROUND(
            100.0 *
            COUNT(*) FILTER (
                WHERE stockout_flag = TRUE
            ) / COUNT(*),
            2
        ) AS stockout_rate_pct,

        ROUND(
            100.0 *
            COUNT(*) FILTER (
                WHERE sale_amount = 0
            ) / COUNT(*),
            2
        ) AS zero_sales_pct

    FROM core.fact_daily_sales

    GROUP BY product_id
),

ranked AS (

    SELECT
        *,

        PERCENT_RANK() OVER (
            ORDER BY avg_demand
        ) AS demand_score,

        PERCENT_RANK() OVER (
            ORDER BY stockout_rate_pct
        ) AS stockout_score,

        PERCENT_RANK() OVER (
            ORDER BY total_sales
        ) AS sales_score

    FROM product_metrics
)

SELECT
    product_id,
    observations,
    avg_demand,
    total_sales,
    total_stockout_hours,
    stockout_rate_pct,
    zero_sales_pct,

    ROUND(
        (
            demand_score * 0.40 +
            stockout_score * 0.40 +
            sales_score * 0.20
        )::numeric,
        4
    ) AS replenishment_risk_score

FROM ranked

ORDER BY replenishment_risk_score DESC

LIMIT 20;