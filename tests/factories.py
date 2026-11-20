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


HEADER = "InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country\n"

ROWS = (
    # Product lines
    "536365,85123A,WHITE HANGING HEART,6,12/1/2010 8:26,2.55,17850,United Kingdom\n"
    "536365,71053,WHITE METAL LANTERN,6,12/1/2010 8:26,3.39,17850,United Kingdom\n"
    "536366,22633,HAND WARMER,2,12/1/2010 8:28,1.85,13047,France\n"
    "536367,84406B,CREAM CUPID HEARTS,3,12/1/2010 8:34,4.00,,United Kingdom\n"
    "536370,22728,ALARM CLOCK BAKELIKE,4,12/2/2010 9:00,2.50,17850,United Kingdom\n"
    "C536379,22423,REGENCY CAKESTAND 3 TIER,-1,12/2/2010 9:41,10.00,13047,France\n"
    "537000,22086,PAPER CHAIN KIT,5,1/5/2011 10:00,3.00,12583,France\n"
    # Non-product lines
    "536371,POST,POSTAGE,1,12/1/2010 9:00,15.00,17850,United Kingdom\n"
    "536372,M,Manual,1,12/1/2010 9:30,99.99,99999,Germany\n"
    "C536380,D,Discount,-1,12/2/2010 10:00,5.00,13047,France\n"
    # Bad rows
    "C536379,22423,REGENCY CAKESTAND 3 TIER,-1,12/2/2010 9:41,-6767.00,13047,France\n"
    "537000,22086,PAPER CHAIN KIT,5,1/5/2011 10:00,12abc.00,12583,France\n"
    # Stock adjustments
    "536373,21319,adjustment,3,12/1/2010 9:45,0,,United Kingdom\n"
    "536374,22501,reverse adjustment,-100,12/2/2010 10:30,0,,United Kingdom\n"
)


def make_input_lf(*samples: dict) -> pl.LazyFrame:
    rows = [{**INPUT_SAMPLE, **sample} for sample in (samples or ({},))]

    return pl.LazyFrame(list(rows) or {}, schema=INPUT_SCHEMA)


def make_output_lf(*samples: dict) -> pl.LazyFrame:
    rows = [{**OUTPUT_SAMPLE, **sample} for sample in (samples or ({},))]

    return pl.LazyFrame(list(rows) or {}, schema=OUTPUT_SCHEMA)
