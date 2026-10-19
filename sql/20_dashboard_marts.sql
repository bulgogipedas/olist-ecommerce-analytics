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

-- Calendar-month review has its own month selector. Keep prior-month components
-- additive so state selections recompute changes from sums, including states
-- with no current-month orders. Do not sum or average precomputed growth rates.
CREATE OR REPLACE TABLE monthly_review AS
WITH months AS (
    SELECT month_start::DATE AS month_start
    FROM GENERATE_SERIES(DATE '2017-01-01', DATE '2018-08-01', INTERVAL '1 month') t(month_start)
), states AS (
    SELECT DISTINCT customer_state FROM report_orders
), source_bounds AS (
    SELECT MIN(purchase_at)::DATE AS first_purchase,
           MAX(purchase_at)::DATE AS last_purchase FROM stg_orders
), monthly AS (
    SELECT DATE_TRUNC('month', purchase_date)::DATE AS month_start,
           customer_state, SUM(merchandise_value) AS merchandise_value,
           SUM(delivered_orders)::BIGINT AS delivered_orders
    FROM orders_daily GROUP BY month_start, customer_state
)
SELECT STRFTIME(m.month_start, '%Y-%m') AS review_month, s.customer_state,
       COALESCE(cur.merchandise_value, 0)::DECIMAL(18,2) AS merchandise_value,
       COALESCE(cur.delivered_orders, 0)::BIGINT AS delivered_orders,
       COALESCE(prev.merchandise_value, 0)::DECIMAL(18,2) AS previous_merchandise_value,
       COALESCE(prev.delivered_orders, 0)::BIGINT AS previous_delivered_orders,
       CASE WHEN m.month_start > DATE '2017-01-01'
                  AND b.first_purchase <= (m.month_start - INTERVAL '1 month')::DATE
                  AND b.last_purchase >= LAST_DAY(m.month_start)
            THEN 1 ELSE 0 END::INTEGER AS comparison_available
FROM months m CROSS JOIN states s CROSS JOIN source_bounds b
LEFT JOIN monthly cur ON cur.month_start = m.month_start
                     AND cur.customer_state = s.customer_state
LEFT JOIN monthly prev ON prev.month_start = (m.month_start - INTERVAL '1 month')::DATE
                      AND prev.customer_state = s.customer_state
ORDER BY review_month, customer_state;
