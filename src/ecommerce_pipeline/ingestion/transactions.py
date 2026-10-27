from contextlib import contextmanager
import hashlib
from pathlib import Path
import shutil
import tempfile
from typing import Generator

import polars as pl


def hash_file(path: Path, chunk_size: int = 1 << 20) -> str:
    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


@contextmanager
def extract_transactions(
    path: Path, chunk_size: int = 1 << 20
) -> Generator[pl.LazyFrame]:
    with tempfile.TemporaryDirectory(prefix="transactions_") as tmp:
        utf8_path = Path(tmp) / f"{path.stem}_utf8.csv"

        with (
            open(path, "r", encoding="cp1252", newline="") as file_in,
            open(utf8_path, "w", encoding="utf-8", newline="") as file_out,
        ):
            shutil.copyfileobj(file_in, file_out, chunk_size)

        source_file_hash = hash_file(path, chunk_size)

        yield (
            pl.scan_csv(
                utf8_path,
                infer_schema=False,
                row_index_name="source_row_number",
                row_index_offset=1,
            )
            .rename(lambda name: name.strip())
            .with_columns(pl.lit(source_file_hash).alias("source_file_hash"))
            .cast(
                {
                    "source_row_number": pl.Int64,
                    "Quantity": pl.Int32,
                    "UnitPrice": pl.Decimal(12, 4),
                }
            )
        )
