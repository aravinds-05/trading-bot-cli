"""Unit tests for bot.logging_config – configure_logging and get_logger."""

from __future__ import annotations

import logging
from pathlib import Path

from bot.logging_config import configure_logging, get_logger


class TestConfigureLogging:
    def test_creates_log_file_directory(self, tmp_path: Path) -> None:
        log_path = tmp_path / "subdir" / "test.log"
        logger = configure_logging(log_path)
        assert log_path.parent.exists()
        assert logger.name == "trading_bot"

    def test_adds_handlers(self, tmp_path: Path) -> None:
        log_path = tmp_path / "test.log"
        # Clear any existing handlers from previous tests
        root = logging.getLogger("trading_bot")
        root.handlers.clear()

        logger = configure_logging(log_path)
        # Should have exactly a file handler + a console handler
        assert len(logger.handlers) == 2

    def test_idempotent_when_called_twice(self, tmp_path: Path) -> None:
        log_path = tmp_path / "test.log"
        root = logging.getLogger("trading_bot")
        root.handlers.clear()

        logger1 = configure_logging(log_path)
        handler_count = len(logger1.handlers)
        logger2 = configure_logging(log_path)
        # Should not add duplicate handlers
        assert len(logger2.handlers) == handler_count

    def test_sets_level(self, tmp_path: Path) -> None:
        log_path = tmp_path / "test.log"
        root = logging.getLogger("trading_bot")
        root.handlers.clear()

        logger = configure_logging(log_path, level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_propagate_is_false(self, tmp_path: Path) -> None:
        log_path = tmp_path / "test.log"
        root = logging.getLogger("trading_bot")
        root.handlers.clear()

        logger = configure_logging(log_path)
        assert logger.propagate is False


class TestGetLogger:
    def test_returns_child_logger(self) -> None:
        logger = get_logger("mymodule")
        assert logger.name == "trading_bot.mymodule"

    def test_different_names_return_different_loggers(self) -> None:
        l1 = get_logger("a")
        l2 = get_logger("b")
        assert l1 is not l2
