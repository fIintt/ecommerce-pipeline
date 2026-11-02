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
    "missing_quantity": pl.col("Quantity").is_null(),
    "missing_invoice_date": pl.col("InvoiceDate").is_null(),
    "missing_unit_price": pl.col("UnitPrice").is_null(),
    "missing_country": is_blank("Country"),
}

_TRANSACTION_OUTPUT_RULES: dict[str, pl.Expr] = {
    "negative_unit_price": pl.col("unit_price") < 0,
}


def validate_transaction_input(lf: pl.LazyFrame) -> tuple[pl.LazyFrame, pl.LazyFrame]:
    return validate_input(lf, _REQUIRED_TRANSACTION_COLUMNS, _TRANSACTION_INPUT_RULES)


def validate_transaction_output(lf: pl.LazyFrame) -> tuple[pl.LazyFrame, pl.LazyFrame]:
    return validate_output(lf, _TRANSACTION_OUTPUT_RULES)
