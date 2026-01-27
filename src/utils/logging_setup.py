"""Logging configuration for the chicken coop application."""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Name for the logger (typically __name__)

    Returns:
        Logger instance for the specified name
    """
    return logging.getLogger(name)


def _is_our_handler(handler: logging.Handler) -> bool:
    """Check if a handler was created by our logging setup."""
    return getattr(handler, "_chickencoop_handler", False)


def setup_logging(
    level: int = None,
    log_file: Path = None,
    console: bool = True,
    include_coop_id: bool = False,
) -> None:
    """
    Configure logging with the specified settings.

    Sets up root logger with console and/or file handlers.
    Log level can be set via parameter or LOG_LEVEL environment variable.

    Args:
        level: Logging level (e.g., logging.INFO). Defaults to LOG_LEVEL env var or INFO.
        log_file: Optional path to log file
        console: Whether to log to console (default: True)
        include_coop_id: Whether to include COOP_ID in log format (default: False)
    """
    root_logger = logging.getLogger()
    # Remove only handlers we created, not pytest's caplog handler
    for handler in root_logger.handlers[:]:
        if _is_our_handler(handler):
            root_logger.removeHandler(handler)

    # Determine log level
    if level is None:
        env_level = os.environ.get("LOG_LEVEL")
        if env_level:
            level = getattr(logging, env_level.upper(), logging.INFO)
        else:
            level = logging.INFO

    root_logger.setLevel(level)

    # Build format string
    if include_coop_id:
        coop_id = os.environ.get("COOP_ID", "unknown")
        fmt = f"%(asctime)s - %(levelname)s - %(name)s - [{coop_id}] - %(message)s"
    else:
        fmt = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

    formatter = logging.Formatter(fmt)

    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler._chickencoop_handler = True
        root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler._chickencoop_handler = True
        root_logger.addHandler(file_handler)


def setup_logging_with_rotation(
    log_file: Path,
    max_bytes: int = 10485760,
    backup_count: int = 5,
) -> None:
    """
    Configure logging with rotating file handler.

    Sets up a rotating file handler that automatically rotates log files
    when they reach the specified size.

    Args:
        log_file: Path to the log file
        max_bytes: Maximum file size before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
    """
    root_logger = logging.getLogger()
    # Remove only handlers we created
    for handler in root_logger.handlers[:]:
        if _is_our_handler(handler):
            root_logger.removeHandler(handler)
    root_logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    rotating_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
    )
    rotating_handler.setFormatter(formatter)
    rotating_handler._chickencoop_handler = True
    root_logger.addHandler(rotating_handler)
