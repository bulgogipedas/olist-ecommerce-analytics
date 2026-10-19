-- Independent order-grain reference for manual native-dashboard filter checks.
-- Execute against the database produced by the standard build command.
-- These expected results are not evidence that the dashboard interactions passed.
WITH cases(case_id, start_date, end_date, customer_state) AS (
    VALUES
        ('whole_window', DATE '2017-01-01', DATE '2018-08-31', NULL),
        ('date_august_2018', DATE '2018-08-01', DATE '2018-08-31', NULL),
        ('state_sp', DATE '2017-01-01', DATE '2018-08-31', 'SP'),
        ('combined_sp_august_2018', DATE '2018-08-01', DATE '2018-08-31', 'SP'),
        ('combined_rj_march_2018', DATE '2018-03-01', DATE '2018-03-31', 'RJ'),
        ('small_group_rr_february_2017', DATE '2017-02-01', DATE '2017-02-28', 'RR'),
        ('empty_january_2016', DATE '2016-01-01', DATE '2016-01-31', NULL)
), totals AS (
    SELECT c.case_id, c.start_date, c.end_date, c.customer_state,
           COUNT(o.order_id) AS placed_orders,
           COUNT(o.order_id) FILTER (WHERE o.is_delivered) AS delivered_orders,
           COALESCE(SUM(o.merchandise_value) FILTER (WHERE o.is_delivered), 0)
               AS merchandise_value,
           COUNT(o.order_id) FILTER (WHERE o.valid_delivery) AS eligible_delivery_orders,
           COUNT(o.order_id) FILTER (WHERE o.delivery_outcome = 'On time') AS on_time_orders,
           COUNT(o.order_id) FILTER (WHERE o.delivery_outcome = 'Late') AS late_orders,
           COALESCE(SUM(o.delivery_days), 0) AS delivery_days_sum,
           COUNT(o.order_id) FILTER (WHERE o.is_reviewed) AS reviewed_orders,
           COALESCE(SUM(o.review_score) FILTER (WHERE o.is_reviewed), 0) AS review_score_sum,
           COUNT(o.order_id) FILTER (WHERE o.is_reviewed AND o.review_score IN (1, 2)) AS low_rating_orders
    FROM cases c
    LEFT JOIN report_orders o
        ON o.purchase_date BETWEEN c.start_date AND c.end_date
       AND (c.customer_state IS NULL OR o.customer_state = c.customer_state)
    GROUP BY c.case_id, c.start_date, c.end_date, c.customer_state
)
SELECT *,
       merchandise_value / NULLIF(delivered_orders, 0) AS average_order_value,
       on_time_orders::DOUBLE / NULLIF(eligible_delivery_orders, 0) AS on_time_delivery_rate,
       delivery_days_sum / NULLIF(eligible_delivery_orders, 0) AS average_delivery_days,
       review_score_sum::DOUBLE / NULLIF(reviewed_orders, 0) AS average_review_score,
       reviewed_orders::DOUBLE / NULLIF(delivered_orders, 0) AS review_coverage,
       low_rating_orders::DOUBLE / NULLIF(reviewed_orders, 0) AS low_rating_share,
       CASE WHEN eligible_delivery_orders >= 30
            THEN on_time_orders::DOUBLE / eligible_delivery_orders
       END AS ranked_on_time_delivery_rate,
       CASE WHEN reviewed_orders >= 30
            THEN review_score_sum::DOUBLE / reviewed_orders
       END AS ranked_average_review_score
FROM totals ORDER BY case_id;
