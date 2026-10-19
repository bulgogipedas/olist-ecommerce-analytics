-- Each many-side is reduced to one record per order before the joins.
CREATE OR REPLACE TABLE order_model AS
WITH item_totals AS (
    SELECT order_id, COUNT(*) AS item_count, SUM(price) AS merchandise_value,
           SUM(freight_value) AS freight_value
    FROM stg_items GROUP BY order_id
), payment_totals AS (
    SELECT order_id, COUNT(*) AS payment_records, SUM(payment_value) AS payment_value
    FROM stg_payments GROUP BY order_id
), latest_reviews AS (
    SELECT order_id, review_id, review_score
    FROM stg_reviews
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY order_id
        ORDER BY created_at DESC NULLS LAST, answered_at DESC NULLS LAST,
                 review_id DESC NULLS LAST, review_score DESC NULLS LAST
    ) = 1
), joined AS (
    SELECT o.*, CAST(o.purchase_at AS DATE) AS purchase_date,
           COALESCE(c.customer_state, 'Unknown') AS customer_state,
           i.item_count, i.merchandise_value, i.freight_value,
           p.payment_records, p.payment_value, r.review_score,
           o.order_status = 'delivered' AS is_delivered,
           COALESCE(o.order_status = 'delivered'
               AND o.purchase_at IS NOT NULL
               AND o.delivered_at >= o.purchase_at
               AND CAST(o.estimated_at AS DATE) >= CAST(o.purchase_at AS DATE), FALSE)
               AS valid_delivery
    FROM stg_orders o
    LEFT JOIN stg_customers c USING (customer_id)
    LEFT JOIN item_totals i USING (order_id)
    LEFT JOIN payment_totals p USING (order_id)
    LEFT JOIN latest_reviews r USING (order_id)
)
SELECT *,
       CASE WHEN NOT is_delivered THEN 'Not delivered'
            WHEN NOT valid_delivery THEN 'Unknown'
            WHEN CAST(delivered_at AS DATE) <= CAST(estimated_at AS DATE) THEN 'On time'
            ELSE 'Late' END AS delivery_outcome,
       CASE WHEN valid_delivery
            THEN DATE_DIFF('second', purchase_at, delivered_at) / 86400.0 END AS delivery_days,
       is_delivered AND COALESCE(review_score BETWEEN 1 AND 5, FALSE) AS is_reviewed
FROM joined;

CREATE OR REPLACE VIEW report_orders AS
SELECT * FROM order_model
WHERE purchase_date BETWEEN DATE '2017-01-01' AND DATE '2018-08-31';

CREATE OR REPLACE VIEW report_items AS
SELECT o.purchase_date, o.customer_state, i.order_id, i.order_item_id,
       COALESCE(p.product_category, 'Unknown') AS product_category,
       i.price, i.freight_value
FROM stg_items i
JOIN report_orders o USING (order_id)
LEFT JOIN stg_products p USING (product_id)
WHERE o.is_delivered;
