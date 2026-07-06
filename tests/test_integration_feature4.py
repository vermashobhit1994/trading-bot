"""Optional live API tests for Feature 4 order placement (require .env and network)."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()


@pytest.mark.integration
def test_live_market_order_dry_run() -> None:
    """POST /fapi/v1/order/test — MARKET BUY BTCUSDT 0.001."""
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
    assert "=== Order Request ===" in result.stdout
    assert "Dry run successful." in result.stdout


@pytest.mark.integration
def test_live_limit_order_dry_run() -> None:
    """POST /fapi/v1/order/test — LIMIT SELL far above market (should validate only)."""
    result = runner.invoke(
        app,
        [
            "order",
            "--symbol",
            "BTCUSDT",
            "--side",
            "SELL",
            "--type",
            "LIMIT",
            "--quantity",
            "0.001",
            "--price",
            "200000",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert "Price:    200000" in result.stdout
    assert "Dry run successful." in result.stdout


@pytest.mark.integration
def test_live_market_sell_dry_run() -> None:
    """POST /fapi/v1/order/test — MARKET SELL."""
    result = runner.invoke(
        app,
        [
            "order",
            "--symbol",
            "BTCUSDT",
            "--side",
            "SELL",
            "--type",
            "MARKET",
            "--quantity",
            "0.001",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert "Side:     SELL" in result.stdout
