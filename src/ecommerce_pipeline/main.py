# 10/19/2026
import argparse
import logging
from pathlib import Path

from ecommerce_pipeline.config import (
    ANALYTICS_DIR,
    RAW_DIR,
    REJECTED_DIR,
    SCHEMA_DIR,
    VIEW_DIR,
)
from ecommerce_pipeline.loading.postgres import connect_postgres, initialize_postgres
from ecommerce_pipeline.logging_config import log_summary, setup_logging
from ecommerce_pipeline.models import PipelineResult
from ecommerce_pipeline.pipelines.transactions import run_transaction_pipeline

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the ecommerce pipelines")
    parser.add_argument(
        "--path",
        type=Path,
        default=RAW_DIR / "data.csv",
        help="Raw transactions CSV (default: %(default)s)",
    )
    parser.add_argument(
        "--rejected-path",
        type=Path,
        default=REJECTED_DIR,
        help="Where rejected rows are written as Parquet (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    if not args.path.is_file():
        raise SystemExit(f"Input file not found: {args.path}")

    setup_logging()

    logger.info("Starting...")

    summary: dict[str, PipelineResult] = {}

    with connect_postgres() as conn:
        initialize_postgres(conn, SCHEMA_DIR)
        initialize_postgres(conn, VIEW_DIR)
        initialize_postgres(conn, ANALYTICS_DIR)

        summary["transactions"] = run_transaction_pipeline(
            conn, path=args.path, rejected_path=args.rejected_path / "transactions"
        )

    log_summary(summary)

    logger.info("All pipelines finished")


if __name__ == "__main__":
    main()
