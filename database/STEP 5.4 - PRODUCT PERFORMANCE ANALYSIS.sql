-- ============================================================
-- SMARTSTOCK AI
-- STEP 5.4 - PRODUCT PERFORMANCE ANALYSIS
-- ============================================================

SELECT
    product_id,

    COUNT(*) AS observations,

    COUNT(DISTINCT store_id) AS stores,

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

GROUP BY product_id

ORDER BY total_sales DESC;