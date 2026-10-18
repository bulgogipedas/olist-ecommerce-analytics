# Portfolio walkthrough

## Opening: the business decision

"I built this analysis for a commercial and operations manager who needs to understand sales concentration and delivery problems. I used public Olist data to connect delivered sales, delivery promises, and customer ratings. The reporting cohort is purchases from January 2017 through August 2018."

## Explain the architecture

"The source contains separate orders, items, payments, and review records. I load the CSVs into DuckDB locally, keep the transformation logic in SQL, and publish additive summary tables into private Google Sheets. Looker Studio provides the public reporting layer. This design keeps cloud billing out of the project while keeping the calculations reproducible."

## Demonstrate the dashboard

1. Open Sales Overview. Explain BRL 13.18 million in delivered merchandise value, 96,211 delivered orders, and BRL 137.00 AOV. Show the monthly trajectory, product-category contribution, and state contribution.
2. Change the date and state controls. Confirm that all relevant charts use the same selection. Explain that category selection applies only to category charts.
3. Open Delivery Performance. Explain 93.21% on-time delivery and the 96,203 eligible-order denominator. Compare Rio de Janeiro's 87.86% with São Paulo's 95.50%, showing the counts as well as the rates.
4. Open Customer Experience. Compare 2.27 / 5 among reviewed late deliveries with 4.29 / 5 among reviewed on-time deliveries. Show review coverage and the rating distribution. State that this is an association.

## Show the SQL and validation

"A key risk is join fan-out: an order can have several items and several payments. Joining the raw tables would repeat both values. I aggregate items and payments independently before joining to a unique-order model. I also select one latest review per order."

Show the CTEs in `sql/10_order_model.sql` and a relevant test in `tests/test_metrics.py`.

"The pipeline verifies that source totals survive the joins and that category sales equal overall sales. I test same-day estimated delivery, missing dates, duplicate reviews, zero denominators, and repeated builds. Eight delivered orders have invalid delivery dates, so they stay in sales totals but leave the delivery denominator."

## Discuss recommendations

"I would prioritize a Rio de Janeiro operational investigation because it contributes 22.89% of late deliveries from 12.80% of eligible delivery orders. I would request route, dispatch, and carrier evidence before attributing the issue to a particular team. I would also investigate low ratings among late deliveries and test recovery communication, measuring delivery performance and review coverage together."

## Interview questions

**Why not call the main monetary metric revenue?**

The source provides item prices, not Olist's net commission or recognized revenue. Delivered merchandise value is the accurate label.

**Why DuckDB and Sheets rather than a cloud warehouse?**

The dataset fits local analytical processing, and the project constraint was no cloud billing. DuckDB executes readable SQL; Sheets publishes compact aggregates into the reporting tool. A larger or frequently refreshed dataset would justify a different serving layer.

**Why calculate ratios in Looker Studio?**

The report filters multiple days and states. Summing numerators and denominators before division preserves the weighted rate. Averaging state or daily percentages would give small groups too much weight.

**Does late delivery cause poor reviews?**

This analysis does not establish causality. Product category, region, time, or customer expectations could influence both outcomes. A controlled intervention or a more rigorous design is needed to estimate an effect.

**What would you do with internal company access?**

Add inventory, cost, carrier, dispatch, and support-interaction data. Investigate operational causes, define business-owned targets, and measure a delivery or communication intervention against a comparable baseline.
