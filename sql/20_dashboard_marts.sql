-- All numeric measures are additive. Ratios are calculated after filtering.
CREATE OR REPLACE TABLE orders_daily AS
SELECT purchase_date, customer_state,
       COUNT(*) AS placed_orders,
       COUNT(*) FILTER (WHERE is_delivered) AS delivered_orders,
       COUNT(*) FILTER (WHERE order_status = 'canceled') AS canceled_orders,
       COALESCE(SUM(merchandise_value) FILTER (WHERE is_delivered), 0)::DECIMAL(18,2)
           AS merchandise_value,
       COALESCE(SUM(freight_value) FILTER (WHERE is_delivered), 0)::DECIMAL(18,2)
           AS freight_value,
       COUNT(*) FILTER (WHERE is_delivered AND payment_records > 0) AS paid_delivered_orders,
       COALESCE(SUM(payment_value) FILTER (WHERE is_delivered), 0)::DECIMAL(18,2)
           AS payment_value,
       COUNT(*) FILTER (WHERE valid_delivery) AS eligible_delivery_orders,
       COUNT(*) FILTER (WHERE delivery_outcome = 'On time') AS on_time_orders,
       COUNT(*) FILTER (WHERE delivery_outcome = 'Late') AS late_orders,
       COALESCE(SUM(delivery_days), 0)::DOUBLE AS delivery_days_sum,
       COUNT(*) FILTER (WHERE is_reviewed) AS reviewed_orders,
       COALESCE(SUM(review_score) FILTER (WHERE is_reviewed), 0)::BIGINT AS review_score_sum
FROM report_orders
GROUP BY purchase_date, customer_state
ORDER BY purchase_date, customer_state;

CREATE OR REPLACE TABLE categories_daily AS
SELECT purchase_date, customer_state, product_category,
       SUM(price)::DECIMAL(18,2) AS merchandise_value,
       COUNT(*) AS delivered_items
FROM report_items
GROUP BY purchase_date, customer_state, product_category
ORDER BY purchase_date, customer_state, product_category;

CREATE OR REPLACE TABLE experience_daily AS
SELECT purchase_date, customer_state, delivery_outcome,
       COUNT(*) AS delivered_orders,
       COUNT(*) FILTER (WHERE is_reviewed) AS reviewed_orders,
       COALESCE(SUM(review_score) FILTER (WHERE is_reviewed), 0)::BIGINT AS review_score_sum,
       COUNT(*) FILTER (WHERE is_reviewed AND review_score = 1) AS rating_1_count,
       COUNT(*) FILTER (WHERE is_reviewed AND review_score = 2) AS rating_2_count,
       COUNT(*) FILTER (WHERE is_reviewed AND review_score = 3) AS rating_3_count,
       COUNT(*) FILTER (WHERE is_reviewed AND review_score = 4) AS rating_4_count,
       COUNT(*) FILTER (WHERE is_reviewed AND review_score = 5) AS rating_5_count
FROM report_orders WHERE is_delivered
GROUP BY purchase_date, customer_state, delivery_outcome
ORDER BY purchase_date, customer_state, delivery_outcome;
