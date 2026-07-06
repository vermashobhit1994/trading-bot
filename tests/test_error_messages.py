"""Unit tests for Binance API error message formatting."""

from __future__ import annotations

import pytest

from bot.error_messages import (
    format_binance_api_error,
    format_network_error,
)
from bot.exceptions import BinanceAPIError, NetworkError


class TestFormatBinanceApiError:
    def test_known_code_includes_hint(self) -> None:
        exc = BinanceAPIError(-1111, "Precision is over the maximum defined for this asset.")
        message = format_binance_api_error(exc)
        assert "Binance API error -1111" in message
        assert "Precision error" in message

    def test_margin_error_hint(self) -> None:
        exc = BinanceAPIError(-2019, "Margin is insufficient.")
        assert "Insufficient margin" in format_binance_api_error(exc)

    def test_signature_error_hint(self) -> None:
        exc = BinanceAPIError(-1022, "Signature for this request is not valid.")
        assert "Invalid signature" in format_binance_api_error(exc)

    def test_unknown_code_no_extra_hint(self) -> None:
        exc = BinanceAPIError(-9999, "Unknown error.")
        message = format_binance_api_error(exc)
        assert message == "Binance API error -9999: Unknown error."

    @pytest.mark.parametrize(
        ("code", "snippet"),
        [
            (-4164, "notional"),
            (-1021, "recvWindow"),
            (-2015, "Invalid API key"),
            (-1102, "invalid parameter"),
        ],
    )
    def test_mapped_codes_include_hints(self, code: int, snippet: str) -> None:
        exc = BinanceAPIError(code, "API message")
        assert snippet.lower() in format_binance_api_error(exc).lower()


class TestFormatNetworkError:
    def test_includes_network_hint(self) -> None:
        exc = NetworkError("Connection timed out")
        message = format_network_error(exc)
        assert "Connection timed out" in message
        assert "Network failure" in message
