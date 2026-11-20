from pathlib import Path

import pytest
from dotenv import load_dotenv

from ecommerce_pipeline.config import (
    ANALYTICS_DIR,
    PROJECT_ROOT,
    SCHEMA_DIR,
    VIEW_DIR,
    require_env,
)
from ecommerce_pipeline.loading.postgres import connect_postgres, initialize_postgres
from ecommerce_pipeline.pipelines.transactions import run_transaction_pipeline
from tests.factories import HEADER, ROWS


@pytest.fixture(scope="session")
def _test_env():
    load_dotenv(PROJECT_ROOT / ".env")

    mp = pytest.MonkeyPatch()
    mp.setenv("DB_NAME", require_env("DB_NAME_TEST"))

    yield

    mp.undo()


@pytest.fixture(scope="session", autouse=True)
def schema(_test_env):
    with connect_postgres() as conn:
        dbname = conn.info.dbname

        assert "test" in dbname, f"refusing to run against {dbname!r}"

        conn.execute("DROP SCHEMA public CASCADE")
        conn.execute("CREATE SCHEMA public")

        initialize_postgres(conn, SCHEMA_DIR)
        initialize_postgres(conn, VIEW_DIR)
        initialize_postgres(conn, ANALYTICS_DIR)


@pytest.fixture
def conn():
    with connect_postgres() as conn:
        conn.execute("TRUNCATE transactions, loaded_files RESTART IDENTITY CASCADE")
        conn.commit()
        yield conn


@pytest.fixture
def loaded(conn, tmp_path: Path):
    csv = tmp_path / "transactions.csv"
    csv.write_text(HEADER + ROWS, encoding="cp1252")

    result = run_transaction_pipeline(
        conn, path=csv, rejected_path=tmp_path / "rejected" / "transactions"
    )

    assert (result.read, result.rejected, result.loaded) == (14, 2, 12)

    return conn
