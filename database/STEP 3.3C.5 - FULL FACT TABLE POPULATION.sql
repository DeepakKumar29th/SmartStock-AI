-- ============================================================
-- SMARTSTOCK AI
-- STEP 3.3C.5 - FULL FACT TABLE POPULATION
-- ============================================================

INSERT INTO core.fact_daily_sales (
    store_id,
    product_id,
    dt,
    sale_amount,
    stock_hour6_22_cnt,
    total_stockout_hours,
    stockout_flag,
    discount,
    holiday_flag,
    activity_flag,
    precpt,
    avg_temperature,
    avg_humidity,
    avg_wind_level
)
SELECT
    r.store_id,
    r.product_id,
    r.dt,
    r.sale_amount,
    r.stock_hour6_22_cnt,

    (
        SELECT COUNT(*)
        FROM unnest(r.hours_stock_status) AS status
        WHERE status = 1
    ) AS total_stockout_hours,

    (
        (
            SELECT COUNT(*)
            FROM unnest(r.hours_stock_status) AS status
            WHERE status = 1
        ) > 0
    ) AS stockout_flag,

    r.discount,
    r.holiday_flag,
    r.activity_flag,
    r.precpt,
    r.avg_temperature,
    r.avg_humidity,
    r.avg_wind_level

FROM raw.raw_retail_data r;

------------------------------------------

SELECT COUNT(*) AS fact_rows
FROM core.fact_daily_sales;


----------------------------------------------------

--Business-key uniqueness

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT (store_id, product_id, dt)) AS unique_keys
FROM core.fact_daily_sales;


--Stockout-hours validation

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE total_stockout_hours = 0
    ) AS zero_stockout_hours,
    COUNT(*) FILTER (
        WHERE total_stockout_hours > 0
    ) AS positive_stockout_hours,
    MIN(total_stockout_hours) AS min_hours,
    MAX(total_stockout_hours) AS max_hours
FROM core.fact_daily_sales;


--Stockout flag consistency
SELECT COUNT(*) AS inconsistent_rows
FROM core.fact_daily_sales
WHERE
    (total_stockout_hours > 0 AND stockout_flag = FALSE)
    OR
    (total_stockout_hours = 0 AND stockout_flag = TRUE);


--Foreign-key integrity

SELECT COUNT(*) AS orphan_store_rows
FROM core.fact_daily_sales f
LEFT JOIN core.dim_store s
    ON f.store_id = s.store_id
WHERE s.store_id IS NULL;


SELECT COUNT(*) AS orphan_product_rows
FROM core.fact_daily_sales f
LEFT JOIN core.dim_product p
    ON f.product_id = p.product_id
WHERE p.product_id IS NULL;


--Date range

SELECT
    MIN(dt) AS min_date,
    MAX(dt) AS max_date,
    COUNT(DISTINCT dt) AS unique_dates
FROM core.fact_daily_sales;


--Sales sanity check

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE sale_amount < 0) AS negative_sales,
    COUNT(*) FILTER (WHERE sale_amount = 0) AS zero_sales,
    COUNT(*) FILTER (WHERE sale_amount > 0) AS positive_sales,
    MIN(sale_amount) AS min_sales,
    MAX(sale_amount) AS max_sales
FROM core.fact_daily_sales;

