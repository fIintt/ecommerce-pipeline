from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from psycopg import sql

from ecommerce_pipeline.pipelines.transactions import run_transaction_pipeline

HEADER = "InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country\n"

ROWS = (
    "536365,85123A,WHITE HANGING HEART,6,12/1/2010 8:26,2.55,17850,United Kingdom\n"
    "536365,71053,WHITE METAL LANTERN,6,12/1/2010 8:26,3.39,17850,United Kingdom\n"
    "536366,22633,HAND WARMER,2,12/1/2010 8:28,1.85,13047,France\n"
    "536367,84406B,CREAM CUPID HEARTS,3,12/1/2010 8:34,4.00,,United Kingdom\n"
    "536370,22728,ALARM CLOCK BAKELIKE,4,12/2/2010 9:00,2.50,17850,United Kingdom\n"
    "C536379,22423,REGENCY CAKESTAND 3 TIER,-1,12/2/2010 9:41,10.00,13047,France\n"
    "537000,22086,PAPER CHAIN KIT,5,1/5/2011 10:00,3.00,12583,France\n"
)


@pytest.fixture
def loaded(conn, tmp_path: Path):
    csv = tmp_path / "transactions.csv"
    csv.write_text(HEADER + ROWS, encoding="cp1252")

    result = run_transaction_pipeline(conn, csv)

    assert result.loaded == 7

    return conn


def test_every_view_is_queryable_with_data(loaded):
    names = [
        row[0]
        for row in loaded.execute(
            "SELECT table_name FROM information_schema.views "
            "WHERE table_schema = 'public' ORDER BY 1"
        ).fetchall()
    ]

    assert names, "no views found; was the view directory loaded?"

    for name in names:
        loaded.execute(
            sql.SQL("SELECT * FROM {}").format(sql.Identifier(name))
        ).fetchall()


def test_cancellations(loaded):
    rows = loaded.execute(
        "SELECT invoice_no, cancel_date, customer_id, country, stock_code, "
        "description, quantity_returned, value_returned FROM cancellations"
    ).fetchall()

    assert rows == [
        (
            "C536379",
            date(2010, 12, 2),
            13047,
            "France",
            "22423",
            "REGENCY CAKESTAND 3 TIER",
            1,
            Decimal("10.00"),
        )
    ]


def test_daily_revenue(loaded):
    rows = loaded.execute(
        "SELECT revenue_date, revenue, customer_count, order_count, units_sold "
        "FROM daily_revenue ORDER BY revenue_date"
    ).fetchall()

    assert rows == [
        (date(2010, 12, 1), Decimal("51.34"), 2, 3, 17),
        (date(2010, 12, 2), Decimal("10.00"), 1, 1, 4),
        (date(2011, 1, 5), Decimal("15.00"), 1, 1, 5),
    ]


def test_monthly_revenue(loaded):
    rows = loaded.execute(
        "SELECT revenue_month, revenue, customer_count, order_count, units_sold "
        "FROM monthly_revenue ORDER BY revenue_month"
    ).fetchall()

    assert rows == [
        (date(2010, 12, 1), Decimal("61.34"), 2, 4, 21),
        (date(2011, 1, 1), Decimal("15.00"), 1, 1, 5),
    ]


def test_revenue_by_country(loaded):
    rows = loaded.execute(
        "SELECT country, revenue, customer_count, order_count, units_sold, "
        "revenue_share_pct FROM revenue_by_country ORDER BY country"
    ).fetchall()

    assert rows == [
        ("France", Decimal("18.70"), 2, 2, 7, Decimal("24.50")),
        ("United Kingdom", Decimal("57.64"), 1, 3, 19, Decimal("75.50")),
    ]


def test_rfm(loaded):
    rows = loaded.execute(
        "SELECT customer_id, r_score, f_score, m_score FROM rfm"
    ).fetchall()
    scores = {cid: (r, f, m) for cid, r, f, m in rows}

    assert set(scores) == {12583, 13047, 17850}

    assert scores[13047][0] == 1
    assert scores[17850][0] == 2
    assert scores[12583][0] == 3

    assert scores[13047][2] == 1
    assert scores[12583][2] == 2
    assert scores[17850][2] == 3

    assert scores[17850][1] == 3
    assert {scores[13047][1], scores[12583][1]} == {1, 2}
