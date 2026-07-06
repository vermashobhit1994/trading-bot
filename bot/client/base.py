"""Shared constants for Binance USDT-M Futures REST endpoints."""

from __future__ import annotations

from dataclasses import dataclass

PING_ENDPOINT = "/fapi/v1/ping"
TIME_ENDPOINT = "/fapi/v1/time"
EXCHANGE_INFO_ENDPOINT = "/fapi/v1/exchangeInfo"
ORDER_ENDPOINT = "/fapi/v1/order"
ORDER_TEST_ENDPOINT = "/fapi/v1/order/test"


@dataclass(frozen=True)
class FuturesEndpoints:
    """REST path constants for the USDT-M Futures API."""

    ping: str = PING_ENDPOINT
    time: str = TIME_ENDPOINT
    exchange_info: str = EXCHANGE_INFO_ENDPOINT
    order: str = ORDER_ENDPOINT
    order_test: str = ORDER_TEST_ENDPOINT
