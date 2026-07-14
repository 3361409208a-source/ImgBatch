#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional
"""Structured logging for ImgBatch.

All operations, errors, and diagnostics are written to a log file
at ``~/.imgbatch/imgbatch.log``.
"""

import logging
import sys
from pathlib import Path

LOG_DIR = Path.home() / ".imgbatch"
LOG_FILE = LOG_DIR / "imgbatch.log"

_logger: Optional[logging.Logger] = None


def get_logger(name: str = "imgbatch") -> logging.Logger:
    """Return the singleton logger, initializing on first call."""
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger(name)
    _logger.setLevel(logging.DEBUG)

    # File handler — always created
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        _logger.addHandler(fh)
    except OSError:
        # If we can't write to the log directory, fall back to stderr
        pass

    # Console handler — only when running from terminal (not --windowed EXE)
    if sys.stderr is not None and sys.stderr.isatty():
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(logging.INFO)
        ch.setFormatter(
            logging.Formatter("[%(levelname)s] %(message)s")
        )
        _logger.addHandler(ch)

    return _logger


def log_operation(op_type: str, **kwargs):
    """Convenience: log an operation with structured key-value context."""
    parts = [f"{k}={v}" for k, v in kwargs.items()]
    get_logger().info("OPERATION %s | %s", op_type, " | ".join(parts))


def log_error(exc: Exception, context: str = ""):
    """Log an exception with full traceback and optional context."""
    logger = get_logger()
    if context:
        logger.error("ERROR in %s: %s: %s", context, type(exc).__name__, exc)
    else:
        logger.error("ERROR: %s: %s", type(exc).__name__, exc)
    logger.debug("Traceback:", exc_info=True)
