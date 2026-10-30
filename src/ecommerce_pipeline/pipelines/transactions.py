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
        
        received = transformed.height
        skipped = received - loaded

        if loaded == received:
            logger.info("received=%d loaded=%d", received, loaded)
        elif loaded == 0:
            logger.info("No new rows, already loaded", received)
        else:
            logger.info("received=%d loaded=%d skipped=%d", received, loaded, skipped)

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
        logger.info("Elapsed - %.2f seconds", elapsed)
