"""Unit tests for smoke test runner."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from bot.smoke_test import run_smoke_test


def _mock_client() -> MagicMock:
    client = MagicMock()
    client.ping.return_value = {}
    client.get_server_time.return_value = {"serverTime": 1700000000000}
    client.get_account_balance.return_value = [
        {"asset": "USDT", "balance": "5000", "availableBalance": "5000"},
    ]
    client.get_exchange_info.return_value = {
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "filters": [
                    {
                        "filterType": "LOT_SIZE",
                        "minQty": "0.001",
                        "maxQty": "1000",
                        "stepSize": "0.001",
                    },
                    {
                        "filterType": "PRICE_FILTER",
                        "minPrice": "0.01",
                        "maxPrice": "1000000",
                        "tickSize": "0.01",
                    },
                    {"filterType": "MIN_NOTIONAL", "notional": "5"},
                ],
            }
        ]
    }
    client.send_signed_request.return_value = {}
    return client


class TestSmokeTest:
    @patch("bot.smoke_test.test_order", return_value={})
    def test_all_steps_pass(self, _mock_test_order: MagicMock) -> None:
        results = run_smoke_test(_mock_client())
        assert len(results) == 6
        assert all(step.passed for step in results)

    def test_ping_failure_stops_step_only(self) -> None:
        client = _mock_client()
        client.ping.side_effect = Exception("down")
        results = run_smoke_test(client)
        assert results[0].passed is False
        assert "down" in results[0].detail
