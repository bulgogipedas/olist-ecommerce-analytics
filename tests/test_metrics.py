"""Regression tests for concrete join, denominator and date-boundary risks."""

import duckdb
import pytest

from olist_pipeline import run_models, validate


@pytest.fixture
def con():
    db = duckdb.connect()
    db.execute("""
        CREATE TABLE raw_orders(order_id VARCHAR,customer_id VARCHAR,order_status VARCHAR,
          order_purchase_timestamp VARCHAR,order_delivered_customer_date VARCHAR,order_estimated_delivery_date VARCHAR);
        INSERT INTO raw_orders VALUES
          ('a','c','delivered','2018-01-01 12:00:00','2018-01-05 15:00:00','2018-01-05 00:00:00'),
          ('b','c','delivered','2018-01-01 12:00:00',NULL,'2018-01-05'),
          ('c','c','delivered','2018-01-01 12:00:00','2018-01-09','2018-01-05'),
          ('d','c','canceled','2018-01-01',NULL,'2018-01-05');
        CREATE TABLE raw_customers(customer_id VARCHAR,customer_state VARCHAR);
        INSERT INTO raw_customers VALUES ('c','SP');
        CREATE TABLE raw_items(order_id VARCHAR,order_item_id VARCHAR,product_id VARCHAR,seller_id VARCHAR,price VARCHAR,freight_value VARCHAR);
        INSERT INTO raw_items VALUES ('a','1','p','s','100.00','10.00'),('a','2','p','s','50.00','5.00'),
          ('b','1','p','s','20.00','2.00'),('c','1','p','s','30.00','3.00');
        CREATE TABLE raw_products(product_id VARCHAR,product_category_name VARCHAR);
        INSERT INTO raw_products VALUES ('p',NULL);
        CREATE TABLE raw_translations(product_category_name VARCHAR,product_category_name_english VARCHAR);
        INSERT INTO raw_translations VALUES ('casa','home');
        CREATE TABLE raw_payments(order_id VARCHAR,payment_sequential VARCHAR,payment_value VARCHAR);
        INSERT INTO raw_payments VALUES ('a','1','100.00'),('a','2','65.00'),('b','1','22.00'),('c','1','33.00');
        CREATE TABLE raw_reviews(review_id VARCHAR,order_id VARCHAR,review_score VARCHAR,review_creation_date VARCHAR,review_answer_timestamp VARCHAR);
        INSERT INTO raw_reviews VALUES ('r1','a','1','2018-01-06','2018-01-06'),
          ('r2','a','5','2018-01-07','2018-01-08'),('r3','c','2','2018-01-10','2018-01-10');
    """)
    run_models(db)
    yield db
    db.close()


def test_many_side_joins_preserve_money_and_order_count(con):
    assert con.execute("SELECT COUNT(*),SUM(merchandise_value),SUM(payment_value) FROM order_model").fetchone() == (4, 200, 220)
    assert all(validate(con).values())


def test_estimated_calendar_date_includes_same_day_afternoon(con):
    assert con.execute("SELECT delivery_outcome FROM order_model WHERE order_id='a'").fetchone()[0] == 'On time'


def test_missing_delivery_date_only_excludes_delivery_metrics(con):
    assert con.execute("SELECT is_delivered,valid_delivery,merchandise_value,delivery_outcome FROM order_model WHERE order_id='b'").fetchone() == (True, False, 20, 'Unknown')
    assert con.execute("SELECT SUM(delivered_orders),SUM(eligible_delivery_orders) FROM orders_daily").fetchone() == (3, 2)


def test_latest_review_and_missing_review_denominator(con):
    assert con.execute("SELECT review_score FROM order_model WHERE order_id='a'").fetchone()[0] == 5
    assert con.execute("SELECT SUM(review_score_sum),SUM(reviewed_orders) FROM orders_daily").fetchone() == (7, 2)


def test_unknown_category_is_retained(con):
    assert con.execute("SELECT DISTINCT product_category FROM categories_daily").fetchall() == [('Unknown',)]


def test_zero_denominator_stays_unavailable(con):
    assert con.execute("SELECT SUM(review_score_sum)/NULLIF(SUM(reviewed_orders),0) FROM orders_daily WHERE customer_state='ZZ'").fetchone()[0] is None


def test_rebuilding_does_not_append_or_change_results(con):
    before = con.execute("SELECT * FROM orders_daily ORDER BY ALL").fetchall()
    run_models(con)
    assert con.execute("SELECT * FROM orders_daily ORDER BY ALL").fetchall() == before


def test_negative_delivery_interval_is_excluded(con):
    con.execute("UPDATE raw_orders SET order_delivered_customer_date='2017-12-31' WHERE order_id='a'")
    run_models(con)
    assert con.execute("SELECT valid_delivery,delivery_days FROM order_model WHERE order_id='a'").fetchone() == (False, None)


def test_monthly_review_retains_prior_orders_for_a_state_with_no_current_orders(con):
    con.execute("""
        INSERT INTO raw_customers VALUES ('rj','RJ');
        UPDATE raw_orders SET customer_id='rj' WHERE order_id='b';
        INSERT INTO raw_orders VALUES
          ('e','c','delivered','2018-02-01','2018-02-05','2018-02-06'),
          ('before','c','canceled','2016-12-31',NULL,NULL),
          ('after','c','canceled','2018-09-01',NULL,NULL);
        INSERT INTO raw_items VALUES ('e','1','p','s','40.00','4.00');
    """)
    run_models(con)
    assert con.execute("SELECT merchandise_value,delivered_orders,previous_merchandise_value,previous_delivered_orders,comparison_available FROM monthly_review WHERE review_month='2018-02' AND customer_state='RJ'").fetchone() == (0, 0, 20, 1, 1)
    assert con.execute("SELECT SUM(merchandise_value),SUM(delivered_orders),SUM(previous_merchandise_value),SUM(previous_delivered_orders) FROM monthly_review WHERE review_month='2018-02'").fetchone() == (40, 1, 200, 3)


def test_monthly_comparison_requires_covered_prior_calendar_month(con):
    assert con.execute("SELECT MAX(comparison_available) FROM monthly_review").fetchone()[0] == 0
    con.execute("INSERT INTO raw_orders VALUES ('before','c','canceled','2016-12-31',NULL,NULL),('after','c','canceled','2018-09-01',NULL,NULL)")
    run_models(con)
    assert con.execute("SELECT MIN(comparison_available),MAX(comparison_available) FROM monthly_review WHERE review_month='2017-01'").fetchone() == (0, 0)
    assert con.execute("SELECT MIN(comparison_available),MAX(comparison_available) FROM monthly_review WHERE review_month='2018-02'").fetchone() == (1, 1)


def test_monthly_aov_change_does_not_invent_values_for_zero_order_months(con):
    assert con.execute("SELECT (SUM(merchandise_value)/NULLIF(SUM(delivered_orders),0)) / NULLIF(SUM(previous_merchandise_value)/NULLIF(SUM(previous_delivered_orders),0),0)-1 FROM monthly_review WHERE review_month='2018-02'").fetchone()[0] is None
