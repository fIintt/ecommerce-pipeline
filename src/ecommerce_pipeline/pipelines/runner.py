import logging
import time
from collections.abc import Callable
from pathlib import Path

import polars as pl
import psycopg

from ecommerce_pipeline.config import REJECTED_DIR
from ecommerce_pipeline.ingestion.extractor import extract_csv, hash_file
from ecommerce_pipeline.loading.parquet import load_rejected_data
from ecommerce_pipeline.loading.postgres import (
    load_loaded_file_summaries,
    load_loaded_files,
)
from ecommerce_pipeline.models import BatchResult, PipelineResult


def _process_batch(
    *,
    raw: pl.LazyFrame,
    validate_input: Callable[[pl.LazyFrame], tuple[pl.LazyFrame, pl.LazyFrame]],
    transform: Callable[[pl.LazyFrame], pl.LazyFrame],
    validate_output: Callable[[pl.LazyFrame], tuple[pl.LazyFrame, pl.LazyFrame]],
) -> BatchResult:
    valid_input, rejected_input = validate_input(raw)
    transformed = transform(valid_input)
    valid_output, rejected_output = validate_output(transformed)

    rejected_output = raw.join(
        rejected_output.select("_source_row_number", "_reject_reason"),
        on="_source_row_number",
        how="inner",
    )

    rejected = pl.concat(
        [
            rejected_input.with_columns(pl.lit("input").alias("_reject_stage")),
            rejected_output.with_columns(pl.lit("output").alias("_reject_stage")),
        ],
        how="diagonal",
    )

    read_df, valid_df, rejected_df = pl.collect_all(
        [raw.select(pl.len()), valid_output, rejected]
    )

    return BatchResult(
        read=read_df.item(),
        valid=valid_df,
        rejected=rejected_df,
    )


def _check_reconciliation(batch: BatchResult) -> None:
    total_processed = batch.valid.height + batch.rejected.height

    if batch.read != total_processed:
        raise ValueError(
            f"Counts do not add up: read={batch.read} "
            f"valid={batch.valid.height} rejected={batch.rejected.height}"
        )


def _process_rejected_data(
    *,
    rejected: pl.DataFrame,
    pipeline_name: str,
    file_hash: str,
) -> None:
    processed = load_rejected_data(rejected, REJECTED_DIR / pipeline_name, file_hash)

    if processed != rejected.height:
        raise ValueError(
            f"Rejected row persistence mismatch: "
            f"expected={rejected.height} saved={processed}"
        )


def run_pipeline(
    *,  # Everything after this must be passed by keyword.
    name: str,
    conn: psycopg.Connection,
    path: Path,
    validate_input: Callable[[pl.LazyFrame], tuple[pl.LazyFrame, pl.LazyFrame]],
    transform: Callable[[pl.LazyFrame], pl.LazyFrame],
    validate_output: Callable[[pl.LazyFrame], tuple[pl.LazyFrame, pl.LazyFrame]],
    load: Callable[[psycopg.Connection, pl.DataFrame], int],
) -> PipelineResult:
    logger = logging.getLogger(f"pipeline.{name}")

    started_at = time.perf_counter()

    try:
        file_hash = hash_file(path)

        with extract_csv(path) as raw:
            batch = _process_batch(
                raw=raw,
                validate_input=validate_input,
                transform=transform,
                validate_output=validate_output,
            )

        _check_reconciliation(batch)

        _process_rejected_data(
            rejected=batch.rejected,
            pipeline_name=name,
            file_hash=file_hash,
        )

        with conn.transaction():
            load_id, file_created = load_loaded_files(conn, file_hash, path.name)

            if not file_created:
                loaded = 0

            else:
                ready_batch = batch.valid.with_columns(
                    pl.lit(load_id).alias("_loaded_file_id")
                )

                loaded = load(conn, ready_batch)

                if loaded != ready_batch.height:
                    raise ValueError(
                        f"Load mismatch: expected={ready_batch.height} loaded={loaded}"
                    )

            result = PipelineResult(
                read=batch.read,
                rejected=batch.rejected.height,
                skipped=batch.valid.height - loaded,
                loaded=loaded,
                elapsed=time.perf_counter() - started_at,
            )

            if file_created:
                load_loaded_file_summaries(conn, load_id, result)

        return result

    except KeyError, ValueError, TypeError:
        logger.exception("Pipeline encountered an error")

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
