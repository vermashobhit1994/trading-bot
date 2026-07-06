"""Domain models and enums shared across the application."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class TimeInForce(str, Enum):
    GTC = "GTC"


@dataclass(frozen=True)
class OrderRequest:
    """Validated order input ready to be sent to the exchange."""

    symbol: str
    side: Side
    order_type: OrderType
    quantity: Decimal
    price: Decimal | None = None
    time_in_force: TimeInForce = TimeInForce.GTC

    def to_api_params(self) -> dict[str, str]:
        """Convert the order into Binance Futures API parameters."""
        params: dict[str, str] = {
            "symbol": self.symbol,
            "side": self.side.value,
            "type": self.order_type.value,
            "quantity": format_decimal(self.quantity),
            "newOrderRespType": "RESULT",
        }
        if self.order_type is OrderType.LIMIT:
            if self.price is None:
                raise ValueError("LIMIT orders require a price.")
            params["price"] = format_decimal(self.price)
            params["timeInForce"] = self.time_in_force.value
        return params


@dataclass(frozen=True)
class OrderResponse:
    """Normalized order response from Binance."""

    order_id: int
    status: str
    executed_qty: Decimal
    avg_price: Decimal | None
    symbol: str
    side: str
    order_type: str
    raw: dict[str, Any]

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> OrderResponse:
        executed_qty = Decimal(str(payload.get("executedQty", "0")))
        avg_price_raw = payload.get("avgPrice")
        avg_price = None
        if avg_price_raw not in (None, "", "0", "0.0", "0.00", "0.00000"):
            avg_price = Decimal(str(avg_price_raw))
        elif executed_qty > 0:
            cum_quote = payload.get("cumQuote")
            if cum_quote not in (None, "", "0", "0.0", "0.00"):
                avg_price = Decimal(str(cum_quote)) / executed_qty

        return cls(
            order_id=int(payload["orderId"]),
            status=str(payload.get("status", "UNKNOWN")),
            executed_qty=executed_qty,
            avg_price=avg_price,
            symbol=str(payload.get("symbol", "")),
            side=str(payload.get("side", "")),
            order_type=str(payload.get("type", "")),
            raw=payload,
        )

    def is_success(self) -> bool:
        """Return True when Binance accepted the order in a tradable state."""
        return self.status in {"FILLED", "NEW", "PARTIALLY_FILLED"}


def format_decimal(value: Decimal) -> str:
    """Format a Decimal without scientific notation for the API."""
    normalized = value.normalize()
    return format(normalized, "f")
