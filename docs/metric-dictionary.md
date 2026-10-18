# Metric dictionary

All report dates refer to purchase dates from 2017-01-01 through 2018-08-31. Final observed status determines delivery inclusion. Customer state is the delivery/customer dimension, not the seller's state. All monetary values are BRL.

| Metric | Looker Studio expression | Interpretation |
|---|---|---|
| Delivered merchandise value | `SUM(merchandise_value)` | Delivered item prices, excluding freight |
| Delivered orders | `SUM(delivered_orders)` | Additive order count from a unique-order model |
| Average order value | `SUM(merchandise_value) / NULLIF(SUM(delivered_orders), 0)` | Merchandise value per delivered order |
| On-time delivery | `SUM(on_time_orders) / NULLIF(SUM(eligible_delivery_orders), 0)` | Received no later than estimated calendar date |
| Average delivery days | `SUM(delivery_days_sum) / NULLIF(SUM(eligible_delivery_orders), 0)` | Elapsed purchase-to-receipt days among valid dates |
| Average review score | `SUM(review_score_sum) / NULLIF(SUM(reviewed_orders), 0)` | One latest valid review per delivered order |
| Review coverage | `SUM(reviewed_orders) / NULLIF(SUM(delivered_orders), 0)` | Share of delivered orders represented by a valid review |
| Low-rating share | `(SUM(rating_1_count) + SUM(rating_2_count)) / NULLIF(SUM(reviewed_orders), 0)` | Share of selected reviews scoring 1 or 2 |

Use `CASE WHEN SUM(denominator) = 0 THEN NULL ELSE SUM(numerator) / SUM(denominator) END` if the report formula editor does not support NULLIF. An empty or unavailable denominator must not become a zero rate.

Delivery eligibility requires delivered status, a valid purchase timestamp, receipt no earlier than purchase, and an estimated calendar date no earlier than the purchase date. Timezone conversion is not inferred from naive source timestamps. An afternoon receipt on the estimated date is on time.

Reviews are ordered by creation timestamp descending, answer timestamp descending, then review ID descending. Review score is the final deterministic tie-breaker for otherwise identical source keys. Scores outside 1–5 are excluded from review metrics. No invalid scores were found in this build.

## Source contracts

| Worksheet | Unique key | Measures |
|---|---|---|
| orders_daily | purchase_date, customer_state | placed_orders, delivered_orders, canceled_orders, merchandise_value, freight_value, paid_delivered_orders, payment_value, eligible_delivery_orders, on_time_orders, late_orders, delivery_days_sum, reviewed_orders, review_score_sum |
| categories_daily | purchase_date, customer_state, product_category | merchandise_value, delivered_items |
| experience_daily | purchase_date, customer_state, delivery_outcome | delivered_orders, reviewed_orders, review_score_sum, rating_1_count through rating_5_count |
| data_notes | topic | detail |

Every worksheet has exactly one header row. Dates are native dates, amounts are numeric, counts are integers, and identifiers/categories are text. No ratios are pre-averaged in the source tables.

There is no additive category-level order count: one order can contain multiple product categories. Category filtering is restricted to category charts and never silently changes order-level KPIs.

## Rankings and filters

- Date and customer-state controls apply across all analytical sources using unified field IDs.
- Delivery rankings require `SUM(eligible_delivery_orders) >= 30` after filtering.
- Review rankings require `SUM(reviewed_orders) >= 30` after filtering.
- Small groups remain in headline totals. Missing dates and Unknown categories remain visible in the notes.
- Aggregate chart metrics use sums of counts and values, followed by division. Do not average daily/state ratios.
