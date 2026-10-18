# Olist E-commerce Analytics

A Data Analyst portfolio examining sales composition, delivery performance, and customer ratings using Olist's public Brazilian e-commerce dataset.

**Business question:** Which products and regions contribute to sales, where does delivery performance fall short, and how do customer ratings differ by delivery experience?

## Analysis results

Purchases from January 2017 through August 2018, using final observed delivery status:

| Primary KPI | Result |
|---|---:|
| Delivered merchandise value | BRL 13,181,027.13 |
| On-time delivery | 93.21% of 96,203 eligible orders |
| Average review score | 4.16 / 5 across 95,568 reviewed orders |

- The five largest categories contribute **39.88%** of delivered merchandise value.
- Rio de Janeiro accounts for **12.80%** of eligible delivery orders and **22.89%** of late deliveries, warranting an operational investigation.
- Reviewed late deliveries average **2.27 / 5**, versus **4.29 / 5** for reviewed on-time deliveries. This is an association, not a causal estimate.

Read the [case study](docs/case-study.md), [metric dictionary](docs/metric-dictionary.md), and [English walkthrough](docs/walkthrough.md). Exact aggregates are available in [evidence.json](docs/evidence.json).

## Architecture

Olist CSV files → local DuckDB → SQL models and validation → private Google Sheets → native Looker Studio.

Python handles source loading and orchestration. The business calculations live in SQL. Items, payments, and reviews are reduced to order grain before joining. The published tables contain additive measures; the reporting layer divides summed numerators by summed denominators after filtering.

## Reproduce the analysis

Requires [uv](https://docs.astral.sh/uv/). Keep the working directory outside the repository:

```bash
uv sync
uv run python olist_pipeline.py fetch --work-dir ../olist-work
uv run python olist_pipeline.py build --work-dir ../olist-work
uv run pytest -q
```

The fetch command downloads the official public archive and extracts seven named CSVs. An existing complete archive at `../olist-work/olist.zip` is reused. If the source requires sign-in in your environment, download the archive from Kaggle and place it there.

The build creates a local DuckDB database and exports three source CSVs, `workbook-data.json`, the aggregate evidence, quality results, and a SHA-256 manifest under the working directory's `build` folder. Repeated builds replace tables rather than appending orders.

### Package the publishing workbook

The optional XLSX packager uses `@oai/artifact-tool` from the Codex spreadsheet runtime. It requires that package to be resolvable from `node_modules`, and a Node executable provided by that runtime. The core SQL and CSV build does not require this packaging dependency.

```bash
ARTIFACT_NODE=/absolute/path/to/codex-runtime/node \
uv run python olist_pipeline.py build --work-dir ../olist-work --xlsx
```

This command also creates `olist-dashboard-sources.xlsx`, ready for native Google Sheets import. Dates are numeric spreadsheet dates with explicit date formatting for Google conversion compatibility. The workbook is a publishing artifact and is not committed to the repository.

## Validation

- **8 regression tests** cover multi-item/multi-payment joins, latest reviews, missing dates, the estimated-date boundary, unknown categories, zero denominators, negative delivery intervals, and repeat builds.
- **23 full-data assertions** verify source-key uniqueness, join coverage, preserved monetary totals, category reconciliation, review counts, and delivery partitions.
- Repeated full-data builds produced identical CSV hashes.
- Native Google Sheets readback reconciled all source row counts and headline numerator/denominator totals. Currency sums agree within BRL 0.01.

See [data quality](docs/data-quality.json), [repeatability](docs/validation.json), and [Sheets reconciliation](docs/sheets-validation.json). The [native source screenshot](docs/images/sheets-source.jpg) records the imported table formatting and dates.

## Reporting status

The analysis and private Google Sheets sources have been built and verified. Native Looker Studio configuration, public-access validation, and dashboard PDF export are being completed. A verified dashboard URL and screenshots will be added after those checks pass.

## Source and attribution

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). This noncommercial portfolio transforms and aggregates the source data. Dataset-derived materials retain this attribution and the source license. Raw CSVs, customer/order identifiers, databases, credentials, and working files are excluded from the repository.

Merchandise value excludes freight and is not Olist's marketplace revenue or profit. Eight delivered orders are excluded from delivery calculations because their delivery dates are invalid. All interpretation is limited to this historical snapshot.
