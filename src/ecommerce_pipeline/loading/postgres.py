from pathlib import Path
from typing import LiteralString, cast

import polars as pl
import psycopg
from psycopg import sql

from ecommerce_pipeline.config import setup_database_settings
from ecommerce_pipeline.models import PipelineResult


def connect_postgres() -> psycopg.Connection:
    settings = setup_database_settings()

    return psycopg.connect(
        host=settings.host,
        port=settings.port,
        dbname=settings.name,
        user=settings.user,
        password=settings.password,
        connect_timeout=10,
        options="-c lock_timeout=10000",  # millisecond
    )


def initialize_postgres(conn: psycopg.Connection, path: Path) -> None:
    for file in sorted(path.glob("*.sql")):
        conn.execute(cast(LiteralString, file.read_text(encoding="utf-8")))


def load_loaded_files(
    conn: psycopg.Connection, file_hash: str, file_name: str
) -> tuple[int, bool]:
    row = conn.execute(
        """
        INSERT INTO 
            loaded_files (file_hash, file_name)
        VALUES 
            (%s, %s)
        ON CONFLICT 
            (file_hash) 
        DO NOTHING
        RETURNING 
            id
        """,
        (file_hash, file_name),
    ).fetchone()

    if row:
        return row[0], True

    row = conn.execute(
        "SELECT id FROM loaded_files WHERE file_hash = %s", (file_hash,)
    ).fetchone()

    if row is None:
        raise RuntimeError(f"loaded_files row unavailable for hash {file_hash}")

    return row[0], False


def load_loaded_file_summaries(
    conn: psycopg.Connection, load_id: int, result: PipelineResult
) -> None:
    conn.execute(
        """
        INSERT INTO 
            loaded_file_summaries (loaded_file_id, row_count, rejected_count, skipped_count, loaded_count, elapsed_seconds)
        VALUES
            (%s, %s, %s, %s, %s, %s)
        """,
        (
            load_id,
            result.read,
            result.rejected,
            result.skipped,
            result.loaded,
            result.elapsed,
        ),
    )


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
        "_loaded_file_id",
        "_source_row_number",
    ]

    query = sql.SQL("COPY transactions ({columns}) FROM STDIN").format(
        columns=sql.SQL(", ").join(sql.Identifier(col) for col in COLUMNS)
    )

    with conn.cursor() as cursor:
        with cursor.copy(query) as copy:
            for record in rows.select(COLUMNS).iter_rows():
                copy.write_row(record)

        return cursor.rowcount
