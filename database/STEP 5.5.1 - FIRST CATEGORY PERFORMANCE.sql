-- ============================================================
-- SMARTSTOCK AI
-- STEP 5.5.1 - FIRST CATEGORY PERFORMANCE
-- ============================================================

SELECT
    p.first_category_id,

    COUNT(DISTINCT p.product_id)
        AS products,

    COUNT(DISTINCT f.store_id)
        AS stores,

    ROUND(SUM(f.sale_amount)::numeric, 2)
        AS total_sales,

    ROUND(AVG(f.sale_amount)::numeric, 4)
        AS avg_sales_per_observation,

    SUM(f.total_stockout_hours)
        AS total_stockout_hours,

    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE f.stockout_flag = TRUE
        ) / COUNT(*),
        2
    ) AS stockout_rate_pct,

    COUNT(*) FILTER (
        WHERE f.sale_amount = 0
    ) AS zero_sales_observations

FROM core.fact_daily_sales f

JOIN core.dim_product p
    ON f.product_id = p.product_id

GROUP BY p.first_category_id

ORDER BY total_sales DESC;