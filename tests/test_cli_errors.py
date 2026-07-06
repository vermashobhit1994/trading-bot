"""CLI tests for Feature 7 friendly error messages."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from bot.exceptions import BinanceAPIError, NetworkError
from cli.main import app

runner = CliRunner()


def _combined_output(result) -> str:
    return f"{result.stdout}\n{result.stderr}"


def _mock_settings() -> MagicMock:
    settings = MagicMock()
    settings.log_dir = MagicMock()
    settings.log_level = "INFO"
    settings.is_mainnet = False
    settings.confirm_live_trading = False
    settings.base_url = "https://demo-fapi.binance.com"
    return settings


@patch("cli.main.setup_logging")
@patch("cli.main.load_settings", return_value=_mock_settings())
@patch("cli.main.create_client")
class TestCLIErrorMessages:
    def test_binance_api_error_shows_hint(
        self,
        mock_create_client: MagicMock,
        _mock_settings: MagicMock,
        _logging: MagicMock,
    ) -> None:
        client = MagicMock()
        client.test_auth = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        client.get_account_balance.side_effect = BinanceAPIError(
            -1022, "Signature for this request is not valid."
        )
        mock_create_client.return_value = client

        result = runner.invoke(app, ["test_auth"])
        assert result.exit_code == 2
        output = _combined_output(result)
        assert "Binance API error -1022" in output
        assert "Invalid signature" in output

    def test_margin_error_shows_hint_on_order(
        self,
        mock_create_client: MagicMock,
        _mock_settings: MagicMock,
        _logging: MagicMock,
    ) -> None:
        from tests.conftest import BTCUSDT_EXCHANGE_INFO

        client = MagicMock()
        client.get_exchange_info.return_value = BTCUSDT_EXCHANGE_INFO
        client.send_signed_request.side_effect = BinanceAPIError(-2019, "Margin is insufficient.")
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        mock_create_client.return_value = client

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
        assert result.exit_code == 2
        output = _combined_output(result)
        assert "Binance API error -2019" in output
        assert "Insufficient margin" in output

    def test_network_error_shows_hint(
        self,
        mock_create_client: MagicMock,
        _mock_settings: MagicMock,
        _logging: MagicMock,
    ) -> None:
        client = MagicMock()
        client.ping.side_effect = NetworkError("Connection timed out")
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        mock_create_client.return_value = client

        result = runner.invoke(app, ["ping"])
        assert result.exit_code == 2
        output = _combined_output(result)
        assert "Network error" in output
        assert "Network failure" in output
