-- ============================================================
-- SMARTSTOCK AI
-- STEP 5.1 - OVERALL BUSINESS KPIs
-- ============================================================

SELECT
    COUNT(*) AS total_observations,

    COUNT(DISTINCT store_id) AS total_stores,

    COUNT(DISTINCT product_id) AS total_products,

    COUNT(DISTINCT (store_id, product_id))
        AS store_product_combinations,

    COUNT(DISTINCT dt) AS total_days,

    ROUND(SUM(sale_amount)::numeric, 2)
        AS total_sales,

    ROUND(AVG(sale_amount)::numeric, 4)
        AS average_daily_sales,

    ROUND(
        SUM(total_stockout_hours)::numeric,
        2
    ) AS total_stockout_hours,

    ROUND(
        100.0 *
        SUM(CASE WHEN stockout_flag THEN 1 ELSE 0 END)
        / COUNT(*),
        2
    ) AS stockout_rate_pct,

    SUM(
        CASE WHEN sale_amount = 0 THEN 1 ELSE 0 END
    ) AS zero_sales_observations

FROM core.fact_daily_sales;