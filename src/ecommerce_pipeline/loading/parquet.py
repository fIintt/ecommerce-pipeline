from pathlib import Path

import polars as pl


def load_rejected_data(
    rows: pl.DataFrame,
    path: Path,
    file_hash: str,
) -> int:
    if not rows.height:
        return 0

    dir = path / file_hash[:12]
    dir.mkdir(parents=True, exist_ok=True)

    path = dir / f"rejected.parquet"

    rows.write_parquet(path)

    return rows.height
