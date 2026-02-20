"""Logger utility for the Playwright QA Agent."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

VALID_LEVELS = ("debug", "info", "warning", "error")


def setup_logger(
    name: str = "playwright_qa_agent",
    level: str = "info",
    log_file: Optional[Path | str] = None,
) -> logging.Logger:
    """Create and configure a logger instance.

    Args:
        name: Logger name (used in log output).
        level: Log level string: debug, info, warning, error.
        log_file: Optional file path to write logs to.

    Returns:
        Configured logger instance.
    """
    level_upper = level.upper()
    numeric_level = getattr(logging, level_upper, logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)

    # Avoid adding duplicate handlers if logger already set up
    if logger.handlers:
        return logger

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file is not None:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "playwright_qa_agent") -> logging.Logger:
    """Get an existing logger by name.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)
