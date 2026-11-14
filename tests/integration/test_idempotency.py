from pathlib import Path

from ecommerce_pipeline.pipelines.transactions import run_transaction_pipeline
from tests.factories import CSV_CONTENT


def count_rows(conn, table: str) -> int:
    row = conn.execute(f"SELECT count(*) FROM {table}").fetchone()

    assert row is not None

    return row[0]


def test_second_run_is_skipped(conn, tmp_path: Path):
    csv = tmp_path / "transactions.csv"
    csv.write_text(CSV_CONTENT, encoding="cp1252")

    first = run_transaction_pipeline(conn, csv)
    second = run_transaction_pipeline(conn, csv)

    assert (first.loaded, first.skipped) == (2, 0)
    assert (second.loaded, second.skipped) == (0, 2)

    assert count_rows(conn, "transactions") == 2
    assert count_rows(conn, "loaded_files") == 1
