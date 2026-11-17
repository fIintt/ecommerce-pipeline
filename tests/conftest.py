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

HEADER = "InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country\n"

ROWS = (
    "536365,85123A,WHITE HANGING HEART,6,12/1/2010 8:26,2.55,17850,United Kingdom\n"
    "536365,71053,WHITE METAL LANTERN,6,12/1/2010 8:26,3.39,17850,United Kingdom\n"
    "536366,22633,HAND WARMER,2,12/1/2010 8:28,1.85,13047,France\n"
    "536367,84406B,CREAM CUPID HEARTS,3,12/1/2010 8:34,4.00,,United Kingdom\n"
    "536370,22728,ALARM CLOCK BAKELIKE,4,12/2/2010 9:00,2.50,17850,United Kingdom\n"
    "C536379,22423,REGENCY CAKESTAND 3 TIER,-1,12/2/2010 9:41,10.00,13047,France\n"
    "537000,22086,PAPER CHAIN KIT,5,1/5/2011 10:00,3.00,12583,France\n"
    # Non-product lines
    "536371,POST,POSTAGE,1,12/1/2010 9:00,15.00,17850,United Kingdom\n"
    "536372,M,Manual,1,12/1/2010 9:30,99.99,99999,Germany\n"
    "C536380,D,Discount,-1,12/2/2010 10:00,5.00,13047,France\n"
)


@pytest.fixture
def loaded(conn, tmp_path: Path):
    csv = tmp_path / "transactions.csv"
    csv.write_text(HEADER + ROWS, encoding="cp1252")

    result = run_transaction_pipeline(conn, csv)

    assert result.loaded == len(ROWS.splitlines())

    return conn