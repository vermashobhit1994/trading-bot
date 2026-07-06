"""Optional live smoke test (require .env and network)."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()


@pytest.mark.integration
def test_live_smoke_test_cli() -> None:
    result = runner.invoke(app, ["smoke_test"])
    assert result.exit_code == 0
    assert "Smoke test completed successfully." in result.stdout
    assert "[PASS] ping" in result.stdout
    assert "[PASS] dry_run_market_order" in result.stdout
