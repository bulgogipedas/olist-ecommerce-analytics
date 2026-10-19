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
| monthly_review | review_month, customer_state | merchandise_value, delivered_orders, previous_merchandise_value, previous_delivered_orders, comparison_available |
| data_notes | topic | detail |

Every worksheet has exactly one header row. Purchase dates are native dates; review_month is YYYY-MM text. Amounts are numeric, counts and the comparison flag are integers, and identifiers/categories are text. No ratios are pre-averaged in the source tables.

There is no additive category-level order count: one order can contain multiple product categories. Category filtering is restricted to category charts and never silently changes order-level KPIs.

## Rankings and filters

- Date applies to the three daily sources. State applies to all four analytical sources through the shared ID `olist_customer_state`.
- The monthly section has its own grouped Month control and intentionally has no purchase-date dimension. It keeps whole-calendar-month comparisons valid when the main Date selection is partial.
- Delivery rankings require `SUM(eligible_delivery_orders) >= 30` after filtering.
- Outcome average ratings, low-rating comparisons, and all five distribution metrics require `SUM(reviewed_orders) >= 30` after filtering. The Unknown outcome may remain as an empty label; its count is retained in the comparison table.
- Small groups remain in headline totals and count columns. Missing dates and Unknown categories remain visible in the notes.
- Aggregate chart metrics use sums of counts and values, followed by division. Do not average daily/state ratios.

## Monthly review

The dense month/state table preserves previous-month sales even when a state has no current-month orders. Only the reporting window's 20 months are published. Current and previous components remain additive; no row-level percentages are exported.

| Metric | Expression after filtering to a month and selected states |
|---|---|
| Value MoM | SUM(merchandise_value) / SUM(previous_merchandise_value) − 1 |
| Orders MoM | SUM(delivered_orders) / SUM(previous_delivered_orders) − 1 |
| AOV MoM | [SUM(merchandise_value) / SUM(delivered_orders)] / [SUM(previous_merchandise_value) / SUM(previous_delivered_orders)] − 1 |

All MoM expressions require MIN(comparison_available) = 1 and positive baseline denominators. AOV also requires current orders > 0. January 2017 has no prior reporting month, so its MoMs show a dash. Zero current sales with a positive prior baseline legitimately gives −100% value/order growth. Monthly AOV stays unavailable for zero current orders. Source purchase coverage is checked against full current/prior calendar boundaries; final observed status still makes this a cohort analysis, rather than historical status-as-of reporting.

## Delivery baseline and sales shares

The delivery table's gap is **100 × (selected state on-time rate − 0.932112304190098)**, in percentage points, guarded at n ≥ 30. Positive means better on-time performance than the fixed all-state January 2017–August 2018 baseline. This observed 93.21% baseline is not a business target and does not move with report filters.

State and category bars display percentage of merchandise value in the selected cohort. The denominator includes categories/states beyond the visible top ten. A category selection rebases that chart to the selected categories and does not alter order KPIs. Presentation labels are maintained in a reusable Looker Category field; source keys remain unchanged.
