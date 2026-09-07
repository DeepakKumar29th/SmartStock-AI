-- ============================================================
-- SMARTSTOCK AI
-- STEP 3.2C.1
-- CREATE EVALUATION RAW TABLE
-- ============================================================

CREATE TABLE raw.raw_retail_eval (
    city_id INTEGER,
    store_id INTEGER,
    management_group_id INTEGER,
    first_category_id INTEGER,
    second_category_id INTEGER,
    third_category_id INTEGER,
    product_id INTEGER,
    dt DATE,
    sale_amount NUMERIC(12,4),

    hours_sale DOUBLE PRECISION[],
    stock_hour6_22_cnt INTEGER,
    hours_stock_status INTEGER[],

    discount NUMERIC(8,4),
    holiday_flag INTEGER,
    activity_flag INTEGER,

    precpt NUMERIC(10,4),
    avg_temperature NUMERIC(10,4),
    avg_humidity NUMERIC(10,4),
    avg_wind_level NUMERIC(10,4)
);


---------------------------------------

SELECT
    table_schema,
    table_name,
    COUNT(*) AS column_count
FROM information_schema.columns
WHERE table_schema = 'raw'
  AND table_name = 'raw_retail_eval'
GROUP BY
    table_schema,
    table_name;
-------------------------------------
SELECT COUNT(*)
FROM raw.raw_retail_eval;

------------------------------------------



