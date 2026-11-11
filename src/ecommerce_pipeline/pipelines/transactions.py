from pathlib import Path

import psycopg

from ecommerce_pipeline.loading.postgres import load_transactions
from ecommerce_pipeline.pipelines.runner import PipelineResult, run_pipeline
from ecommerce_pipeline.transformation.transactions import transform_transactions
from ecommerce_pipeline.validation.transactions import (
    validate_transaction_input,
    validate_transaction_output,
)

from ecommerce_pipeline.config import (
    BRONZE_DIR,
)


def run_transaction_pipeline(
    conn: psycopg.Connection, path: Path = BRONZE_DIR / "transactions.csv"
) -> PipelineResult:
    return run_pipeline(
        name="transactions",
        conn=conn,
        path=path,
        validate_input=validate_transaction_input,
        transform=transform_transactions,
        validate_output=validate_transaction_output,
        load=load_transactions,
    )
