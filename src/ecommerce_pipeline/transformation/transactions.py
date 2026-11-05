import polars as pl

COLUMN_MAPPING = {
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
        lf.rename(COLUMN_MAPPING)
        .with_columns(pl.col(pl.String).str.strip_chars())
        .with_columns(
            pl.col("invoice_date").str.to_datetime("%m/%d/%Y %H:%M", strict=False),
            pl.col("quantity").cast(pl.Int32, strict=False),
            pl.col("unit_price").cast(pl.Decimal(12, 4), strict=False),
        )
        .with_columns(pl.col(pl.String).replace("", None))
    )
