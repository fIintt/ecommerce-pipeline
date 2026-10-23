import logging
from pathlib import Path
import time

import psycopg

from ecommerce_pipeline.ingestion.transactions import extract_transactions
from ecommerce_pipeline.loading.postgres import load_transactions
from ecommerce_pipeline.transformation.transactions import transform_transactions
from ecommerce_pipeline.validation.transactions import validate_transactions

logger = logging.getLogger(__name__)


def run_pipeline(path: Path) -> None:
    started_at = time.perf_counter()

    logger.info("Transactions pipeline started")

    try:
        with extract_transactions(path) as raw:
            validated = validate_transactions(raw)
            transformed = transform_transactions(validated).collect()
        loaded = load_transactions(transformed)

        if transformed.height == loaded:
            logger.info(f"received={transformed.height} inserted={loaded}")
        else:
            logger.warning(f"Mismatch: received={transformed.height} inserted={loaded}")

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
        logger.info("Transactions pipeline succeeded.")

    finally:
        elapsed = time.perf_counter() - started_at
        logger.info(f"Elapsed - {elapsed:.2f} seconds")
