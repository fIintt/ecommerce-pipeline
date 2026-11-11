import logging
from typing import get_type_hints

from rich import box
from rich.logging import RichHandler
from rich.table import Table
from rich.console import Console

from ecommerce_pipeline.pipelines.runner import PipelineResult


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s | %(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )


def log_summary(results: dict[str, PipelineResult]) -> None:
    table = Table(title="Summary", title_style="bold", box=box.MINIMAL, expand=True)

    table.add_column("pipeline")

    for col in list(get_type_hints(PipelineResult)):
        table.add_column(col, justify="right")

    for name, result in results.items():
        table.add_row(
            name,
            str(result.read),
            f"[red]{result.rejected}[/red]" if result.rejected else "0",
            f"[yellow]{result.skipped}[/yellow]" if result.skipped else "0",
            f"[green]{result.loaded}[/green]" if result.loaded else "0",
            f"{result.elapsed:.2f}s",
        )

    Console().print(table)
