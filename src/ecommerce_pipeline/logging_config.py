import logging


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%m/%d/%Y %I:%M %p",  # MM/DD/YYYY HH:MM AM/PM (e.g., 10/19/2026 10:28 AM)
    )
