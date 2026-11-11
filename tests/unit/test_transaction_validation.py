import polars as pl
import pytest

from ecommerce_pipeline.validation.transactions import (
    validate_transaction_input,
    validate_transaction_output,
)
from tests.factories import INPUT_SCHEMA, make_input_lf, make_output_lf


def run(validator, lf: pl.LazyFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    valid, rejected = validator(lf)

    valid_df, rejected_df = pl.collect_all([valid, rejected])

    return valid_df, rejected_df


def test_input_valid_row_passes():
    valid_df, rejected_df = run(
        validate_transaction_input,
        make_input_lf(),
    )

    assert valid_df.height == 1
    assert rejected_df.height == 0


@pytest.mark.parametrize(
    "samples",
    [
        pytest.param({"InvoiceNo": ""}, id="missing_invoice_no"),
        pytest.param({"InvoiceNo": None}, id="missing_invoice_no"),
        pytest.param({"StockCode": "  "}, id="missing_stock_code"),
        pytest.param({"StockCode": ""}, id="missing_stock_code"),
        pytest.param({"Country": "\n\t"}, id="missing_country"),
        pytest.param({"Country": None}, id="missing_country"),
    ],
)
def test_input_invalid_row_is_rejected(samples):
    valid_df, rejected_df = run(validate_transaction_input, make_input_lf(samples))

    assert valid_df.height == 0
    assert rejected_df.height == 1


@pytest.mark.parametrize(
    "samples",
    [
        pytest.param({"CustomerID": None}, id="missing_customer_id"),
        pytest.param({"Description": None}, id="missing_description"),
    ],
)
def test_input_optional_fields_may_be_null(samples):
    valid_df, rejected_df = run(validate_transaction_input, make_input_lf(samples))

    assert valid_df.height == 1
    assert rejected_df.height == 0


def test_input_mixed_batch_is_split_correctly():
    valid_df, rejected_df = run(
        validate_transaction_input,
        make_input_lf(
            {},
            {"InvoiceNo": ""},
            {"CustomerID": None},
            {"StockCode": None},
        ),
    )

    assert valid_df.height == 2
    assert rejected_df.height == 2


def test_input_empty_frame():
    valid_df, rejected_df = run(
        validate_transaction_input, pl.LazyFrame(schema=INPUT_SCHEMA)
    )

    assert valid_df.height == 0
    assert rejected_df.height == 0


def test_output_valid_row_passes():
    valid_df, rejected_df = run(
        validate_transaction_output,
        make_output_lf(),
    )

    assert valid_df.height == 1
    assert rejected_df.height == 0


@pytest.mark.parametrize(
    "samples",
    [
        pytest.param({"unit_price": -69.67}, id="negative_unit_price"),
        pytest.param({"quantity": 0}, id="zero_quantity"),
        pytest.param({"unit_price": None}, id="missing_unit_price"),
    ],
)
def test_output_invalid_row_is_rejected(samples):
    valid_df, rejected_df = run(validate_transaction_output, make_output_lf(samples))

    assert valid_df.height == 0
    assert rejected_df.height == 1


def test_output_mixed_batch_is_split_correctly():
    valid_df, rejected_df = run(
        validate_transaction_output,
        make_output_lf({}, {"unit_price": -69.69}, {}, {"unit_price": -67.67}),
    )

    assert valid_df.height == 2
    assert rejected_df.height == 2


def test_input_valid_plus_rejected_equals_total():
    valid, rejected = run(
        validate_transaction_input,
        make_input_lf({}, {"InvoiceNo": ""}, {}, {"StockCode": None}, {}),
    )

    assert valid.height + rejected.height == 5


def test_output_valid_plus_rejected_equals_total():
    valid, rejected = run(
        validate_transaction_output, make_output_lf({}, {"unit_price": -1.0}, {})
    )

    assert valid.height + rejected.height == 3
