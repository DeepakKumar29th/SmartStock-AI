-- STEP 5.6 — Discount, Holiday & Activity Impact Analysis

-- 5.6.1 — Discount Impact

SELECT
    CASE
        WHEN discount = 1 THEN 'No Discount'
        WHEN discount < 1 THEN 'Discount Applied'
        ELSE 'Above 1'
    END AS discount_group,

    COUNT(*) AS observations,

    ROUND(AVG(sale_amount)::numeric, 4)
        AS avg_sales,

    ROUND(SUM(sale_amount)::numeric, 2)
        AS total_sales,

    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE sale_amount = 0
        ) / COUNT(*),
        2
    ) AS zero_sales_pct

FROM core.fact_daily_sales

GROUP BY
    CASE
        WHEN discount = 1 THEN 'No Discount'
        WHEN discount < 1 THEN 'Discount Applied'
        ELSE 'Above 1'
    END

ORDER BY avg_sales DESC;

---------------------------------------

--5.6.2 — Holiday Impact

SELECT
    holiday_flag,

    COUNT(*) AS observations,

    ROUND(AVG(sale_amount)::numeric, 4)
        AS avg_sales,

    ROUND(SUM(sale_amount)::numeric, 2)
        AS total_sales,

    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE sale_amount = 0
        ) / COUNT(*),
        2
    ) AS zero_sales_pct

FROM core.fact_daily_sales

GROUP BY holiday_flag

ORDER BY holiday_flag;


-----------------------------------------------

--5.6.3 — Activity Impact


SELECT
    activity_flag,

    COUNT(*) AS observations,

    ROUND(AVG(sale_amount)::numeric, 4)
        AS avg_sales,

    ROUND(SUM(sale_amount)::numeric, 2)
        AS total_sales,

    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE sale_amount = 0
        ) / COUNT(*),
        2
    ) AS zero_sales_pct

FROM core.fact_daily_sales

GROUP BY activity_flag

ORDER BY activity_flag;

