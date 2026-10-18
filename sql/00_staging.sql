-- Source IDs remain text. Money is decimal, not floating point.
CREATE OR REPLACE TABLE stg_orders AS
SELECT order_id, customer_id, order_status,
       TRY_CAST(order_purchase_timestamp AS TIMESTAMP) AS purchase_at,
       TRY_CAST(order_delivered_customer_date AS TIMESTAMP) AS delivered_at,
       TRY_CAST(order_estimated_delivery_date AS TIMESTAMP) AS estimated_at
FROM raw_orders;

CREATE OR REPLACE TABLE stg_items AS
SELECT order_id, TRY_CAST(order_item_id AS INTEGER) AS order_item_id,
       product_id, seller_id,
       TRY_CAST(price AS DECIMAL(18,2)) AS price,
       TRY_CAST(freight_value AS DECIMAL(18,2)) AS freight_value
FROM raw_items;

CREATE OR REPLACE TABLE stg_payments AS
SELECT order_id, TRY_CAST(payment_sequential AS INTEGER) AS payment_sequential,
       TRY_CAST(payment_value AS DECIMAL(18,2)) AS payment_value
FROM raw_payments;

CREATE OR REPLACE TABLE stg_reviews AS
SELECT review_id, order_id, TRY_CAST(review_score AS INTEGER) AS review_score,
       TRY_CAST(review_creation_date AS TIMESTAMP) AS created_at,
       TRY_CAST(review_answer_timestamp AS TIMESTAMP) AS answered_at
FROM raw_reviews;

CREATE OR REPLACE TABLE stg_customers AS
SELECT customer_id, COALESCE(NULLIF(customer_state, ''), 'Unknown') AS customer_state
FROM raw_customers;

CREATE OR REPLACE TABLE stg_products AS
SELECT p.product_id,
       COALESCE(NULLIF(t.product_category_name_english, ''), 'Unknown') AS product_category
FROM raw_products p
LEFT JOIN raw_translations t USING (product_category_name);
