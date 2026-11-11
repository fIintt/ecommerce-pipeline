from datetime import datetime
from decimal import Decimal

import polars as pl


from ecommerce_pipeline.transformation.transactions import (
    transform_transactions,
)
from tests.factories import OUTPUT_SCHEMA, make_input_lf


def run(lf: pl.LazyFrame) -> pl.DataFrame:
    return transform_transactions(lf).collect()


def test_columns_are_renamed():
    df = run(make_input_lf())

    assert set(df.columns) == set(OUTPUT_SCHEMA.keys())


def test_dtypes_are_converted():
    df = run(make_input_lf())

    assert df.schema["quantity"] == pl.Int32
    assert df.schema["invoice_date"] == pl.Datetime
    assert df.schema["unit_price"] == pl.Decimal(12, 4)
    assert df.schema["customer_id"] == pl.Int32


def test_date_is_parsed():
    df = run(make_input_lf())

    assert df["invoice_date"][0] == datetime(2010, 12, 1, 8, 26)


def test_price_value_survives_conversion():
    df = run(make_input_lf())

    assert df["unit_price"][0] == Decimal("2.55")


def test_strings_are_stripped():
    df = run(
        make_input_lf(
            {
                "Description": "   WHITE HANGING   HEART T-LIGHT HOLDER    ",
                "Country": "  \n United Kingdom  ",
            }
        )
    )

    assert df["description"][0] == "WHITE HANGING HEART T-LIGHT HOLDER"
    assert df["country"][0] == "United Kingdom"


def test_empty_and_whitespace_strings_become_null():
    df = run(make_input_lf({"Description": "", "Country": "   "}))

    assert df["description"][0] is None
    assert df["country"][0] is None


def test_unparseable_date_becomes_null():
    df = run(make_input_lf({"InvoiceDate": "not a date"}))

    assert df["invoice_date"][0] is None


def test_non_numeric_quantity_becomes_null():
    df = run(make_input_lf({"Quantity": "abc"}))

    assert df["quantity"][0] is None


def test_row_count_is_unchanged():
    df = run(make_input_lf({}, {"UnitPrice": "-67.76"}, {"Description": None}))

    assert df.height == 3
