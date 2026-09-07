-- ============================================================
-- SMARTSTOCK AI
-- STEP 2.2D - PHASE 1 DATABASE TABLES
-- PostgreSQL 18
-- ============================================================


-- ============================================================
-- 1. RAW TABLE
-- ============================================================

CREATE TABLE raw.raw_retail_data (
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


-- ============================================================
-- 2. STORE DIMENSION
-- ============================================================

CREATE TABLE core.dim_store (
    store_id INTEGER PRIMARY KEY,
    city_id INTEGER NOT NULL
);


-- ============================================================
-- 3. PRODUCT DIMENSION
-- ============================================================

CREATE TABLE core.dim_product (
    product_id INTEGER PRIMARY KEY,
    management_group_id INTEGER NOT NULL,
    first_category_id INTEGER NOT NULL,
    second_category_id INTEGER NOT NULL,
    third_category_id INTEGER NOT NULL
);


-- ============================================================
-- 4. DAILY FACT TABLE
-- ============================================================

CREATE TABLE core.fact_daily_sales (
    store_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    dt DATE NOT NULL,

    sale_amount NUMERIC(12,4) NOT NULL,

    stock_hour6_22_cnt INTEGER NOT NULL,
    total_stockout_hours INTEGER NOT NULL,
    stockout_flag BOOLEAN NOT NULL,

    discount NUMERIC(8,4) NOT NULL,
    holiday_flag INTEGER NOT NULL,
    activity_flag INTEGER NOT NULL,

    precpt NUMERIC(10,4) NOT NULL,
    avg_temperature NUMERIC(10,4) NOT NULL,
    avg_humidity NUMERIC(10,4) NOT NULL,
    avg_wind_level NUMERIC(10,4) NOT NULL,

    CONSTRAINT pk_fact_daily_sales
        PRIMARY KEY (store_id, product_id, dt),

    CONSTRAINT fk_daily_store
        FOREIGN KEY (store_id)
        REFERENCES core.dim_store(store_id),

    CONSTRAINT fk_daily_product
        FOREIGN KEY (product_id)
        REFERENCES core.dim_product(product_id)
);