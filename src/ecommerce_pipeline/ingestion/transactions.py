import polars as pl


def extract_transactions(path: str) -> pl.DataFrame:
    return (
        pl.scan_csv(path, infer_schema=False)
        .rename(lambda name: name.strip())
        .cast(
            {
                "InvoiceNo": pl.String,
                "StockCode": pl.String,
                "Description": pl.String,
                "Quantity": pl.Int32,
                "InvoiceDate": pl.String,
                "UnitPrice": pl.Float32,
                "CustomerID": pl.String,
                "Country": pl.String,
            }
        )
        .collect()
    )
