-- ============================================================
-- SMARTSTOCK AI
-- STEP 3.3A.1 - POPULATE STORE DIMENSION
-- ============================================================

INSERT INTO core.dim_store (
    store_id,
    city_id
)
SELECT
    store_id,
    city_id
FROM raw.raw_retail_data
GROUP BY
    store_id,
    city_id
ORDER BY
    store_id;


SELECT COUNT(*) AS total_stores
FROM core.dim_store;


SELECT
    store_id,
    COUNT(DISTINCT city_id) AS city_count
FROM core.dim_store
GROUP BY store_id
HAVING COUNT(DISTINCT city_id) <> 1;


SELECT *
FROM core.dim_store
ORDER BY store_id
LIMIT 10;

SELECT
    city_id,
    COUNT(*) AS store_count
FROM core.dim_store
GROUP BY city_id
ORDER BY city_id;

