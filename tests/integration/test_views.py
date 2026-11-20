from datetime import date
from decimal import Decimal

from psycopg import sql


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


def test_non_product_summary(loaded):
    rows = loaded.execute(
        "SELECT stock_code, typical_description, line_count, net_value "
        "FROM non_product_summary ORDER BY stock_code"
    ).fetchall()

    assert rows == [
        ("D", "Discount", 1, Decimal("-5.00")),
        ("M", "Manual", 1, Decimal("99.99")),
        ("POST", "POSTAGE", 1, Decimal("15.00")),
    ]


def test_stock_adjustments(loaded):
    rows = loaded.execute(
        "SELECT reason, count, units_added, units_removed "
        "FROM stock_adjustments ORDER BY reason"
    ).fetchall()

    assert rows == [
        ("ADJUSTMENT", 1, 3, 0),
        ("REVERSE ADJUSTMENT", 1, 0, -100),
    ]
