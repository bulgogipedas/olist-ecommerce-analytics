# Sales concentration and delivery experience at Olist

[Explore the public dashboard](https://lookerstudio.google.com/reporting/61137e61-5731-4947-b306-b6872ad2660f/page/dZYBG?hl=en) or [open the native three-page PDF](olist-dashboard.pdf).

## Decision and population

A commercial and operations manager needs to understand which products and regions contribute to sales, where delivery improvement deserves attention, and how review scores differ by delivery experience.

This analysis covers purchases from 1 January 2017 through 31 August 2018 in Olist's historical Brazilian e-commerce snapshot. Merchandise metrics include orders whose final observed status is delivered. The currency is BRL. Merchandise value excludes freight and does not represent Olist's commission revenue or profit.

## Results

| Measure | Result | Population |
|---|---:|---|
| Delivered merchandise value | BRL 13,181,027.13 | Delivered orders in the purchase window |
| Delivered orders | 96,211 | Distinct orders |
| Average order value | BRL 137.00 | Merchandise value / delivered orders |
| On-time delivery | 93.21% | 89,672 of 96,203 eligible delivered orders |
| Average delivery duration | 12.54 days | Eligible delivered orders, elapsed time |
| Average review score | 4.16 / 5 | 95,568 reviewed delivered orders |
| Review coverage | 99.33% | Reviewed / all delivered orders |
| 1–2-star review share | 12.80% | Reviewed delivered orders |

### 1. Sales have meaningful product and geographic concentration

Health and beauty contributes BRL 1,229,557.50, or 9.33% of delivered merchandise value. Watches and gifts contributes 8.83%, and bed, bath and table contributes 7.76%. The five largest categories together account for 39.88%.

São Paulo accounts for BRL 5,055,587.13, or 38.36% of delivered merchandise value. This indicates where commercial planning has substantial exposure, although it does not establish category profitability or advertising returns.

**Action:** Maintain category-level demand and availability reviews for the five largest categories. Validate stock, supplier lead times, and contribution margin with internal sources before changing purchasing or marketing budgets. Monitor delivered merchandise value and order value by category in the dashboard.

### 2. Rio de Janeiro deserves an operational investigation

Rio de Janeiro represents 12.80% of eligible delivery orders but 22.89% of late deliveries. Its on-time rate is 87.86%, compared with 93.21% overall. It has 1,495 late orders from 12,310 eligible orders and a mean delivery duration of 15.30 days.

São Paulo has the largest absolute late-order count, 1,817, but a stronger 95.50% on-time rate on 40,399 eligible orders. Rate and volume therefore identify different operating priorities.

**Action:** Prioritize a review of Rio de Janeiro delivery routes and promise accuracy. Request carrier, dispatch, route, and warehouse data to distinguish fulfillment delays from transport delays. Keep São Paulo in volume-based monitoring. Evaluate any intervention using both on-time rate and absolute late-order count, with matched product and route segments.

### 3. Late deliveries are associated with much lower review scores

Among reviewed delivered orders, late deliveries average 2.27 / 5 across 6,378 reviews. On-time deliveries average 4.29 / 5 across 89,182 reviews. One- or two-star reviews account for 62.40% of reviewed late deliveries and 9.25% of reviewed on-time deliveries.

**Action:** Investigate low ratings among late deliveries and test proactive delay communication and customer recovery. Monitor rating distribution and review coverage alongside delivery performance. This descriptive comparison does not estimate the causal effect of delivery speed; category, region, timing, and other factors may also influence reviews.

### 4. August value fell while order volume grew

August 2018 delivered merchandise value was BRL 838,576.64, down 3.38% from July. Delivered orders increased 3.12% to 6,351, while AOV fell 6.31% to BRL 132.04. The divergence points to lower value per delivered order in this final-status purchase cohort; it does not identify a pricing or product-mix cause.

**Action:** Have the commercial team review basket value and product/category mix, then obtain promotion and price-history evidence before changing discounts. Use the monthly section's prior-calendar-month components and selected states, keeping the main date picker independent to avoid partial-month comparisons.

## Measurement and data quality

- The original source contains 99,441 orders, 112,650 items, 103,886 payment records, and 99,224 reviews.
- The reporting window contains 99,092 placed orders. Of these, 96,211 have delivered status.
- Items and payments are independently aggregated to order level before joining. This prevents a multi-item, multi-payment order from multiplying either value.
- There are 547 source orders with multiple review records. Selecting the latest review removes 551 superseded records before order-level measurement.
- Eight delivered orders lack valid delivery dates. They remain in sales and review totals, and are excluded from delivery-rate and duration denominators.
- There are 643 delivered orders without a selected valid review. Review coverage is displayed instead of assuming those orders received a neutral score.
- There are 1,557 delivered item rows with missing or untranslated categories. They remain under Unknown and in overall sales totals.
- Twenty-seven build assertions verify uniqueness, join coverage, monetary reconciliation, review counts, and delivery partitions. Synthetic regression tests cover the specific join and date-boundary risks.

## Limits and next evidence

The data describes this Olist snapshot and period, not today's Brazilian e-commerce market. Final observed status is used to identify delivered orders, while purchases determine the reporting cohort. This is not historical status-as-of reporting.

Payment totals are not substituted for merchandise value. The delivered-order payment total is BRL 15,375,875.44, while merchandise plus freight is BRL 15,373,120.01. These fields have distinct source meanings, and the difference is retained rather than forced to reconcile.

The source does not provide the costs, inventory, ad spend, or controlled experiments needed to estimate margin, ROAS, stock availability, or causal delivery effects. Rankings require at least 30 eligible observations. The delivery table compares against the fixed observed 93.21% full-period baseline. It is not a target. Actual-versus-target assessments are omitted because the source does not supply business targets.

## Source and reproduction

Source: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), published under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). This portfolio aggregates and transforms the source data. Raw source files are not redistributed in the repository.

Reproduce the analysis with the commands in the repository README. The SQL model and aggregate evidence are included for review.
