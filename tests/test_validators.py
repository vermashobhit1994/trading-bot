"""Unit tests for Feature 3 input validation."""

from __future__ import annotations

from decimal import Decimal

import pytest

from bot.exceptions import ValidationError
from bot.models import OrderType, Side
from bot.validators import (
    SymbolFilters,
    build_order_request,
    parse_order_type,
    parse_side,
    parse_symbol,
    validate_against_exchange_filters,
)
from tests.conftest import BTCUSDT_EXCHANGE_INFO


class TestParseSymbol:
    def test_accepts_btcusdt(self) -> None:
        assert parse_symbol("btcusdt") == "BTCUSDT"

    def test_rejects_invalid_symbol(self) -> None:
        with pytest.raises(ValidationError, match="Invalid symbol"):
            parse_symbol("INVALID")


class TestParseSide:
    def test_accepts_buy_and_sell(self) -> None:
        assert parse_side("buy") == Side.BUY
        assert parse_side("SELL") == Side.SELL

    def test_rejects_invalid_side(self) -> None:
        with pytest.raises(ValidationError, match="Invalid side"):
            parse_side("HOLD")


class TestParseOrderType:
    def test_accepts_market_and_limit(self) -> None:
        assert parse_order_type("market") == OrderType.MARKET
        assert parse_order_type("LIMIT") == OrderType.LIMIT

    def test_rejects_invalid_type(self) -> None:
        with pytest.raises(ValidationError, match="Invalid order type"):
            parse_order_type("STOP")


class TestBuildOrderRequest:
    def test_valid_market_order(self) -> None:
        order = build_order_request(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity="0.001",
        )
        assert order.symbol == "BTCUSDT"
        assert order.side is Side.BUY
        assert order.order_type is OrderType.MARKET
        assert order.quantity == Decimal("0.001")
        assert order.price is None

    def test_valid_limit_order(self) -> None:
        order = build_order_request(
            symbol="BTCUSDT",
            side="SELL",
            order_type="LIMIT",
            quantity="0.001",
            price="95000",
        )
        assert order.order_type is OrderType.LIMIT
        assert order.price == Decimal("95000")

    def test_limit_requires_price(self) -> None:
        with pytest.raises(ValidationError, match="Price is required"):
            build_order_request(
                symbol="BTCUSDT",
                side="BUY",
                order_type="LIMIT",
                quantity="0.001",
            )

    def test_market_rejects_price(self) -> None:
        with pytest.raises(ValidationError, match="must not be provided"):
            build_order_request(
                symbol="BTCUSDT",
                side="BUY",
                order_type="MARKET",
                quantity="0.001",
                price="90000",
            )

    def test_rejects_non_positive_quantity(self) -> None:
        with pytest.raises(ValidationError, match="greater than zero"):
            build_order_request(
                symbol="BTCUSDT",
                side="BUY",
                order_type="MARKET",
                quantity="-1",
            )


class TestExchangeFilters:
    def test_parses_btcusdt_filters(self) -> None:
        filters = SymbolFilters.from_exchange_info("BTCUSDT", BTCUSDT_EXCHANGE_INFO)
        assert filters.min_qty == Decimal("0.001")
        assert filters.step_size == Decimal("0.001")

    def test_valid_quantity_passes(self, btcusdt_filters: SymbolFilters) -> None:
        order = build_order_request(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity="0.001",
        )
        validate_against_exchange_filters(order, btcusdt_filters)

    def test_quantity_below_minimum_fails(self, btcusdt_filters: SymbolFilters) -> None:
        order = build_order_request(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity="0.0001",
        )
        with pytest.raises(ValidationError, match="below minimum"):
            validate_against_exchange_filters(order, btcusdt_filters)

    def test_quantity_step_mismatch_fails(self, btcusdt_filters: SymbolFilters) -> None:
        order = build_order_request(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity="0.0015",
        )
        with pytest.raises(ValidationError, match="step size"):
            validate_against_exchange_filters(order, btcusdt_filters)

    def test_limit_notional_below_minimum_fails(self, btcusdt_filters: SymbolFilters) -> None:
        order = build_order_request(
            symbol="BTCUSDT",
            side="BUY",
            order_type="LIMIT",
            quantity="0.001",
            price="1",
        )
        with pytest.raises(ValidationError, match="notional"):
            validate_against_exchange_filters(order, btcusdt_filters)
