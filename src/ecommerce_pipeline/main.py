# 10/19/2026
import logging

from ecommerce_pipeline.config import ANALYTICS_DIR, SCHEMA_DIR, VIEW_DIR
from ecommerce_pipeline.loading.postgres import connect_postgres, initialize_postgres
from ecommerce_pipeline.logging_config import log_summary, setup_logging
from ecommerce_pipeline.pipelines.transactions import run_transaction_pipeline

logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()

    logger.info("Starting...")

    summary = {}

    with connect_postgres() as conn:
        initialize_postgres(conn, SCHEMA_DIR)
        initialize_postgres(conn, VIEW_DIR)
        initialize_postgres(conn, ANALYTICS_DIR)

        summary["transactions"] = run_transaction_pipeline(conn)

    log_summary(summary)

    logger.info("All pipelines finished")


if __name__ == "__main__":
    main()
