--STEP 4.2.4 — Discount & Promotion Validation

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE discount = 0) AS no_discount,
    COUNT(*) FILTER (WHERE discount > 0 AND discount <= 1) AS normal_discount,
    COUNT(*) FILTER (WHERE discount > 1) AS above_one,
    MIN(discount) AS minimum_discount,
    MAX(discount) AS maximum_discount
FROM core.fact_daily_sales;

-----------------------------------------------
SELECT
    ROUND(AVG(discount)::numeric, 4) AS avg_discount,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE discount > 1)
        / COUNT(*),
        2
    ) AS above_one_pct
FROM core.fact_daily_sales;
--------------------------------------------
SELECT
    discount,
    COUNT(*) AS row_count
FROM core.fact_daily_sales
WHERE discount > 1
GROUP BY discount
ORDER BY discount;