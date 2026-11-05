from typing import LiteralString, cast

import psycopg
import polars as pl

from ecommerce_pipeline.config import (
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    SCHEMA_DIR,
)


def connect_postgres() -> psycopg.Connection:
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10,
        options="-c lock_timeout=10000",  # millisecond
    )


def create_schemas(conn: psycopg.Connection) -> None:
    for file in sorted(SCHEMA_DIR.glob("*.sql")):
        conn.execute(cast(LiteralString, file.read_text(encoding="utf-8")))


def load_loaded_files(
    conn: psycopg.Connection, file_hash: str, file_name: str, row_count: int
) -> int | None:
    row = conn.execute(
        """
        INSERT INTO loaded_files (file_hash, file_name, row_count)
        VALUES (%s, %s, %s)
        ON CONFLICT (file_hash) DO NOTHING
        RETURNING id
        """,
        (file_hash, file_name, row_count)
    ).fetchone()

    return row[0] if row else None


def load_transactions(conn: psycopg.Connection, rows: pl.DataFrame) -> int:
    records = rows.select(
        [
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

    with conn.cursor() as cursor:
        with cursor.copy(
            """
            COPY transactions 
                (invoice_no, stock_code, description, quantity, invoice_date, unit_price, customer_id, country) 
            FROM STDIN
            """
            ) as copy:
            for record in records:
                copy.write_row(record)

        return cursor.rowcount
