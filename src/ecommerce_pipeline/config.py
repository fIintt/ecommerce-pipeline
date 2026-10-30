import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


def require_env(name: str) -> str:
    # If the 'name' doesnt exist, it returns None instead of crashing the program, unlike os.environ[name]
    value = os.environ.get(name)

    if not value or not value.strip():
        raise ValueError(f"Required environment variable {name!r} is missing or empty")

    return value


# Database
DB_USER = require_env("DB_USER")
DB_PASSWORD = require_env("DB_PASSWORD")
DB_HOST = require_env("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = require_env("DB_NAME")

# Path
RAW_TRANSACTIONS_PATH = Path("data/bronze/transactions.csv")
REJECTED_TRANSACTIONS_PATH = Path("data/rejected")