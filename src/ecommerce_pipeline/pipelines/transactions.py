from pathlib import Path

import psycopg

from ecommerce_pipeline.loading.postgres import load_transactions
from ecommerce_pipeline.pipelines.runner import PipelineResult, run_pipeline
from ecommerce_pipeline.transformation.transactions import transform_transactions
from ecommerce_pipeline.validation.transactions import (
    validate_transaction_input,
    validate_transaction_output,
)


def run_transaction_pipeline(
    conn: psycopg.Connection,
    *,
    path: Path,
    rejected_path: Path,
) -> PipelineResult:
    return run_pipeline(
        name="transactions",
        conn=conn,
        path=path,
        rejected_path=rejected_path,
        validate_input=validate_transaction_input,
        transform=transform_transactions,
        validate_output=validate_transaction_output,
        load=load_transactions,
    )
