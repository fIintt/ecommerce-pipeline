from pathlib import Path
from typing import LiteralString, cast

import psycopg
import polars as pl
from psycopg import sql

from ecommerce_pipeline.config import (
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
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


def initialize_postgres(conn: psycopg.Connection, path: Path) -> None:
    for file in sorted(path.glob("*.sql")):
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
        (file_hash, file_name, row_count),
    ).fetchone()

    return row[0] if row else None


def load_transactions(conn: psycopg.Connection, rows: pl.DataFrame) -> int:
    COLUMNS = [
        "invoice_no",
        "stock_code",
        "description",
        "quantity",
        "invoice_date",
        "unit_price",
        "customer_id",
        "country",
    ]

    query = sql.SQL("COPY transactions ({columns}) FROM STDIN").format(
        columns=sql.SQL(", ").join(sql.Identifier(c) for c in COLUMNS)
    )

    with conn.cursor() as cursor:
        with cursor.copy(query) as copy:
            for record in rows.select(COLUMNS).iter_rows():
                copy.write_row(record)

        return cursor.rowcount
