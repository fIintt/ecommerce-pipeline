import logging
import time
from collections.abc import Callable
from pathlib import Path

import polars as pl
import psycopg

from ecommerce_pipeline.loading.postgres import load_loaded_files
from ecommerce_pipeline.logging_config import PipelineLogs
from ecommerce_pipeline.ingestion.extractor import extract_csv, hash_file
from ecommerce_pipeline.loading.parquet import load_rejected_data


def run_pipeline(
    *,
    name: str,
    conn: psycopg.Connection,
    path: Path,
    rejected_path: Path,
    validate_input: Callable[[pl.LazyFrame], tuple[pl.LazyFrame, pl.LazyFrame]],
    transform: Callable[[pl.LazyFrame], pl.LazyFrame],
    validate_output: Callable[[pl.LazyFrame], tuple[pl.LazyFrame, pl.LazyFrame]],
    load: Callable[[psycopg.Connection, pl.DataFrame], int],
) -> PipelineLogs:
    logger = logging.getLogger(f"pipeline.{name}")

    started_at = time.perf_counter()

    try:
        source_file_hash = hash_file(path)

        with extract_csv(path) as raw:
            valid_input, rejected_input = validate_input(raw)
            transformed = transform(valid_input)
            valid_output, rejected_output = validate_output(transformed)

            output_rejected = raw.join(
                rejected_output.select("source_row_number", "reject_reason"),
                on="source_row_number",
                how="inner",
            )

            rejected = pl.concat(
                [
                    rejected_input.with_columns(pl.lit("source").alias("reject_stage")),
                    output_rejected.with_columns(
                        pl.lit("output").alias("reject_stage")
                    ),
                ],
                how="diagonal",
            )

            read_df, deduped_df, valid_df, rejected_df = pl.collect_all(
                [
                    raw.select(pl.len()),
                    transformed.select(pl.len()),
                    valid_output,
                    rejected,
                ]
            )

        read = read_df.item()
        duplicates = read - deduped_df.item()
        validated_count = valid_df.height
        rejected_count = rejected_df.height

        if read != duplicates + rejected_count + validated_count:
            raise ValueError(
                f"Counts do not add up: read={read} duplicates={duplicates} "
                f"rejected={rejected_count} valid={validated_count}"
            )

        loaded_rejected_count = load_rejected_data(
            rejected_df, rejected_path, source_file_hash
        )

        if loaded_rejected_count != rejected_count:
            raise ValueError(
                f"Rejected row persistence mismatch: "
                f"expected={rejected_count} loaded={loaded_rejected_count}"
            )

        with conn.transaction():
            load_id = load_loaded_files(
                conn, source_file_hash, path.name, validated_count
            )

            if load_id is None:
                loaded = 0

            else:
                loaded = load(conn, valid_df)

                if loaded != validated_count:
                    raise ValueError(
                        f"Load mismatch: expected={validated_count} loaded={loaded}"
                    )

        skipped = validated_count - loaded
        elapsed = time.perf_counter() - started_at

        return {
            "read": read,
            "duplicated": duplicates,
            "rejected": rejected_count,
            "skipped": skipped,
            "loaded": loaded,
            "elapsed": elapsed,
        }

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
