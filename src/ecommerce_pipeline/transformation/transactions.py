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


def transform_transactions(df: pl.DataFrame) -> pl.DataFrame:
    return df.rename(COLUMN_MAPPING).with_columns(
        pl.col("invoice_date").str.to_datetime("%m/%d/%Y %H:%M"),
    )
