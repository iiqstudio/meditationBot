"""Logging configuration for bot runtime."""

import logging


def setup_logging() -> None:
    """Configure log formatting and levels."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
