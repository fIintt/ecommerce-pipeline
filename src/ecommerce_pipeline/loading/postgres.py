import psycopg
import polars as pl


def load_transactions(conn: psycopg.Connection, rows: pl.DataFrame) -> int:
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
