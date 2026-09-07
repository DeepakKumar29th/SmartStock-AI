-- ============================================================
-- SMARTSTOCK AI
-- STEP 5.3 - STORE PERFORMANCE ANALYSIS
-- ============================================================

SELECT
    store_id,

    COUNT(*) AS observations,

    COUNT(DISTINCT product_id) AS products,

    ROUND(SUM(sale_amount)::numeric, 2)
        AS total_sales,

    ROUND(AVG(sale_amount)::numeric, 4)
        AS avg_sales_per_observation,

    SUM(total_stockout_hours)
        AS total_stockout_hours,

    COUNT(*) FILTER (
        WHERE stockout_flag = TRUE
    ) AS stockout_observations,

    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE stockout_flag = TRUE
        ) / COUNT(*),
        2
    ) AS stockout_rate_pct,

    COUNT(*) FILTER (
        WHERE sale_amount = 0
    ) AS zero_sales_observations

FROM core.fact_daily_sales

GROUP BY store_id

ORDER BY total_sales DESC;