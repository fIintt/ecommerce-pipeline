import polars as pl

REQUIRED_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "Country",
]


def _blank(col: str) -> pl.Expr:
    return pl.col(col).is_null() | (pl.col(col).str.strip_chars() == "")


RULES: dict[str, pl.Expr] = {
    "missing_invoice_no": _blank("InvoiceNo"),
    "missing_stock_code": _blank("StockCode"),
    "missing_quantity": pl.col("Quantity").is_null(),
    "missing_invoice_date": pl.col("InvoiceDate").is_null(),
    "missing_unit_price": pl.col("UnitPrice").is_null(),
    "negative_unit_price": pl.col("UnitPrice") < 0,
    "missing_country": _blank("Country"),
}


def validate_transactions(lf: pl.LazyFrame) -> tuple[pl.LazyFrame, pl.LazyFrame]:
    missing = [
        col for col in REQUIRED_COLUMNS if col not in lf.collect_schema().names()
    ]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    flagged = lf.with_columns(
        pl.concat_str(
            [
                pl.when(expr.fill_null(False)).then(pl.lit(name))
                for name, expr in RULES.items()
            ],
            separator=";",
            ignore_nulls=True,
        ).alias("reject_reason")
    )

    validated = flagged.filter(pl.col("reject_reason") == "").drop("reject_reason")
    rejected = flagged.filter(pl.col("reject_reason") != "")

    return validated, rejected
