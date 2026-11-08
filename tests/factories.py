from datetime import datetime
from decimal import Decimal

import polars as pl

INPUT_SCHEMA = {
    "InvoiceNo": pl.String,
    "StockCode": pl.String,
    "Description": pl.String,
    "Quantity": pl.String,
    "InvoiceDate": pl.String,
    "UnitPrice": pl.String,
    "CustomerID": pl.String,
    "Country": pl.String,
}

OUTPUT_SCHEMA = {
    "invoice_no": pl.String,
    "stock_code": pl.String,
    "description": pl.String,
    "quantity": pl.Int32,
    "invoice_date": pl.Datetime,
    "unit_price": pl.Decimal(12, 4),
    "customer_id": pl.Int32,
    "country": pl.String,
}

INPUT_SAMPLE = {
    "InvoiceNo": "536365",
    "StockCode": "85123A",
    "Description": "WHITE HANGING HEART T-LIGHT HOLDER",
    "Quantity": "6",
    "InvoiceDate": "12/1/2010 8:26",
    "UnitPrice": "2.55",
    "CustomerID": "17850",
    "Country": "United Kingdom",
}

OUTPUT_SAMPLE = {
    "invoice_no": "536365",
    "stock_code": "85123A",
    "description": "WHITE HANGING HEART T-LIGHT HOLDER",
    "quantity": 6,
    "invoice_date": datetime(2010, 12, 1, 8, 26),
    "unit_price": Decimal("2.55"),
    "customer_id": 17850,
    "country": "United Kingdom",
}


def make_input_lf(*samples: dict) -> pl.LazyFrame:
    rows = [{**INPUT_SAMPLE, **sample} for sample in (samples or ({},))]

    return pl.LazyFrame(list(rows) or {}, schema=INPUT_SCHEMA)


def make_output_lf(*samples: dict) -> pl.LazyFrame:
    rows = [{**OUTPUT_SAMPLE, **sample} for sample in (samples or ({},))]

    return pl.LazyFrame(list(rows) or {}, schema=OUTPUT_SCHEMA)