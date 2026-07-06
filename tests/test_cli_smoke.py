"""CLI tests for smoke_test command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from bot.smoke_test import SmokeStepResult
from cli.main import app

runner = CliRunner()


@patch("cli.main.setup_logging")
@patch("cli.main.load_settings")
@patch("cli.main.create_client")
@patch("cli.main.run_smoke_test")
class TestSmokeTestCLI:
    def test_smoke_test_success(
        self,
        mock_run_smoke: MagicMock,
        mock_create_client: MagicMock,
        mock_settings: MagicMock,
        _logging: MagicMock,
    ) -> None:
        mock_settings.return_value = MagicMock(base_url="https://demo-fapi.binance.com")
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        mock_create_client.return_value = client
        mock_run_smoke.return_value = [
            SmokeStepResult("ping", True, "ok"),
            SmokeStepResult("test_auth", True, "ok"),
        ]

        result = runner.invoke(app, ["smoke_test"])
        assert result.exit_code == 0
        assert "Smoke test completed successfully." in result.stdout
        assert "[PASS] ping" in result.stdout

    def test_smoke_test_partial_failure(
        self,
        mock_run_smoke: MagicMock,
        mock_create_client: MagicMock,
        mock_settings: MagicMock,
        _logging: MagicMock,
    ) -> None:
        mock_settings.return_value = MagicMock(base_url="https://demo-fapi.binance.com")
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        mock_create_client.return_value = client
        mock_run_smoke.return_value = [
            SmokeStepResult("ping", True, "ok"),
            SmokeStepResult("test_auth", False, "auth failed"),
        ]

        result = runner.invoke(app, ["smoke_test"])
        assert result.exit_code == 2
        assert "[FAIL] test_auth" in result.stdout
