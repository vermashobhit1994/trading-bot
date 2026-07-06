"""Unit tests for Feature 4 order placement (bot/orders.py)."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from bot.client.base import ORDER_ENDPOINT, ORDER_TEST_ENDPOINT
from bot.exceptions import ValidationError
from bot.models import OrderRequest, OrderResponse, OrderType, Side
from bot.orders import (
    format_request_summary,
    format_response_summary,
    format_result_message,
    place_order,
    test_order as submit_test_order,
    validate_order_with_exchange,
)
from tests.conftest import BTCUSDT_EXCHANGE_INFO


def _market_order() -> OrderRequest:
    return OrderRequest(
        symbol="BTCUSDT",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("0.001"),
    )


def _limit_order() -> OrderRequest:
    return OrderRequest(
        symbol="BTCUSDT",
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        quantity=Decimal("0.001"),
        price=Decimal("120000"),
    )


def _mock_client() -> MagicMock:
    client = MagicMock()
    client.get_exchange_info.return_value = BTCUSDT_EXCHANGE_INFO
    return client


class TestValidateOrderWithExchange:
    def test_valid_market_order_passes(self) -> None:
        client = _mock_client()
        validate_order_with_exchange(client, _market_order())
        client.get_exchange_info.assert_called_once_with("BTCUSDT")

    def test_invalid_step_size_raises(self) -> None:
        client = _mock_client()
        bad_order = OrderRequest(
            symbol="BTCUSDT",
            side=Side.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.0015"),
        )
        with pytest.raises(ValidationError, match="step size"):
            validate_order_with_exchange(client, bad_order)


class TestTestOrder:
    def test_calls_test_endpoint_with_params(self) -> None:
        client = _mock_client()
        client.send_signed_request.return_value = {}
        order = _market_order()
        result = submit_test_order(client, order)
        client.send_signed_request.assert_called_once_with(
            "POST",
            ORDER_TEST_ENDPOINT,
            params=order.to_api_params(),
        )
        assert result == {}

    def test_rejects_non_dict_response(self) -> None:
        client = _mock_client()
        client.send_signed_request.return_value = []
        with pytest.raises(ValueError, match="Unexpected test order response"):
            submit_test_order(client, _market_order())


class TestPlaceOrder:
    def test_place_market_order_maps_response(self) -> None:
        client = _mock_client()
        client.send_signed_request.return_value = {
            "orderId": 19505693006,
            "symbol": "BTCUSDT",
            "status": "FILLED",
            "executedQty": "0.001",
            "avgPrice": "97234.50",
            "side": "BUY",
            "type": "MARKET",
        }
        order = _market_order()
        response = place_order(client, order)
        client.send_signed_request.assert_called_once_with(
            "POST",
            ORDER_ENDPOINT,
            params=order.to_api_params(),
        )
        assert response.order_id == 19505693006
        assert response.status == "FILLED"
        assert response.executed_qty == Decimal("0.001")
        assert response.avg_price == Decimal("97234.50")

    def test_place_limit_order_includes_price_and_tif(self) -> None:
        client = _mock_client()
        client.send_signed_request.return_value = {
            "orderId": 99,
            "symbol": "BTCUSDT",
            "status": "NEW",
            "executedQty": "0",
            "avgPrice": "0",
            "side": "SELL",
            "type": "LIMIT",
        }
        order = _limit_order()
        response = place_order(client, order)
        params = client.send_signed_request.call_args.kwargs["params"]
        assert params["type"] == "LIMIT"
        assert params["price"] == "120000"
        assert params["timeInForce"] == "GTC"
        assert params["newOrderRespType"] == "RESULT"
        assert response.status == "NEW"

    def test_rejects_non_dict_response(self) -> None:
        client = _mock_client()
        client.send_signed_request.return_value = "error"
        with pytest.raises(ValueError, match="Unexpected order response"):
            place_order(client, _market_order())


class TestFormatters:
    def test_format_request_summary_market(self) -> None:
        summary = format_request_summary(_market_order())
        assert "=== Order Request ===" in summary
        assert "Symbol:   BTCUSDT" in summary
        assert "Side:     BUY" in summary
        assert "Type:     MARKET" in summary
        assert "Quantity: 0.001" in summary
        assert "Price:" not in summary

    def test_format_request_summary_limit(self) -> None:
        summary = format_request_summary(_limit_order())
        assert "Price:    120000" in summary

    def test_format_response_summary_with_avg_price(self) -> None:
        response = OrderResponse(
            order_id=1,
            status="FILLED",
            executed_qty=Decimal("0.001"),
            avg_price=Decimal("95000"),
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            raw={},
        )
        summary = format_response_summary(response)
        assert "Order ID:     1" in summary
        assert "Status:       FILLED" in summary
        assert "Avg Price:    95000" in summary

    def test_format_response_summary_without_avg_price(self) -> None:
        response = OrderResponse(
            order_id=2,
            status="NEW",
            executed_qty=Decimal("0"),
            avg_price=None,
            symbol="BTCUSDT",
            side="SELL",
            order_type="LIMIT",
            raw={},
        )
        assert "Avg Price:    n/a" in format_response_summary(response)

    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            ("FILLED", "Order placed and filled successfully."),
            ("NEW", "Limit order placed successfully and is open on the book."),
            ("PARTIALLY_FILLED", "Order placed successfully (partially filled)."),
            ("REJECTED", "Order failed or was rejected. Status: REJECTED"),
        ],
    )
    def test_format_result_message(self, status: str, expected: str) -> None:
        response = OrderResponse(
            order_id=1,
            status=status,
            executed_qty=Decimal("0"),
            avg_price=None,
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            raw={},
        )
        assert format_result_message(response) == expected
