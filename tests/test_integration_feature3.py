"""Optional live API tests for Feature 3 (require .env and network)."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()


@pytest.mark.integration
def test_live_validate_market_order() -> None:
    """Mirrors: cli.py validate_order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001"""
    result = runner.invoke(
        app,
        [
            "validate_order",
            "--symbol",
            "BTCUSDT",
            "--side",
            "BUY",
            "--type",
            "MARKET",
            "--quantity",
            "0.001",
        ],
    )
    assert result.exit_code == 0
    assert "Order validation passed." in result.stdout


@pytest.mark.integration
def test_live_order_dry_run() -> None:
    """Mirrors: cli.py order ... --dry-run"""
    result = runner.invoke(
        app,
        [
            "order",
            "--symbol",
            "BTCUSDT",
            "--side",
            "BUY",
            "--type",
            "MARKET",
            "--quantity",
            "0.001",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert "Dry run successful." in result.stdout


@pytest.mark.integration
def test_live_invalid_symbol() -> None:
    result = runner.invoke(
        app,
        [
            "validate_order",
            "--symbol",
            "INVALID",
            "--side",
            "BUY",
            "--type",
            "MARKET",
            "--quantity",
            "0.001",
        ],
    )
    assert result.exit_code == 1
    assert "Validation error:" in f"{result.stdout}\n{result.stderr}"
