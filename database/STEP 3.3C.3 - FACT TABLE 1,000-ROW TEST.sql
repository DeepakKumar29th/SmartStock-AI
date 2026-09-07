-- ============================================================
-- SMARTSTOCK AI
-- STEP 3.3C.3 - FACT TABLE 1,000-ROW TEST
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

FROM raw.raw_retail_data r
ORDER BY r.dt, r.store_id, r.product_id
LIMIT 1000;


-----------------------------------------------------
--Row count

SELECT COUNT(*) AS fact_rows
FROM core.fact_daily_sales;


--Check stockout calculation
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE stockout_flag = TRUE
    ) AS stockout_rows,
    MIN(total_stockout_hours) AS min_stockout_hours,
    MAX(total_stockout_hours) AS max_stockout_hours
FROM core.fact_daily_sales;

--Check primary-key uniqueness

SELECT
    COUNT(*) AS total_rows,
    COUNT(
        DISTINCT (store_id, product_id, dt)
    ) AS unique_keys
FROM core.fact_daily_sales;


--Check foreign-key relationships
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



--Inspect sample row

SELECT
    store_id,
    product_id,
    dt,
    sale_amount,
    stock_hour6_22_cnt,
    total_stockout_hours,
    stockout_flag
FROM core.fact_daily_sales
ORDER BY dt, store_id, product_id
LIMIT 10;


---Clear Test Rows
TRUNCATE TABLE core.fact_daily_sales;

SELECT COUNT(*) AS fact_rows
FROM core.fact_daily_sales;























