"""Shared pytest fixtures."""

from __future__ import annotations

from decimal import Decimal

import pytest

from bot.validators import SymbolFilters

BTCUSDT_EXCHANGE_INFO = {
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


@pytest.fixture
def btcusdt_filters() -> SymbolFilters:
    return SymbolFilters(
        step_size=Decimal("0.001"),
        min_qty=Decimal("0.001"),
        max_qty=Decimal("1000"),
        tick_size=Decimal("0.01"),
        min_price=Decimal("0.01"),
        max_price=Decimal("1000000"),
        min_notional=Decimal("5"),
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: tests that call the live Binance demo API",
    )
