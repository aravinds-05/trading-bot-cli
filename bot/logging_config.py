"""Sets up logging - a rotating file handler plus a console handler.

Call configure_logging() once at startup. Everywhere else just does
logging.getLogger(...) / get_logger(...) and it picks up these handlers.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pythonjsonlogger.jsonlogger import JsonFormatter

MAX_BYTES = 5 * 1024 * 1024  # 5MB, then rotate
BACKUP_COUNT = 5

FILE_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
CONSOLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"


def configure_logging(log_path: Path, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("trading_bot")
    logger.setLevel(level)

    if logger.handlers:
        # already set up (happens if this gets called twice, e.g. in tests)
        return logger

    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        filename=str(log_path),
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(JsonFormatter(FILE_FORMAT))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # keep the terminal quiet
    console_handler.setFormatter(logging.Formatter(CONSOLE_FORMAT))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"trading_bot.{name}")
