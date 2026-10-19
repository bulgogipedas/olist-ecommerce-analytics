# Native Looker Studio build specification

## Current state

The [public native report](https://lookerstudio.google.com/reporting/61137e61-5731-4947-b306-b6872ad2660f/page/dZYBG?hl=en), [three-page native PDF](olist-dashboard.pdf), SQL analysis, validations, and private native Google Sheets sources are complete. Source row counts and primary metric totals reconcile. All three Google Sheets sources use owner's credentials; the workbook remains private. Shared purchase-date and customer-state ID overrides are saved across the sources.

All three native pages are authored. Sales Overview contains merchandise, orders, AOV, monthly trend, and state/category contribution charts. Delivery Performance contains on-time rate, duration, eligible counts, a monthly trend, guarded state-rate bars, and an eligible/late-order table. Customer Experience contains average rating, coverage, reviewed counts, a monthly trend, an outcome comparison with sample counts, and a five-rating distribution.

Percentage data types and display formats are verified: the overall on-time rate displays as 93.21% and coverage as 99.33%. Category labels are readable, definitions and source attribution are present, and the category selector affects its grouped chart only. Native date/state readback for SP in August 2018 matches SQL across all three sources: BRL 387,733.71, 3,164 delivered orders, 90.99% on-time rate, 6.20 delivery days, 4.28 rating, and 99.62% review coverage.

Empty selections, the two-order RR / February 2017 sample, and a second combined RJ / March 2018 selection pass native checks. Public access was verified in a separate browser with no signed-in Google account, while Drive permission metadata shows only the workbook owner. The native PDF was re-exported after fixing axis-label truncation and every page was rendered and inspected. See [dashboard-validation.json](dashboard-validation.json) and the [validation readout](dashboard-validation.md).

This file records the source setup and maintenance procedure. The private workbook URL is supplied to its owner separately rather than published in this repository.

## Source setup

Connect orders_daily, categories_daily, and experience_daily from the verified workbook as separate Google Sheets sources. Use first row as headers and owner's credentials. Confirm purchase_date is Date, customer_state and categorical fields are Text, and all measures are Number with Sum aggregation.

Before constructing charts, use Resource → Manage field names and IDs. Override purchase_date to the same ID `olist_purchase_date` in all three sources, and customer_state to `olist_customer_state`. Do not use blends.

Use one date-range control and one customer-state dropdown at report scope. Default dates are 2017-01-01 through 2018-08-31. All primary charts use purchase_date as their date-range dimension. Category selection is grouped only with category charts.

## Theme and layout

- Three pages named Sales Overview, Delivery Performance, and Customer Experience.
- Fixed landscape canvas, 1200 × 900 pixels, with a white background and 40-pixel margins.
- Public view uses Fit to width. Portfolio screenshots use the native fixed-canvas viewer for a complete page view.
- Dark text on white, restrained teal primary series, and red/amber through green for the five-rating distribution.
- Page title at top left, date/state controls at top right, summary metrics below, followed by trends and segment comparisons.
- Display BRL explicitly, ratios as percentages with two decimals, ratings with two decimals, and count denominators as integers.
- Trend axes use a valid 0–100% scale for delivery and 0–5 for ratings. Extra right plot margin preserves the final month label in the native PDF.

## Page 1: Sales Overview

1. Scorecards: delivered merchandise value, delivered orders, average order value.
2. Monthly time series: purchase_date grouped as Year Month; sum merchandise_value.
3. Horizontal category bar chart: categories_daily, product_category, sum merchandise_value, descending, top 10. Add a category dropdown grouped with this chart only.
4. Horizontal state bar chart: orders_daily, customer_state, sum merchandise_value, descending, top 10.
5. Definition: delivered item prices, excluding freight, grouped by purchase date using final observed delivery status. Currency BRL.

## Page 2: Delivery Performance

1. Scorecards: on-time delivery rate, average delivery duration, eligible delivery orders.
2. Monthly time series: purchase_date Year Month, ratio of summed on_time_orders to eligible_delivery_orders.
3. State performance table: customer_state, eligible_delivery_orders, late_orders, on-time rate, and average delivery days. Sort by late_orders descending.
4. State rate bar chart: customer_state and on-time rate for ranked groups. Use an aggregate expression returning NULL when SUM(eligible_delivery_orders) is below 30. Keep small groups in scorecard totals.
5. Definition: compare receipt and estimate calendar dates. Exclude invalid dates from delivery denominators; retain the orders in sales totals.

## Page 3: Customer Experience

1. Scorecards: average review score, review coverage, reviewed orders.
2. Monthly time series: orders_daily, purchase_date Year Month, ratio of summed review_score_sum to reviewed_orders.
3. Delivery-outcome comparison: experience_daily, delivery_outcome, average review score and reviewed order count. Ranked metrics return NULL below 30 reviewed orders. Unknown outcomes stay in overall totals.
4. Rating distribution: experience_daily with five summed metrics, rating_1_count through rating_5_count. A stacked bar by delivery_outcome retains the full distribution and supports the report's date/state controls.
5. Definition: one latest valid review per delivered order. Relationships between ratings and delivery outcomes are descriptive associations.

Use the metric expressions in metric-dictionary.md. Calculate ratios after aggregation and preserve NULL for zero denominators.

## Acceptance and publishing

- Reconcile the unfiltered scorecards to evidence.json. Delivered merchandise value must equal BRL 13,181,027.13, delivered orders 96,211, on-time numerator 89,672, eligible denominator 96,203, review-score sum 397,204, and reviewed orders 95,568.
- Test date-only, state-only, combined date/state, category-only, and empty selections. Verify the category selector does not change order scorecards.
- Check small filtered groups against the 30-observation ranking rule.
- Use [dashboard-filter-reference.json](dashboard-filter-reference.json), independently queried at order grain by [40_dashboard_filter_reference.sql](../sql/40_dashboard_filter_reference.sql), as the reference for seven date/state scenarios. The observed native checks and their scope are recorded separately in dashboard-validation.json. The RR / February 2017 case has two eligible orders: retain them in overall totals, but suppress the performance ranking.
- Verify text and chart labels are readable at normal zoom on all three pages.
- Share only the report publicly as a viewer. Keep the workbook private. Verify the public report from an unauthenticated view.
- Export the three-page PDF from the verified native report and inspect every page. Save screenshots of the verified dashboard, then add actual demo links and the PDF to the README and PR.
- Reconcile Google Sheets publication notes with the final publication timestamp. Leave the PR ready for review, without merging it.

## Updating the source workbook

Rebuild and validate the local tables first. Update the existing spreadsheet and its existing worksheet ranges, preserving spreadsheet ID, sheet IDs, header names, and field types. Clear only stale rows below a shortened replacement table. Verify row counts and sums before updating the successful-publication note. Do not import a replacement workbook as a new file for a routine update.
