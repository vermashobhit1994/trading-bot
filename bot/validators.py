"""Input validation for CLI order parameters."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from bot.exceptions import ValidationError
from bot.models import OrderRequest, OrderType, Side

SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{1,20}USDT$")


@dataclass(frozen=True)
class SymbolFilters:
    """Exchange filter rules for a single futures symbol."""

    step_size: Decimal
    min_qty: Decimal
    max_qty: Decimal
    tick_size: Decimal
    min_price: Decimal
    max_price: Decimal
    min_notional: Decimal | None = None

    @classmethod
    def from_exchange_info(cls, symbol: str, exchange_info: dict[str, Any]) -> SymbolFilters:
        symbols = exchange_info.get("symbols", [])
        symbol_data = next(
            (item for item in symbols if item.get("symbol") == symbol.upper()),
            None,
        )
        if symbol_data is None:
            raise ValidationError(f"Symbol '{symbol}' is not listed on this exchange.")

        filters = {item["filterType"]: item for item in symbol_data.get("filters", [])}
        lot_size = filters.get("LOT_SIZE", {})
        price_filter = filters.get("PRICE_FILTER", {})
        min_notional_filter = filters.get("MIN_NOTIONAL") or filters.get("NOTIONAL")

        return cls(
            step_size=Decimal(str(lot_size.get("stepSize", "0"))),
            min_qty=Decimal(str(lot_size.get("minQty", "0"))),
            max_qty=Decimal(str(lot_size.get("maxQty", "0"))),
            tick_size=Decimal(str(price_filter.get("tickSize", "0"))),
            min_price=Decimal(str(price_filter.get("minPrice", "0"))),
            max_price=Decimal(str(price_filter.get("maxPrice", "0"))),
            min_notional=(
                Decimal(str(min_notional_filter.get("notional")))
                if min_notional_filter and min_notional_filter.get("notional") is not None
                else None
            ),
        )


def parse_side(value: str) -> Side:
    normalized = value.strip().upper()
    try:
        return Side(normalized)
    except ValueError as exc:
        raise ValidationError(f"Invalid side '{value}'. Expected BUY or SELL.") from exc


def parse_order_type(value: str) -> OrderType:
    normalized = value.strip().upper()
    try:
        return OrderType(normalized)
    except ValueError as exc:
        raise ValidationError(f"Invalid order type '{value}'. Expected MARKET or LIMIT.") from exc


def parse_symbol(value: str) -> str:
    symbol = value.strip().upper()
    if not SYMBOL_PATTERN.match(symbol):
        raise ValidationError(
            f"Invalid symbol '{value}'. Expected a USDT-M symbol like BTCUSDT."
        )
    return symbol


def parse_positive_decimal(name: str, value: str) -> Decimal:
    raw = value.strip()
    try:
        decimal_value = Decimal(raw)
    except InvalidOperation as exc:
        raise ValidationError(f"Invalid {name} '{value}'. Must be a positive number.") from exc

    if decimal_value <= 0:
        raise ValidationError(f"{name.capitalize()} must be greater than zero.")
    return decimal_value


def build_order_request(
    *,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None = None,
) -> OrderRequest:
    """Validate raw CLI strings and build an OrderRequest."""
    parsed_symbol = parse_symbol(symbol)
    parsed_side = parse_side(side)
    parsed_type = parse_order_type(order_type)
    parsed_quantity = parse_positive_decimal("quantity", quantity)

    parsed_price: Decimal | None = None
    if parsed_type is OrderType.LIMIT:
        if price is None or not price.strip():
            raise ValidationError("Price is required for LIMIT orders.")
        parsed_price = parse_positive_decimal("price", price)
    elif price is not None and price.strip():
        raise ValidationError("Price must not be provided for MARKET orders.")

    return OrderRequest(
        symbol=parsed_symbol,
        side=parsed_side,
        order_type=parsed_type,
        quantity=parsed_quantity,
        price=parsed_price,
    )


def validate_against_exchange_filters(
    order: OrderRequest,
    filters: SymbolFilters,
) -> None:
    """Validate quantity and price against exchange filter rules."""
    if order.quantity < filters.min_qty:
        raise ValidationError(
            f"Quantity {order.quantity} is below minimum {filters.min_qty} for {order.symbol}."
        )
    if order.quantity > filters.max_qty:
        raise ValidationError(
            f"Quantity {order.quantity} exceeds maximum {filters.max_qty} for {order.symbol}."
        )
    if not _is_step_aligned(order.quantity, filters.step_size):
        raise ValidationError(
            f"Quantity {order.quantity} does not match step size {filters.step_size}."
        )

    if order.order_type is OrderType.LIMIT and order.price is not None:
        if order.price < filters.min_price:
            raise ValidationError(
                f"Price {order.price} is below minimum {filters.min_price} for {order.symbol}."
            )
        if order.price > filters.max_price:
            raise ValidationError(
                f"Price {order.price} exceeds maximum {filters.max_price} for {order.symbol}."
            )
        if not _is_step_aligned(order.price, filters.tick_size):
            raise ValidationError(
                f"Price {order.price} does not match tick size {filters.tick_size}."
            )
        if filters.min_notional is not None:
            notional = order.quantity * order.price
            if notional < filters.min_notional:
                raise ValidationError(
                    f"Order notional {notional} is below minimum {filters.min_notional}."
                )


def _is_step_aligned(value: Decimal, step: Decimal) -> bool:
    if step <= 0:
        return True
    remainder = value % step
    return remainder == 0
