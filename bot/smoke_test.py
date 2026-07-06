"""End-to-end smoke test steps for demo/testnet connectivity and order flow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from bot.client.futures import BinanceFuturesClient
from bot.exceptions import BinanceAPIError, NetworkError, ValidationError
from bot.models import OrderType, Side
from bot.orders import test_order, validate_order_with_exchange
from bot.validators import build_order_request


@dataclass(frozen=True)
class SmokeStepResult:
    """Outcome of a single smoke test step."""

    name: str
    passed: bool
    detail: str


def run_smoke_test(client: BinanceFuturesClient) -> list[SmokeStepResult]:
    """Run connectivity, auth, validation, and dry-run order checks."""
    results: list[SmokeStepResult] = []

    def _run(name: str, fn: Callable[[], str]) -> None:
        try:
            detail = fn()
            results.append(SmokeStepResult(name=name, passed=True, detail=detail))
        except Exception as exc:
            results.append(SmokeStepResult(name=name, passed=False, detail=str(exc)))

    _run("ping", lambda: _step_ping(client))
    _run("server_time", lambda: _step_server_time(client))
    _run("test_auth", lambda: _step_test_auth(client))
    _run("validate_market_order", lambda: _step_validate_market(client))
    _run("dry_run_market_order", lambda: _step_dry_run_market(client))
    _run("dry_run_limit_order", lambda: _step_dry_run_limit(client))

    return results


def _step_ping(client: BinanceFuturesClient) -> str:
    client.ping()
    return "Public API reachable."


def _step_server_time(client: BinanceFuturesClient) -> str:
    payload = client.get_server_time()
    server_time = payload.get("serverTime")
    return f"Server time: {server_time}"


def _step_test_auth(client: BinanceFuturesClient) -> str:
    balances = client.get_account_balance()
    non_zero = [
        b
        for b in balances
        if float(b.get("balance", 0)) != 0.0 or float(b.get("availableBalance", 0)) != 0.0
    ]
    return f"Signed auth OK ({len(non_zero)} non-zero assets)."


def _step_validate_market(client: BinanceFuturesClient) -> str:
    order = build_order_request(
        symbol="BTCUSDT",
        side=Side.BUY.value,
        order_type=OrderType.MARKET.value,
        quantity="0.001",
    )
    validate_order_with_exchange(client, order)
    return "BTCUSDT MARKET BUY 0.001 passed exchange filter validation."


def _step_dry_run_market(client: BinanceFuturesClient) -> str:
    order = build_order_request(
        symbol="BTCUSDT",
        side=Side.BUY.value,
        order_type=OrderType.MARKET.value,
        quantity="0.001",
    )
    test_order(client, order)
    return "MARKET dry-run accepted by Binance."


def _step_dry_run_limit(client: BinanceFuturesClient) -> str:
    order = build_order_request(
        symbol="BTCUSDT",
        side=Side.BUY.value,
        order_type=OrderType.LIMIT.value,
        quantity="0.001",
        price="50000",
    )
    test_order(client, order)
    return "LIMIT dry-run accepted by Binance."
