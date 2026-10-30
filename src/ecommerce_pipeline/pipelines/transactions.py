import hashlib
import logging
from pathlib import Path
import time

import polars as pl
import psycopg

from ecommerce_pipeline.ingestion.transactions import extract_transactions
from ecommerce_pipeline.loading.parquet import load_rejected_transactions
from ecommerce_pipeline.loading.postgres import load_transactions
from ecommerce_pipeline.transformation.transactions import transform_transactions
from ecommerce_pipeline.validation.transactions import validate_transactions

from ecommerce_pipeline.config import (
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    REJECTED_TRANSACTIONS_PATH,
)

logger = logging.getLogger(__name__)


def connect_postgres() -> psycopg.Connection:
    return psycopg.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def hash_file(path: Path, chunk_size: int = 1 << 20) -> str:
    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def run_pipeline(path: Path) -> None:
    started_at = time.perf_counter()

    logger.info("Transactions pipeline started")

    try:
        source_file_hash = hash_file(path)

        with extract_transactions(path, source_file_hash) as raw:
            validated, rejected = validate_transactions(raw)
            transformed = transform_transactions(validated)

            read_df, transformed_df, rejected_df = pl.collect_all(
                [raw.select(pl.len()), transformed, rejected]
            )

        read = read_df.item()  # Total rows in the source .csv
        received = transformed_df.height  # Total rows that passed the transformation
        rejected_count = rejected_df.height

        if read != rejected_count + received:
            raise ValueError(
                f"Counts do not add up: read={read} "
                f"rejected={rejected_count} valid={received}"
            )

        loaded_rejected_count = load_rejected_transactions(
            rejected_df,
            REJECTED_TRANSACTIONS_PATH,
            source_file_hash,
        )

        if loaded_rejected_count != rejected_count:
            raise ValueError(
                f"Rejected row persistence mismatch: "
                f"expected={rejected_count} "
                f"loaded={loaded_rejected_count}"
            )

        with connect_postgres() as conn:
            loaded = load_transactions(conn, transformed_df)

        skipped = received - loaded

        logger.info(
            "read=%d rejected=%d skipped=%d loaded=%d",
            read,
            rejected_count,
            skipped,
            loaded,
        )

    except KeyError, ValueError, TypeError:
        logger.exception("Transactions pipeline failed")
        raise

    except psycopg.OperationalError:
        logger.exception("Database connection/operation failed")
        raise

    except psycopg.DataError:
        logger.exception("Database rejected the data")
        raise

    except psycopg.Error:
        logger.exception("Miscellaneous database error")
        raise

    else:
        logger.info("Transactions pipeline succeeded")

    finally:
        elapsed = time.perf_counter() - started_at
        logger.info("Elapsed - %.2f seconds", elapsed)
