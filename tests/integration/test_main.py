import polars as pl
import pytest

from ecommerce_pipeline.config import PROJECT_ROOT
from ecommerce_pipeline.main import main
from ecommerce_pipeline.pipelines.transactions import run_transaction_pipeline
from tests.factories import HEADER, ROWS


def test_main_loads_file(conn, tmp_path):
    csv = tmp_path / "transactions.csv"
    csv.write_text(HEADER + ROWS, encoding="cp1252")

    main(["--path", str(csv), "--rejected-path", str(tmp_path / "rejected")])

    assert conn.execute("SELECT count(*) FROM transactions").fetchone() == (12,)


def test_main_exits_when_file_is_missing(tmp_path):
    with pytest.raises(SystemExit):
        main(["--path", str(tmp_path / "nonexistent_file.csv")])


def test_rejects_are_saved(conn, tmp_path):
    csv = tmp_path / "transactions.csv"
    csv.write_text(HEADER + ROWS, encoding="cp1252")

    result = run_transaction_pipeline(
        conn, path=csv, rejected_path=tmp_path / "rejected" / "transactions"
    )

    files = list((tmp_path / "rejected" / "transactions").glob("*.parquet"))

    assert len(files) == 1
    assert pl.read_parquet(files[0]).height == result.rejected


def test_sample_pipeline_matches_documented_summary(conn, tmp_path):
    sample = PROJECT_ROOT / "data" / "sample" / "sample.csv"

    result = run_transaction_pipeline(
        conn, path=sample, rejected_path=tmp_path / "rejected" / "transactions"
    )

    assert (result.read, result.rejected, result.skipped, result.loaded) == (
        49,
        8,
        0,
        41,
    )
