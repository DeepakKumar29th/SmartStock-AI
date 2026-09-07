--STEP 5.8 — Stockout Pattern Analysis


--5.8.1 — Stockout by Day of Week

-- ============================================================
-- SMARTSTOCK AI
-- STEP 5.8.1 - STOCKOUT BY DAY OF WEEK
-- ============================================================

SELECT
    EXTRACT(ISODOW FROM dt)::integer AS day_number,

    TO_CHAR(dt, 'Day') AS day_name,

    COUNT(*) AS observations,

    SUM(total_stockout_hours) AS total_stockout_hours,

    ROUND(
        AVG(total_stockout_hours)::numeric,
        4
    ) AS avg_stockout_hours,

    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE stockout_flag = TRUE
        ) / COUNT(*),
        2
    ) AS stockout_rate_pct,

    ROUND(
        AVG(sale_amount)::numeric,
        4
    ) AS avg_sales

FROM core.fact_daily_sales

GROUP BY
    EXTRACT(ISODOW FROM dt),
    TO_CHAR(dt, 'Day')

ORDER BY day_number;


--5.8.2 — Stockout by Holiday
SELECT
    holiday_flag,

    COUNT(*) AS observations,

    SUM(total_stockout_hours) AS total_stockout_hours,

    ROUND(
        AVG(total_stockout_hours)::numeric,
        4
    ) AS avg_stockout_hours,

    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE stockout_flag = TRUE
        ) / COUNT(*),
        2
    ) AS stockout_rate_pct,

    ROUND(
        AVG(sale_amount)::numeric,
        4
    ) AS avg_sales

FROM core.fact_daily_sales

GROUP BY holiday_flag

ORDER BY holiday_flag;


-- 5.8.3 — Stockout Severity
SELECT
    CASE
        WHEN total_stockout_hours = 0
            THEN 'No Stockout'

        WHEN total_stockout_hours <= 6
            THEN 'Low (1-6h)'

        WHEN total_stockout_hours <= 12
            THEN 'Medium (7-12h)'

        WHEN total_stockout_hours <= 18
            THEN 'High (13-18h)'

        ELSE 'Severe (19-24h)'
    END AS stockout_severity,

    COUNT(*) AS observations,

    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS percentage,

    ROUND(
        AVG(sale_amount)::numeric,
        4
    ) AS avg_sales

FROM core.fact_daily_sales

GROUP BY
    CASE
        WHEN total_stockout_hours = 0
            THEN 'No Stockout'

        WHEN total_stockout_hours <= 6
            THEN 'Low (1-6h)'

        WHEN total_stockout_hours <= 12
            THEN 'Medium (7-12h)'

        WHEN total_stockout_hours <= 18
            THEN 'High (13-18h)'

        ELSE 'Severe (19-24h)'
    END

ORDER BY
    CASE
        WHEN MIN(total_stockout_hours) = 0 THEN 1
        ELSE MIN(total_stockout_hours)
    END;


