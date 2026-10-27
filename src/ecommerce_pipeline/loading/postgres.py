import psycopg
import polars as pl

from ecommerce_pipeline.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


def connect_postgres() -> psycopg.Connection:
    return psycopg.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def load_transactions(rows: pl.DataFrame) -> int:
    records = rows.select(
        [
            "source_file_hash",
            "source_row_number",
            "invoice_no",
            "stock_code",
            "description",
            "quantity",
            "invoice_date",
            "unit_price",
            "customer_id",
            "country",
        ]
    ).iter_rows()

    with connect_postgres() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO transactions (
                    source_file_hash,
                    source_row_number,
                    invoice_no,
                    stock_code,
                    description,
                    quantity,
                    invoice_date,
                    unit_price,
                    customer_id,
                    country
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT ON CONSTRAINT uq_transactions_source_record
                DO NOTHING
                """,
                records,
            )

            return cursor.rowcount
