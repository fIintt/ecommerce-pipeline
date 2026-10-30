# 10/19/2026
import argparse
import logging
from pathlib import Path

from ecommerce_pipeline.config import RAW_TRANSACTIONS_PATH
from ecommerce_pipeline.logging_config import setup_logging
from ecommerce_pipeline.pipelines.transactions import run_pipeline

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the transactions pipeline")
    parser.add_argument(
        "--path",
        type=Path,
        default=RAW_TRANSACTIONS_PATH,
        help="Path to the raw transactions CSV (default: %(default)s)",
    )
    return parser.parse_args()


def main() -> None:
    setup_logging()

    path = parse_args().path

    if not path.is_file():
        raise SystemExit(f"Input file not found: {path}")

    try:
        run_pipeline(path)

    except Exception:
        logger.exception("Pipeline failed")

        raise


if __name__ == "__main__":
    main()
