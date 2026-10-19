"""Load public Olist CSVs, execute reviewable SQL, validate, and export BI sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.request import urlretrieve

import duckdb

ROOT = Path(__file__).resolve().parent
SOURCE_URL = "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
DOWNLOAD_URL = "https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce"
FILES = {
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "translations": "product_category_name_translation.csv",
}
MARTS = ["orders_daily", "categories_daily", "experience_daily", "monthly_review"]


def json_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Unsupported JSON value: {type(value).__name__}")


def write_json(path: Path, value):
    path.write_text(json.dumps(value, default=json_value, ensure_ascii=False,
                               indent=2, sort_keys=True) + "\n")


def records(con, sql):
    cursor = con.execute(sql)
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def run_models(con):
    for name in ["00_staging.sql", "10_order_model.sql", "20_dashboard_marts.sql"]:
        con.execute((ROOT / "sql" / name).read_text())


def validate(con):
    checks = {}

    def check(name, sql):
        value = con.execute(sql).fetchone()[0]
        checks[name] = bool(value)
        if not value:
            raise ValueError(f"Validation failed: {name}")

    for table, key in [("orders", "order_id"), ("customers", "customer_id"),
                       ("products", "product_id"), ("translations", "product_category_name")]:
        check(f"unique_{table}", f"SELECT COUNT(*) = COUNT(DISTINCT {key}) FROM raw_{table}")
    check("unique_item_keys", "SELECT COUNT(*) = COUNT(DISTINCT (order_id, order_item_id)) FROM stg_items")
    check("unique_payment_keys", "SELECT COUNT(*) = COUNT(DISTINCT (order_id, payment_sequential)) FROM stg_payments")
    check("one_row_per_order", "SELECT COUNT(*) = COUNT(DISTINCT order_id) FROM order_model")
    check("order_count_preserved", "SELECT (SELECT COUNT(*) FROM raw_orders) = (SELECT COUNT(*) FROM order_model)")
    check("required_purchase_dates", "SELECT COUNT(*) = 0 FROM stg_orders WHERE purchase_at IS NULL")
    check("valid_item_money", "SELECT COUNT(*) = 0 FROM stg_items WHERE price IS NULL OR price < 0 OR freight_value IS NULL OR freight_value < 0")
    check("valid_payment_money", "SELECT COUNT(*) = 0 FROM stg_payments WHERE payment_value IS NULL OR payment_value < 0")
    check("item_join_coverage", "SELECT COUNT(*) = 0 FROM stg_items i ANTI JOIN stg_orders o USING(order_id)")
    check("customer_join_coverage", "SELECT COUNT(*) = 0 FROM stg_orders o ANTI JOIN stg_customers c USING(customer_id)")
    check("delivered_orders_have_items", "SELECT COUNT(*) = 0 FROM order_model WHERE is_delivered AND item_count IS NULL")
    check("merchandise_not_multiplied", "SELECT (SELECT SUM(price) FROM stg_items) = (SELECT SUM(merchandise_value) FROM order_model)")
    check("payments_not_multiplied", "SELECT (SELECT SUM(payment_value) FROM stg_payments) = (SELECT SUM(payment_value) FROM order_model)")
    check("category_sales_reconcile", "SELECT (SELECT SUM(merchandise_value) FROM categories_daily) = (SELECT SUM(merchandise_value) FROM orders_daily)")
    check("experience_orders_reconcile", "SELECT (SELECT SUM(delivered_orders) FROM experience_daily) = (SELECT SUM(delivered_orders) FROM orders_daily)")
    check("experience_reviews_reconcile", "SELECT (SELECT SUM(review_score_sum) FROM experience_daily) = (SELECT SUM(review_score_sum) FROM orders_daily)")
    check("review_histogram_reconciles", "SELECT SUM(rating_1_count+rating_2_count+rating_3_count+rating_4_count+rating_5_count) = SUM(reviewed_orders) FROM experience_daily")
    check("delivery_partition_reconciles", "SELECT SUM(on_time_orders+late_orders) = SUM(eligible_delivery_orders) FROM orders_daily")
    check("nonnegative_durations", "SELECT COUNT(*) = 0 FROM order_model WHERE delivery_days < 0")
    check("valid_review_range", "SELECT COUNT(*) = 0 FROM order_model WHERE is_reviewed AND review_score NOT BETWEEN 1 AND 5")
    check("monthly_review_unique_grain", "SELECT COUNT(*) = COUNT(DISTINCT (review_month,customer_state)) FROM monthly_review")
    check("monthly_review_sales_reconcile", "SELECT (SELECT SUM(merchandise_value) FROM monthly_review) = (SELECT SUM(merchandise_value) FROM orders_daily)")
    check("monthly_review_orders_reconcile", "SELECT (SELECT SUM(delivered_orders) FROM monthly_review) = (SELECT SUM(delivered_orders) FROM orders_daily)")
    check("monthly_review_prior_components_reconcile", "SELECT (SELECT SUM(previous_merchandise_value) FROM monthly_review) = (SELECT SUM(merchandise_value) FROM orders_daily WHERE purchase_date < DATE '2018-08-01') AND (SELECT SUM(previous_delivered_orders) FROM monthly_review) = (SELECT SUM(delivered_orders) FROM orders_daily WHERE purchase_date < DATE '2018-08-01')")
    return checks


def evidence(con):
    result = {}
    result["headline"] = records(con, """
        SELECT SUM(placed_orders) AS placed_orders, SUM(delivered_orders) AS delivered_orders,
               SUM(merchandise_value) AS merchandise_value_brl, SUM(freight_value) AS freight_brl,
               SUM(payment_value) AS payment_value_brl,
               SUM(paid_delivered_orders) AS paid_delivered_orders,
               SUM(merchandise_value)/NULLIF(SUM(delivered_orders),0) AS aov_brl,
               SUM(eligible_delivery_orders) AS eligible_delivery_orders,
               SUM(on_time_orders) AS on_time_orders, SUM(late_orders) AS late_orders,
               SUM(on_time_orders)::DOUBLE/NULLIF(SUM(eligible_delivery_orders),0) AS on_time_rate,
               SUM(delivery_days_sum)/NULLIF(SUM(eligible_delivery_orders),0) AS mean_delivery_days,
               SUM(reviewed_orders) AS reviewed_orders, SUM(review_score_sum) AS review_score_sum,
               SUM(review_score_sum)::DOUBLE/NULLIF(SUM(reviewed_orders),0) AS review_score,
               SUM(reviewed_orders)::DOUBLE/NULLIF(SUM(delivered_orders),0) AS review_coverage
        FROM orders_daily""")[0]
    result["monthly"] = records(con, """
        SELECT DATE_TRUNC('month',purchase_date)::DATE AS month,
               SUM(merchandise_value) AS merchandise_value_brl, SUM(delivered_orders) AS delivered_orders,
               SUM(on_time_orders)::DOUBLE/NULLIF(SUM(eligible_delivery_orders),0) AS on_time_rate,
               SUM(review_score_sum)::DOUBLE/NULLIF(SUM(reviewed_orders),0) AS review_score
        FROM orders_daily GROUP BY month ORDER BY month""")
    result["categories"] = records(con, """
        SELECT product_category, SUM(merchandise_value) AS merchandise_value_brl,
               SUM(delivered_items) AS delivered_items,
               SUM(merchandise_value)/SUM(SUM(merchandise_value)) OVER() AS sales_share
        FROM categories_daily GROUP BY product_category ORDER BY merchandise_value_brl DESC""")
    result["states"] = records(con, """
        SELECT customer_state, SUM(delivered_orders) AS delivered_orders,
               SUM(merchandise_value) AS merchandise_value_brl,
               SUM(eligible_delivery_orders) AS eligible_orders,
               SUM(late_orders) AS late_orders,
               SUM(on_time_orders)::DOUBLE/NULLIF(SUM(eligible_delivery_orders),0) AS on_time_rate,
               SUM(delivery_days_sum)/NULLIF(SUM(eligible_delivery_orders),0) AS mean_delivery_days,
               SUM(reviewed_orders) AS reviewed_orders,
               SUM(review_score_sum)::DOUBLE/NULLIF(SUM(reviewed_orders),0) AS review_score
        FROM orders_daily GROUP BY customer_state ORDER BY merchandise_value_brl DESC""")
    result["experience"] = records(con, """
        SELECT delivery_outcome, SUM(delivered_orders) AS delivered_orders,
               SUM(reviewed_orders) AS reviewed_orders,
               SUM(review_score_sum)::DOUBLE/NULLIF(SUM(reviewed_orders),0) AS mean_review_score,
               SUM(rating_1_count+rating_2_count)::DOUBLE/NULLIF(SUM(reviewed_orders),0) AS low_rating_share,
               SUM(rating_1_count) AS rating_1_count, SUM(rating_2_count) AS rating_2_count,
               SUM(rating_3_count) AS rating_3_count, SUM(rating_4_count) AS rating_4_count,
               SUM(rating_5_count) AS rating_5_count
        FROM experience_daily GROUP BY delivery_outcome ORDER BY delivery_outcome""")
    result["monthly_review"] = records(con, """
        SELECT review_month, SUM(merchandise_value) AS merchandise_value_brl,
               SUM(delivered_orders) AS delivered_orders,
               SUM(merchandise_value)/NULLIF(SUM(delivered_orders),0) AS aov_brl,
               CASE WHEN MIN(comparison_available)=1 THEN
                   SUM(merchandise_value)/NULLIF(SUM(previous_merchandise_value),0)-1 END AS merchandise_mom,
               CASE WHEN MIN(comparison_available)=1 THEN
                   SUM(delivered_orders)::DOUBLE/NULLIF(SUM(previous_delivered_orders),0)-1 END AS orders_mom,
               CASE WHEN MIN(comparison_available)=1 THEN
                   (SUM(merchandise_value)/NULLIF(SUM(delivered_orders),0)) /
                   NULLIF(SUM(previous_merchandise_value)/NULLIF(SUM(previous_delivered_orders),0),0)-1 END AS aov_mom,
               MIN(comparison_available) AS comparison_available
        FROM monthly_review GROUP BY review_month ORDER BY review_month""")
    return result


def build(work_dir: Path, export_xlsx: bool = False):
    work_dir = work_dir.resolve()
    data_dir, output_dir = work_dir / "data", work_dir / "build"
    output_dir.mkdir(parents=True, exist_ok=True)
    missing = [name for name in FILES.values() if not (data_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing CSVs in {data_dir}: {', '.join(missing)}. Run the fetch command first.")
    # Replace the local database so repeated builds never append observations.
    con = duckdb.connect(str(work_dir / "olist.duckdb"))
    for table, filename in FILES.items():
        con.execute(f"CREATE OR REPLACE TABLE raw_{table} AS SELECT * FROM read_csv(?, all_varchar=true)",
                    [str(data_dir / filename)])
    run_models(con)
    checks = validate(con)
    audit = {
        "source_rows": {table: con.execute(f"SELECT COUNT(*) FROM raw_{table}").fetchone()[0] for table in FILES},
        "source_purchase_coverage": records(con, "SELECT MIN(purchase_at) AS first_purchase, MAX(purchase_at) AS last_purchase FROM stg_orders")[0],
        "report_orders": con.execute("SELECT COUNT(*) FROM report_orders").fetchone()[0],
        "multiple_review_orders": con.execute("SELECT COUNT(*) FROM (SELECT order_id FROM stg_reviews GROUP BY order_id HAVING COUNT(*)>1)").fetchone()[0],
        "superseded_reviews": con.execute("SELECT COUNT(*)-COUNT(DISTINCT order_id) FROM stg_reviews").fetchone()[0],
        "invalid_review_scores": con.execute("SELECT COUNT(*) FROM stg_reviews WHERE review_score IS NULL OR review_score NOT BETWEEN 1 AND 5").fetchone()[0],
        "delivered_excluded_from_delivery": con.execute("SELECT COUNT(*) FROM report_orders WHERE is_delivered AND NOT valid_delivery").fetchone()[0],
        "delivered_without_review": con.execute("SELECT COUNT(*) FROM report_orders WHERE is_delivered AND NOT is_reviewed").fetchone()[0],
        "unknown_category_items": con.execute("SELECT COUNT(*) FROM report_items WHERE product_category='Unknown'").fetchone()[0],
        "checks": checks,
    }
    result = evidence(con)
    workbook = {}
    hashes = {}
    for table in MARTS:
        cursor = con.execute(f"SELECT * FROM {table} ORDER BY ALL")
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        workbook[table] = {"columns": columns, "rows": rows}
        target = output_dir / f"{table}.csv"
        con.execute(f"COPY (SELECT * FROM {table} ORDER BY ALL) TO ? (HEADER, DELIMITER ',')", [str(target)])
        hashes[table] = hashlib.sha256(target.read_bytes()).hexdigest()
    notes = [
        ["Source", SOURCE_URL], ["Reporting window", "2017-01-01 through 2018-08-31, by purchase date"],
        ["Currency", "BRL. Merchandise value excludes freight and is not marketplace commission revenue."],
        ["Status", "Historical source snapshot. Delivered-only monetary metrics use final observed status."],
        ["On-time delivery", "Received by estimated calendar date; requires valid purchase, receipt and estimated dates."],
        ["Average delivery days", "Elapsed seconds from purchase to receipt divided by 86400, among valid delivered orders."],
        ["Reviews", "One latest review per order; only scores 1 to 5 on delivered orders. Display review coverage."],
        ["Review association", "Delivery outcomes and review scores are associated; the comparison is not causal."],
        ["Small groups", "Rank only groups with at least 30 eligible delivery orders or 30 reviewed orders."],
        ["Monthly review", "Separate calendar-month selector; state filtering applies. Changes use summed current/prior month components. January has no prior reporting month; zero or unavailable baselines stay unavailable."],
        ["Delivery exclusions", str(audit["delivered_excluded_from_delivery"])],
        ["Unreviewed delivered orders", str(audit["delivered_without_review"])],
        ["Unknown-category item rows", str(audit["unknown_category_items"])],
        ["Last successful publication", "Pending native Google Sheets import and readback"],
    ]
    workbook["data_notes"] = {"columns": ["topic", "detail"], "rows": notes}
    write_json(output_dir / "workbook-data.json", workbook)
    write_json(output_dir / "evidence.json", result)
    write_json(output_dir / "data-quality.json", audit)
    manifest = {
        "source_url": SOURCE_URL, "report_start": "2017-01-01", "report_end": "2018-08-31",
        "built_at": datetime.now(timezone.utc).isoformat(),
        "input_sha256": {f: hashlib.sha256((data_dir/f).read_bytes()).hexdigest() for f in FILES.values()},
        "mart_sha256": hashes,
        "mart_rows": {table: len(workbook[table]["rows"]) for table in MARTS},
        "checks_passed": len(checks),
    }
    write_json(output_dir / "build-manifest.json", manifest)
    con.close()
    if export_xlsx:
        node = os.environ.get("ARTIFACT_NODE") or shutil.which("node")
        if not node:
            raise RuntimeError("XLSX packaging requires the Artifact Tool Node runtime. Set ARTIFACT_NODE to its executable.")
        subprocess.run([node, "--max-old-space-size=4096", str(ROOT / "scripts" / "export_workbook.mjs"),
                        str(output_dir)], check=True)
    print(json.dumps({"build_dir": str(output_dir), "checks_passed": len(checks), "mart_rows": manifest["mart_rows"]}))


def fetch(work_dir: Path):
    work_dir.mkdir(parents=True, exist_ok=True)
    archive = work_dir / "olist.zip"
    if not archive.exists():
        print("Downloading the official public Olist archive...")
        urlretrieve(DOWNLOAD_URL, archive)
    data_dir = work_dir / "data"
    data_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        for filename in FILES.values():
            # Extract only the known CSV members, never arbitrary archive paths.
            (data_dir / filename).write_bytes(bundle.read(filename))
    print(f"Extracted {len(FILES)} source CSVs into {data_dir}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["fetch", "build"])
    parser.add_argument("--work-dir", type=Path, required=True,
                        help="Private working directory outside this repository")
    parser.add_argument("--xlsx", action="store_true", help="Also package the publishing workbook using the Artifact Tool runtime")
    args = parser.parse_args()
    if args.command == "fetch":
        fetch(args.work_dir)
    else:
        build(args.work_dir, export_xlsx=args.xlsx)


if __name__ == "__main__":
    main()
