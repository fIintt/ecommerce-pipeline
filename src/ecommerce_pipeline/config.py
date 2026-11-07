import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


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
DB_PORT = int(require_env("DB_PORT"))
DB_NAME = require_env("DB_NAME")

# Path
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
REJECTED_DIR = PROJECT_ROOT / "data" / "rejected"
SCHEMA_DIR = PROJECT_ROOT / "sql" / "schemas"
VIEW_DIR = PROJECT_ROOT / "sql" / "views"

BRONZE_TRANSACTION_PATH = BRONZE_DIR / "transactions.csv"

REJECTED_TRANSACTION_PATH = REJECTED_DIR / "transactions"
