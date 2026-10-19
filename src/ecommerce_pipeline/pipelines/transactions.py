from ecommerce_pipeline.ingestion.clients import extract_transactions
from ecommerce_pipeline.validation.validate import validate_transactions


def run_pipeline() -> None:
    transactions = extract_transactions("data/processed/transactions_utf8.csv")

    validated = validate_transactions(transactions)
