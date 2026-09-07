-- STEP 4.2.6 — Train vs Evaluation Consistency


SELECT
    COUNT(*) AS eval_rows,
    MIN(dt) AS min_date,
    MAX(dt) AS max_date,
    COUNT(DISTINCT dt) AS unique_dates,
    COUNT(DISTINCT store_id) AS stores,
    COUNT(DISTINCT product_id) AS products
FROM raw.raw_retail_eval;

--Evaluation stores missing from TRAIN

SELECT COUNT(*) AS stores_not_in_train
FROM (
    SELECT DISTINCT store_id
    FROM raw.raw_retail_eval

    EXCEPT

    SELECT DISTINCT store_id
    FROM raw.raw_retail_data
) x;


-- Query 3: Evaluation products missing from TRAIN

SELECT COUNT(*) AS products_not_in_train
FROM (
    SELECT DISTINCT product_id
    FROM raw.raw_retail_eval

    EXCEPT

    SELECT DISTINCT product_id
    FROM raw.raw_retail_data
) x;

--Query 4: Evaluation store-product coverage

SELECT
    COUNT(*) AS eval_store_product_pairs,
    MIN(date_count) AS minimum_dates,
    MAX(date_count) AS maximum_dates,
    AVG(date_count) AS average_dates
FROM (
    SELECT
        store_id,
        product_id,
        COUNT(DISTINCT dt) AS date_count
    FROM raw.raw_retail_eval
    GROUP BY store_id, product_id
) x;

-- Query 5: Evaluation category consistency

SELECT COUNT(*) AS inconsistent_products
FROM (
    SELECT
        product_id,
        COUNT(DISTINCT management_group_id) AS mg,
        COUNT(DISTINCT first_category_id) AS fc,
        COUNT(DISTINCT second_category_id) AS sc,
        COUNT(DISTINCT third_category_id) AS tc
    FROM raw.raw_retail_eval
    GROUP BY product_id
    HAVING
        COUNT(DISTINCT management_group_id) > 1
        OR COUNT(DISTINCT first_category_id) > 1
        OR COUNT(DISTINCT second_category_id) > 1
        OR COUNT(DISTINCT third_category_id) > 1
) x;







