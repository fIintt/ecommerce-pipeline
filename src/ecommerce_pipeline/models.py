from dataclasses import dataclass

import polars as pl


@dataclass(frozen=True)
class DatabaseSettings:
    user: str
    password: str
    host: str
    port: int
    name: str


@dataclass(frozen=True)
class PipelineResult:  # Summary of a run
    read: int
    rejected: int
    skipped: int
    loaded: int
    elapsed: float


@dataclass(frozen=True)
class BatchResult:  # Frames produced by validating and transforming one file.
    read: int
    valid: pl.DataFrame
    rejected: pl.DataFrame
