import psycopg
import polars as pl

from ecommerce_pipeline.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


def connect_postgres() -> psycopg.Connection:
    return psycopg.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def load_transactions(rows: pl.DataFrame) -> int:
    records = rows.select(["description", "quantity", "unit_price"]).iter_rows()

    with connect_postgres() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO transactions
                    (description, quantity, unit_price)
                VALUES 
                    (%s, %s, %s)
                """,
                records,
            )

            return cursor.rowcount
