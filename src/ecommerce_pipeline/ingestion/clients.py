import polars as pl


def extract_transactions(path: str) -> pl.DataFrame:
    return (
        pl.scan_csv(
            path,
            schema_overrides={
                "InvoiceNo": pl.String,
                "StockCode": pl.String,
                "Description": pl.String,
                "Quantity": pl.Int32,
                "InvoiceDate": pl.String,
                "UnitPrice": pl.Float32,
                "CustomerID": pl.String,
                "Country": pl.String,
            },
        )
        .with_columns(
            pl.col("InvoiceDate").str.to_datetime("%m/%d/%Y %H:%M"),
        )
        .collect()
    )
