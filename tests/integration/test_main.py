import pytest

from ecommerce_pipeline.main import main
from tests.factories import CSV_CONTENT


def test_main_loads_file(conn, tmp_path):
    csv = tmp_path / "transactions.csv"
    csv.write_text(CSV_CONTENT, encoding="cp1252")

    main(["--path", str(csv)])

    assert conn.execute("SELECT count(*) FROM transactions").fetchone() == (2,)


def test_main_exits_when_file_is_missing(tmp_path):
    with pytest.raises(SystemExit):
        main(["--path", str(tmp_path / "nonexistent_file.csv")])