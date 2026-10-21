"""
Structured logging configuration using Python's logging module.

Provides JSON-formatted logs for production and human-readable logs for development.
"""

import logging
import sys
from typing import Optional

from app.core.config import settings


def setup_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Create and configure a structured logger.

    Args:
        name: Logger name (typically __name__ of the calling module).
        level: Override log level. Defaults to settings.LOG_LEVEL.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    if level is None:
        level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        if settings.LOG_FORMAT == "json":
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"logger": "%(name)s", "message": "%(message)s"}',
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        else:
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
