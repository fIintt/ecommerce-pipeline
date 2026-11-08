from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
REJECTED_DIR = PROJECT_ROOT / "data" / "rejected"
SCHEMA_DIR = PROJECT_ROOT / "sql" / "schemas"
VIEW_DIR = PROJECT_ROOT / "sql" / "views"
ANALYTICS_DIR = PROJECT_ROOT / "sql" / "analytics"

BRONZE_TRANSACTION_PATH = BRONZE_DIR / "transactions.csv"

REJECTED_TRANSACTION_PATH = REJECTED_DIR / "transactions"


@dataclass(frozen=True)
class DatabaseSettings:
    user: str
    password: str
    host: str
    port: int
    name: str


def require_env(name: str) -> str:
    # If the 'name' doesnt exist, it returns None instead of crashing the program, unlike os.environ[name]
    value = os.environ.get(name)

    if not value or not value.strip():
        raise ValueError(f"Required environment variable {name!r} is missing or empty")

    return value


def setup_database_settings() -> DatabaseSettings:
    load_dotenv(PROJECT_ROOT / ".env")

    return DatabaseSettings(
        user=require_env("DB_USER"),
        password=require_env("DB_PASSWORD"),
        host=require_env("DB_HOST"),
        port=int(require_env("DB_PORT")),
        name=require_env("DB_NAME"),
    )
