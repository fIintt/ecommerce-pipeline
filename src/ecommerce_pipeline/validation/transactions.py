import polars as pl

from ecommerce_pipeline.validation.validator import (
    is_blank,
    validate_input,
    validate_output,
)

_REQUIRED_TRANSACTION_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "Country",
]


_TRANSACTION_INPUT_RULES: dict[str, pl.Expr] = {
    "missing_invoice_no": is_blank("InvoiceNo"),
    "missing_stock_code": is_blank("StockCode"),
    "missing_country": is_blank("Country"),
    "missing_unit_price": is_blank("UnitPrice"),
    "missing_quantity": is_blank("Quantity"),
    "missing_invoice_date": is_blank("InvoiceDate"),
}

_TRANSACTION_OUTPUT_RULES: dict[str, pl.Expr] = {
    "negative_unit_price": pl.col("unit_price") < 0,
    "unparseable_unit_price": pl.col("unit_price").is_null(),
    "zero_quantity": pl.col("quantity") == 0,
    "unparseable_quantity": pl.col("quantity").is_null(),
    "unparseable_invoice_date": pl.col("invoice_date").is_null(),
}


def validate_transaction_input(lf: pl.LazyFrame) -> tuple[pl.LazyFrame, pl.LazyFrame]:
    return validate_input(lf, _REQUIRED_TRANSACTION_COLUMNS, _TRANSACTION_INPUT_RULES)


def validate_transaction_output(lf: pl.LazyFrame) -> tuple[pl.LazyFrame, pl.LazyFrame]:
    return validate_output(lf, _TRANSACTION_OUTPUT_RULES)
