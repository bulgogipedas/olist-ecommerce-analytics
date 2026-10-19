-- Run each named query in DuckDB after building the model.
-- Primary KPIs. NULLIF preserves an unavailable ratio instead of inventing zero.
SELECT SUM(merchandise_value) AS merchandise_value_brl,
       SUM(delivered_orders) AS delivered_orders,
       SUM(merchandise_value) / NULLIF(SUM(delivered_orders), 0) AS aov_brl,
       SUM(on_time_orders)::DOUBLE / NULLIF(SUM(eligible_delivery_orders), 0) AS on_time_rate,
       SUM(delivery_days_sum) / NULLIF(SUM(eligible_delivery_orders), 0) AS mean_delivery_days,
       SUM(review_score_sum)::DOUBLE / NULLIF(SUM(reviewed_orders), 0) AS review_score,
       SUM(reviewed_orders)::DOUBLE / NULLIF(SUM(delivered_orders), 0) AS review_coverage
FROM orders_daily;

-- Category sales composition. Category-level distinct order counts are not additive.
SELECT product_category, SUM(merchandise_value) AS merchandise_value_brl,
       SUM(delivered_items) AS delivered_items,
       SUM(merchandise_value) / SUM(SUM(merchandise_value)) OVER () AS sales_share
FROM categories_daily GROUP BY product_category ORDER BY merchandise_value_brl DESC;

-- State-level operational priorities. Small groups remain in totals, not rankings.
SELECT customer_state, SUM(eligible_delivery_orders) AS eligible_orders,
       SUM(late_orders) AS late_orders,
       SUM(on_time_orders)::DOUBLE / NULLIF(SUM(eligible_delivery_orders), 0) AS on_time_rate,
       SUM(delivery_days_sum) / NULLIF(SUM(eligible_delivery_orders), 0) AS mean_delivery_days
FROM orders_daily GROUP BY customer_state HAVING SUM(eligible_delivery_orders) >= 30
ORDER BY late_orders DESC;

-- Delivery experience and ratings are associated; this is not a causal estimate.
SELECT delivery_outcome, SUM(delivered_orders) AS delivered_orders,
       SUM(reviewed_orders) AS reviewed_orders,
       SUM(review_score_sum)::DOUBLE / NULLIF(SUM(reviewed_orders), 0) AS mean_review_score,
       SUM(rating_1_count + rating_2_count)::DOUBLE / NULLIF(SUM(reviewed_orders), 0)
           AS low_rating_share
FROM experience_daily GROUP BY delivery_outcome
HAVING SUM(reviewed_orders) >= 30 ORDER BY delivery_outcome;
