-- STEP 5.7 — Weather Impact Analysis

--5.7.1 — Precipitation Impact

-- ============================================================
-- SMARTSTOCK AI
-- STEP 5.7.1 - PRECIPITATION IMPACT
-- ============================================================

SELECT
    CASE
        WHEN precpt = 0 THEN 'No Rain'
        WHEN precpt <= 2 THEN 'Light Rain'
        WHEN precpt <= 5 THEN 'Moderate Rain'
        ELSE 'Heavy Rain'
    END AS rain_group,

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
        WHEN precpt = 0 THEN 'No Rain'
        WHEN precpt <= 2 THEN 'Light Rain'
        WHEN precpt <= 5 THEN 'Moderate Rain'
        ELSE 'Heavy Rain'
    END

ORDER BY avg_sales DESC;

---5.7.2 — Temperature Impact

SELECT
    CASE
        WHEN avg_temperature < 18 THEN 'Cool'
        WHEN avg_temperature < 23 THEN 'Moderate'
        WHEN avg_temperature < 27 THEN 'Warm'
        ELSE 'Hot'
    END AS temperature_group,

    COUNT(*) AS observations,

    ROUND(AVG(sale_amount)::numeric, 4)
        AS avg_sales,

    ROUND(SUM(sale_amount)::numeric, 2)
        AS total_sales

FROM core.fact_daily_sales

GROUP BY
    CASE
        WHEN avg_temperature < 18 THEN 'Cool'
        WHEN avg_temperature < 23 THEN 'Moderate'
        WHEN avg_temperature < 27 THEN 'Warm'
        ELSE 'Hot'
    END

ORDER BY avg_sales DESC;


--5.7.3 — Overall Weather Correlation


SELECT
    ROUND(
        CORR(sale_amount, precpt)::numeric,
        4
    ) AS sales_precipitation_corr,

    ROUND(
        CORR(sale_amount, avg_temperature)::numeric,
        4
    ) AS sales_temperature_corr,

    ROUND(
        CORR(sale_amount, avg_humidity)::numeric,
        4
    ) AS sales_humidity_corr,

    ROUND(
        CORR(sale_amount, avg_wind_level)::numeric,
        4
    ) AS sales_wind_corr

FROM core.fact_daily_sales;



