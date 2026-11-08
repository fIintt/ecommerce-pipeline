import polars as pl

_TRANSACTION_COLUMN_MAPPING = {
    "InvoiceNo": "invoice_no",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "UnitPrice": "unit_price",
    "CustomerID": "customer_id",
    "Country": "country",
}


def transform_transactions(lf: pl.LazyFrame) -> pl.LazyFrame:
    return (
        lf.rename(_TRANSACTION_COLUMN_MAPPING)
        .with_columns(pl.col(pl.String).str.replace_all(r"\s+", " ").str.strip_chars())
        .with_columns(
            pl.col("quantity").cast(pl.Int32, strict=False),
            pl.col("invoice_date").str.to_datetime("%m/%d/%Y %H:%M", strict=False),
            pl.col("unit_price").cast(pl.Decimal(12, 4), strict=False),
            pl.col("customer_id").cast(pl.Int32, strict=False),
        )
        .with_columns(pl.col(pl.String).replace("", None))
    )
