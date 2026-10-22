# 10/19/2026
import logging

from ecommerce_pipeline.logging_config import setup_logging
from ecommerce_pipeline.pipelines.transactions import run_pipeline

logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()

    try:
        result = run_pipeline("data/silver/transactions_utf8.csv")

    except Exception:
        logger.exception("Pipeline failed")

        raise
    
    logger.info(f"Pipeline result: {result}")


if __name__ == "__main__":
    main()
