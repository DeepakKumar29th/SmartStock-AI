-- ============================================================
-- SMARTSTOCK AI
-- STEP 3.3C.1 - FACT TABLE TRANSFORMATION PREVIEW
-- ============================================================

SELECT
    store_id,
    product_id,
    dt,
    sale_amount,
    stock_hour6_22_cnt,

    (
        SELECT COUNT(*)
        FROM unnest(hours_stock_status) AS status
        WHERE status = 1
    ) AS total_stockout_hours,

    (
        (
            SELECT COUNT(*)
            FROM unnest(hours_stock_status) AS status
            WHERE status = 1
        ) > 0
    ) AS stockout_flag,

    discount,
    holiday_flag,
    activity_flag,
    precpt,
    avg_temperature,
    avg_humidity,
    avg_wind_level

FROM raw.raw_retail_data

ORDER BY dt, store_id, product_id

LIMIT 20;