-- ============================================================
-- SMARTSTOCK AI
-- STEP 4.2.5 - WEATHER & CONTEXT VALIDATION
-- ============================================================

SELECT
    COUNT(*) AS total_rows,

    -- Precipitation
    MIN(precpt) AS min_precpt,
    MAX(precpt) AS max_precpt,
    COUNT(*) FILTER (WHERE precpt < 0) AS negative_precpt,

    -- Temperature
    MIN(avg_temperature) AS min_temperature,
    MAX(avg_temperature) AS max_temperature,

    -- Humidity
    MIN(avg_humidity) AS min_humidity,
    MAX(avg_humidity) AS max_humidity,
    COUNT(*) FILTER (
        WHERE avg_humidity < 0
           OR avg_humidity > 100
    ) AS invalid_humidity,

    -- Wind
    MIN(avg_wind_level) AS min_wind,
    MAX(avg_wind_level) AS max_wind,
    COUNT(*) FILTER (
        WHERE avg_wind_level < 0
    ) AS negative_wind

FROM core.fact_daily_sales;

--------------------------------------

SELECT
    holiday_flag,
    COUNT(*) AS row_count
FROM core.fact_daily_sales
GROUP BY holiday_flag
ORDER BY holiday_flag;
-------------------------------------
SELECT
    activity_flag,
    COUNT(*) AS row_count
FROM core.fact_daily_sales
GROUP BY activity_flag
ORDER BY activity_flag;