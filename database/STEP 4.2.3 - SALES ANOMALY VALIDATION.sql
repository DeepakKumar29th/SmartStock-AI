-- ============================================================
-- STEP 4.2.3 - SALES ANOMALY VALIDATION
-- ============================================================

SELECT
    COUNT(*) AS total_rows,

    ROUND(
        PERCENTILE_CONT(0.95)
        WITHIN GROUP (ORDER BY sale_amount)::numeric,
        4
    ) AS p95_sales,

    ROUND(
        PERCENTILE_CONT(0.99)
        WITHIN GROUP (ORDER BY sale_amount)::numeric,
        4
    ) AS p99_sales,

    ROUND(
        PERCENTILE_CONT(0.999)
        WITHIN GROUP (ORDER BY sale_amount)::numeric,
        4
    ) AS p999_sales,

    MAX(sale_amount) AS maximum_sales

FROM core.fact_daily_sales;

-------------------------------------
WITH thresholds AS (
    SELECT
        PERCENTILE_CONT(0.99)
        WITHIN GROUP (ORDER BY sale_amount) AS p99,

        PERCENTILE_CONT(0.999)
        WITHIN GROUP (ORDER BY sale_amount) AS p999

    FROM core.fact_daily_sales
)

SELECT
    COUNT(*) FILTER (
        WHERE sale_amount > p99
    ) AS above_p99,

    COUNT(*) FILTER (
        WHERE sale_amount > p999
    ) AS above_p999

FROM core.fact_daily_sales
CROSS JOIN thresholds;