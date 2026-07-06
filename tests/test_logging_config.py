"""Unit tests for Feature 6 logging configuration."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

import bot.logging_config as logging_config_module
from bot.logging_config import setup_logging


@pytest.fixture(autouse=True)
def reset_logging_state() -> None:
    """Allow setup_logging to run fresh in each test."""
    logging_config_module._CONFIGURED = False
    root = logging.getLogger()
    root.handlers.clear()
    yield
    root.handlers.clear()
    logging_config_module._CONFIGURED = False


def test_file_handler_logs_debug(tmp_path: Path) -> None:
    setup_logging(tmp_path, log_level="INFO")
    root = logging.getLogger()
    file_handlers = [h for h in root.handlers if h.level == logging.DEBUG]
    assert len(file_handlers) >= 1

    test_logger = logging.getLogger("test.feature6")
    test_logger.debug("debug-only-message")
    log_text = (tmp_path / "trading_bot.log").read_text(encoding="utf-8")
    assert "debug-only-message" in log_text


def test_console_handler_respects_info_level(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    setup_logging(tmp_path, log_level="INFO")
    test_logger = logging.getLogger("test.feature6.console")
    test_logger.debug("should-not-appear-on-console")
    test_logger.info("should-appear-on-console")

    captured = capsys.readouterr()
    assert "should-not-appear-on-console" not in captured.err
    assert "should-not-appear-on-console" not in captured.out
    assert "should-appear-on-console" in captured.err or "should-appear-on-console" in captured.out


def test_console_shows_debug_when_log_level_debug(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    setup_logging(tmp_path, log_level="DEBUG")
    test_logger = logging.getLogger("test.feature6.debug")
    test_logger.debug("debug-on-console-too")

    captured = capsys.readouterr()
    assert "debug-on-console-too" in captured.err or "debug-on-console-too" in captured.out
