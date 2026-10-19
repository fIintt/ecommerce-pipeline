import polars as pl


def validate_transactions(df: pl.DataFrame) -> pl.DataFrame:
    required_columns = [
        "InvoiceNo",
        "StockCode",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "Country",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    validated = df.filter(
        pl.col("InvoiceNo").is_not_null()
        & (pl.col("InvoiceNo").str.strip_chars() != "")
        & pl.col("StockCode").is_not_null()
        & (pl.col("StockCode").str.strip_chars() != "")
        & pl.col("Quantity").is_not_null()
        & (pl.col("Quantity") > 0)
        & pl.col("InvoiceDate").is_not_null()
        & pl.col("UnitPrice").is_not_null()
        & (pl.col("UnitPrice") > 0)
        & pl.col("Country").is_not_null()
        & (pl.col("Country").str.strip_chars() != "")
    )

    return validated
