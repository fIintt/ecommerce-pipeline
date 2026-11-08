from pathlib import Path

import psycopg

from ecommerce_pipeline.loading.postgres import load_transactions
from ecommerce_pipeline.logging_config import PipelineLogs
from ecommerce_pipeline.pipelines.runner import run_pipeline
from ecommerce_pipeline.transformation.transactions import transform_transactions
from ecommerce_pipeline.validation.transactions import (
    validate_transaction_input,
    validate_transaction_output,
)

from ecommerce_pipeline.config import (
    BRONZE_TRANSACTION_PATH,
    REJECTED_TRANSACTION_PATH,
)


def run_transaction_pipeline(
    conn: psycopg.Connection, path: Path = BRONZE_TRANSACTION_PATH
) -> PipelineLogs:
    return run_pipeline(
        name="transactions",
        conn=conn,
        path=path,
        rejected_path=REJECTED_TRANSACTION_PATH,
        validate_input=validate_transaction_input,
        transform=transform_transactions,
        validate_output=validate_transaction_output,
        load=load_transactions,
    )
