"""Order placement and presentation logic."""

from __future__ import annotations

import logging
from typing import Any

from bot.client.base import ORDER_ENDPOINT, ORDER_TEST_ENDPOINT
from bot.client.futures import BinanceFuturesClient
from bot.models import OrderRequest, OrderResponse
from bot.validators import SymbolFilters, validate_against_exchange_filters

logger = logging.getLogger(__name__)


def validate_order_with_exchange(
    client: BinanceFuturesClient,
    order: OrderRequest,
) -> SymbolFilters:
    """Fetch exchange info and validate the order against symbol filters."""
    exchange_info = client.get_exchange_info(order.symbol)
    filters = SymbolFilters.from_exchange_info(order.symbol, exchange_info)
    validate_against_exchange_filters(order, filters)
    return filters


def test_order(client: BinanceFuturesClient, order: OrderRequest) -> dict[str, Any]:
    """Validate an order with Binance without placing it."""
    validate_order_with_exchange(client, order)
    params = order.to_api_params()
    logger.info("Order dry-run request:\n%s", format_request_summary(order))
    logger.debug("Dry-run API params: %s", params)
    response = client.send_signed_request("POST", ORDER_TEST_ENDPOINT, params=params)
    if not isinstance(response, dict):
        raise ValueError("Unexpected test order response format.")
    logger.info("Dry-run accepted by Binance for %s %s %s", order.symbol, order.side.value, order.order_type.value)
    return response


def place_order(client: BinanceFuturesClient, order: OrderRequest) -> OrderResponse:
    """Place a MARKET or LIMIT order on Binance Futures."""
    validate_order_with_exchange(client, order)
    params = order.to_api_params()
    logger.info("Order submit request:\n%s", format_request_summary(order))
    logger.debug("Order API params: %s", params)
    response = client.send_signed_request("POST", ORDER_ENDPOINT, params=params)
    if not isinstance(response, dict):
        raise ValueError("Unexpected order response format.")
    result = OrderResponse.from_api(response)
    logger.info("Order submit response:\n%s", format_response_summary(result))
    logger.debug("Order raw API response: %s", response)
    return result


def format_request_summary(order: OrderRequest) -> str:
    """Build a human-readable order request summary."""
    lines = [
        "=== Order Request ===",
        f"Symbol:   {order.symbol}",
        f"Side:     {order.side.value}",
        f"Type:     {order.order_type.value}",
        f"Quantity: {order.quantity}",
    ]
    if order.order_type.value == "LIMIT" and order.price is not None:
        lines.append(f"Price:    {order.price}")
    return "\n".join(lines)


def format_response_summary(response: OrderResponse) -> str:
    """Build a human-readable order response summary."""
    lines = [
        "=== Order Response ===",
        f"Order ID:     {response.order_id}",
        f"Status:       {response.status}",
        f"Executed Qty: {response.executed_qty}",
    ]
    if response.avg_price is not None:
        lines.append(f"Avg Price:    {response.avg_price}")
    else:
        lines.append("Avg Price:    n/a")
    return "\n".join(lines)


def format_result_message(response: OrderResponse) -> str:
    """Return a final success or failure message for CLI output."""
    if response.is_success():
        if response.status == "FILLED":
            return "Order placed and filled successfully."
        if response.status == "NEW":
            return "Limit order placed successfully and is open on the book."
        return "Order placed successfully (partially filled)."
    return f"Order failed or was rejected. Status: {response.status}"
