from pathlib import Path

from ecommerce_pipeline.pipelines.transactions import run_transaction_pipeline
from tests.factories import HEADER, ROWS


def count_rows(conn, table: str) -> int:
    row = conn.execute(f"SELECT count(*) FROM {table}").fetchone()

    assert row is not None

    return row[0]


def test_second_run_is_skipped(conn, tmp_path: Path):
    csv = tmp_path / "transactions.csv"
    csv.write_text(HEADER + ROWS, encoding="cp1252")

    first = run_transaction_pipeline(
        conn, path=csv, rejected_path=tmp_path / "rejected" / "transactions"
    )
    second = run_transaction_pipeline(
        conn, path=csv, rejected_path=tmp_path / "rejected" / "transactions"
    )

    assert (first.loaded, first.skipped) == (12, 0)
    assert (second.loaded, second.skipped) == (0, 12)

    assert count_rows(conn, "loaded_files") == 1
