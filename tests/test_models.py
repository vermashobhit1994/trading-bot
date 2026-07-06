"""Unit tests for Feature 3 order models."""

from __future__ import annotations

from decimal import Decimal

import pytest

from bot.models import OrderRequest, OrderResponse, OrderType, Side, TimeInForce


class TestOrderRequest:
    def test_market_api_params(self) -> None:
        order = OrderRequest(
            symbol="BTCUSDT",
            side=Side.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.001"),
        )
        params = order.to_api_params()
        assert params == {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "quantity": "0.001",
            "newOrderRespType": "RESULT",
        }

    def test_limit_api_params(self) -> None:
        order = OrderRequest(
            symbol="BTCUSDT",
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.001"),
            price=Decimal("95000"),
            time_in_force=TimeInForce.GTC,
        )
        params = order.to_api_params()
        assert params["type"] == "LIMIT"
        assert params["price"] == "95000"
        assert params["timeInForce"] == "GTC"


class TestOrderResponse:
    def test_from_api_filled_market(self) -> None:
        response = OrderResponse.from_api(
            {
                "orderId": 19505693006,
                "symbol": "BTCUSDT",
                "status": "FILLED",
                "executedQty": "0.0010",
                "avgPrice": "97234.50",
                "side": "BUY",
                "type": "MARKET",
            }
        )
        assert response.order_id == 19505693006
        assert response.status == "FILLED"
        assert response.executed_qty == Decimal("0.0010")
        assert response.avg_price == Decimal("97234.50")

    def test_from_api_null_avg_price(self) -> None:
        response = OrderResponse.from_api(
            {
                "orderId": 19505693006,
                "symbol": "BTCUSDT",
                "status": "FILLED",
                "executedQty": "0.0010",
                "avgPrice": None,
                "side": "BUY",
                "type": "MARKET",
            }
        )
        assert response.avg_price is None

    def test_from_api_avg_price_from_cum_quote(self) -> None:
        response = OrderResponse.from_api(
            {
                "orderId": 1,
                "symbol": "BTCUSDT",
                "status": "FILLED",
                "executedQty": "0.001",
                "avgPrice": "0",
                "cumQuote": "97.2345",
                "side": "BUY",
                "type": "MARKET",
            }
        )
        assert response.avg_price == Decimal("97234.5")
