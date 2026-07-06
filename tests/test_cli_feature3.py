"""CLI tests for Feature 3 validate_order and order commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from cli.main import app
from tests.conftest import BTCUSDT_EXCHANGE_INFO

runner = CliRunner()


def _combined_output(result) -> str:
    return f"{result.stdout}\n{result.stderr}"


def _mock_settings() -> MagicMock:
    settings = MagicMock()
    settings.log_dir = MagicMock()
    settings.log_level = "INFO"
    return settings


def _mock_client_context() -> MagicMock:
    client = MagicMock()
    client.get_exchange_info.return_value = BTCUSDT_EXCHANGE_INFO
    client.__enter__.return_value = client
    client.__exit__.return_value = False
    return client


@patch("cli.main.setup_logging")
@patch("cli.main.load_settings", return_value=_mock_settings())
@patch("cli.main.create_client")
class TestValidateOrderCLI:
    def test_valid_market_order(self, mock_create_client, _mock_settings, _logging) -> None:
        mock_create_client.return_value = _mock_client_context()
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
        assert "=== Order Request ===" in result.stdout
        assert "Order validation passed." in result.stdout

    def test_invalid_symbol(self, mock_create_client, _mock_settings, _logging) -> None:
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
        assert "Validation error:" in _combined_output(result)
        mock_create_client.assert_not_called()

    def test_limit_missing_price(self, mock_create_client, _mock_settings, _logging) -> None:
        result = runner.invoke(
            app,
            [
                "validate_order",
                "--symbol",
                "BTCUSDT",
                "--side",
                "BUY",
                "--type",
                "LIMIT",
                "--quantity",
                "0.001",
            ],
        )
        assert result.exit_code == 1
        assert "Price is required" in _combined_output(result)

    def test_market_with_price_rejected(self, mock_create_client, _mock_settings, _logging) -> None:
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
                "--price",
                "90000",
            ],
        )
        assert result.exit_code == 1
        assert "must not be provided" in _combined_output(result)


@patch("cli.main.setup_logging")
@patch("cli.main.load_settings", return_value=_mock_settings())
@patch("cli.main.create_client")
@patch("cli.main.test_order")
class TestOrderDryRunCLI:
    def test_dry_run_success(
        self,
        mock_test_order,
        mock_create_client,
        _mock_settings,
        _logging,
    ) -> None:
        mock_create_client.return_value = _mock_client_context()
        mock_test_order.return_value = {"orderId": 0}
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
        mock_test_order.assert_called_once()
