-- ============================================================
-- SMARTSTOCK AI
-- STEP 4.2.1 - STORE-PRODUCT COVERAGE VALIDATION
-- ============================================================

SELECT
    COUNT(*) AS store_product_combinations,
    MIN(date_count) AS minimum_dates,
    MAX(date_count) AS maximum_dates,
    AVG(date_count) AS average_dates
FROM (
    SELECT
        store_id,
        product_id,
        COUNT(DISTINCT dt) AS date_count
    FROM core.fact_daily_sales
    GROUP BY
        store_id,
        product_id
) coverage;


SELECT COUNT(*) AS incomplete_combinations
FROM (
    SELECT
        store_id,
        product_id,
        COUNT(DISTINCT dt) AS date_count
    FROM core.fact_daily_sales
    GROUP BY
        store_id,
        product_id
    HAVING COUNT(DISTINCT dt) <> 90
) incomplete;


-------Stockout vs Sales Validation

SELECT
    stockout_flag,
    COUNT(*) AS rows,
    ROUND(AVG(sale_amount), 4) AS avg_sales,
    SUM(CASE WHEN sale_amount = 0 THEN 1 ELSE 0 END) AS zero_sales_rows,
    ROUND(
        100.0 * SUM(CASE WHEN sale_amount = 0 THEN 1 ELSE 0 END)
        / COUNT(*),
        2
    ) AS zero_sales_pct
FROM core.fact_daily_sales
GROUP BY stockout_flag
ORDER BY stockout_flag;

















