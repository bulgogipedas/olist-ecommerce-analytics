# Native dashboard validation

Verified on 19 October 2026 against DuckDB results from the official Olist snapshot. Expected filter values are independently calculated at order grain in [40_dashboard_filter_reference.sql](../sql/40_dashboard_filter_reference.sql). [Machine-readable results](dashboard-validation.json) record the scope of each native check.

| Check | Observed native result |
|---|---|
| Default purchase window | BRL 13,181,027.13; 96,211 delivered orders; BRL 137.00 AOV; 93.21% on time across 96,203 eligible orders; 12.54 days; 4.16 rating across 95,568 reviews; 99.33% coverage |
| SP, whole window | BRL 5,055,587.13; 40,406 delivered orders; 95.50% on time; 8.74 days; 4.25 rating; 40,178 reviews |
| August 2018, all states: Sales | BRL 838,576.64; 6,351 delivered orders; BRL 132.04 AOV |
| SP + August 2018, all pages | BRL 387,733.71; 3,164 delivered orders; BRL 122.55 AOV; 90.99% on time; 6.20 days; 4.28 rating; 3,152 reviews; 99.62% coverage |
| RJ + March 2018, all pages | BRL 113,062.84; 864 delivered/eligible orders; BRL 130.86 AOV; 65.51% on time; 24.30 days; 3.26 rating; 848 reviews; 98.15% coverage |
| Category-only scope | Selecting health_beauty in SP + August 2018 leaves order KPIs unchanged and narrows the category chart to BRL 49,676.60 |
| RR + February 2017, all pages | BRL 50.80 and two orders remain in totals. Headline rate is 100.00%, mean duration 9.30 days, rating 4.00, and coverage 100.00%. State ranking and outcome average rating are unavailable below n = 30 |
| January 2016, all pages | Scorecards and tables show No data; no zero-denominator rate is fabricated |
| Public access | All three pages render without a signed-in Google account and reproduce the default KPI values |
| Private source | Google Drive metadata reports shared = false and one owner permission for the workbook |
| PDF | Exported using the report's native Download report (PDF), All Pages option in English; three pages; every rendered page visually inspected |

Monetary scorecards match the SQL reference to BRL 0.01; displayed order and sample counts match exactly. Rates and means are compared at the displayed two-decimal precision. Category totals reconcile to overall merchandise value in both the DuckDB and Google Sheets validation layers.

The PDF was re-exported after widening the final-month chart margin and reducing the delivery-axis label size. The final artifact has complete charts and readable labels with no observed clipping. Static exports preserve the default cohort; use the live report for filters, hover values, and all state-table rows.

## Layout revision

The native report was revised on 19 October 2026 to reduce unused space inside the KPI cards. Card height decreased from 150 to 80 pixels, trends moved up 80 pixels, lower comparison charts grew from 250 to 270 pixels, and the footer decreased from 100 to 50 pixels. The canvas is now 1200 × 840 pixels, with Fit to width saved for public viewing. Metric definitions and source contracts are unchanged.

After the layout changes, the combined SP / August 2018 selection was checked across all three pages: BRL 387,733.71, 3,164 orders, 90.99% on time, 6.20 days, 4.28 rating, 3,152 reviews, and 99.62% coverage. Selecting health_beauty for the full reporting window changes only the category chart to BRL 1,229,557.50; the order KPIs remain BRL 13,181,027.13, 96,211 orders, and BRL 137.00 AOV. The default cohort was restored afterward.

All three screenshots were refreshed. A new All Pages PDF was exported from the public native report, rendered page by page, and visually inspected. All three pages measure 900 × 630 points; headline values and complete August 2018 labels were also checked in extracted text.

The report is a historical descriptive analysis. It does not estimate causal delivery effects, allocate carrier/seller responsibility, or provide financial revenue recognition.
