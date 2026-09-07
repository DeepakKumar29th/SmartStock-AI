-- ============================================================
-- SMARTSTOCK AI
-- STEP 2.2E - DATABASE SCHEMA VERIFICATION
-- ============================================================


-- 1. TABLES
SELECT
    table_schema,
    table_name
FROM information_schema.tables
WHERE table_schema IN ('raw', 'core', 'analytics')
  AND table_type = 'BASE TABLE'
ORDER BY table_schema, table_name;


-- 2. COLUMNS
SELECT
    table_schema,
    table_name,
    ordinal_position,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema IN ('raw', 'core', 'analytics')
ORDER BY table_schema, table_name, ordinal_position;


-- 3. PRIMARY KEYS
SELECT
    tc.table_schema,
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    kcu.ordinal_position
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
    AND tc.table_name = kcu.table_name
WHERE tc.constraint_type = 'PRIMARY KEY'
  AND tc.table_schema IN ('raw', 'core', 'analytics')
ORDER BY
    tc.table_schema,
    tc.table_name,
    kcu.ordinal_position;


-- 4. FOREIGN KEYS
SELECT
    tc.table_schema,
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_schema AS referenced_schema,
    ccu.table_name AS referenced_table,
    ccu.column_name AS referenced_column
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON tc.constraint_name = ccu.constraint_name
    AND tc.table_schema = ccu.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema IN ('raw', 'core', 'analytics')
ORDER BY
    tc.table_schema,
    tc.table_name;


-- 5. CURRENT ROW COUNTS
SELECT 'raw.raw_retail_data' AS table_name,
       COUNT(*) AS row_count
FROM raw.raw_retail_data

UNION ALL

SELECT 'core.dim_store',
       COUNT(*)
FROM core.dim_store

UNION ALL

SELECT 'core.dim_product',
       COUNT(*)
FROM core.dim_product

UNION ALL

SELECT 'core.fact_daily_sales',
       COUNT(*)
FROM core.fact_daily_sales;




