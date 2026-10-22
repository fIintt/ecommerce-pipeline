import logging
import time

import psycopg

from ecommerce_pipeline.ingestion.transactions import extract_transactions
from ecommerce_pipeline.loading.postgres import load_transactions
from ecommerce_pipeline.transformation.transactions import transform_transactions
from ecommerce_pipeline.validation.transactions import validate_transactions

logger = logging.getLogger(__name__)


def run_pipeline(path: str) -> None:
    started_at = time.perf_counter()

    logger.info("Transaction pipeline started")

    try:
        raw = extract_transactions(path)
        validated = validate_transactions(raw)
        transformed = transform_transactions(validated)
        loaded = load_transactions(transformed.head(10))

        skipped = len(transformed) - loaded

        logger.info(
            f"Pipeline finished: received={len(transformed)} inserted={loaded} skipped={skipped}"
        )

    except KeyError, ValueError, TypeError:
        logger.exception("Weather data validation failed")
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
        logger.info("Transaction pipeline succeeded.")

    finally:
        elapsed = time.perf_counter() - started_at
        logger.info(f"Elapsed - {elapsed:.2f} seconds")
