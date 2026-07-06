"""User-friendly messages for Binance API and network errors."""

from __future__ import annotations

from bot.exceptions import BinanceAPIError, NetworkError

# Common USDT-M Futures error codes — see Binance error-code docs.
BINANCE_ERROR_HINTS: dict[int, str] = {
    -1111: "Precision error — adjust quantity or price to match the symbol step/tick size.",
    -2019: "Insufficient margin — add demo funds or reduce order size.",
    -4164: "Order notional below minimum — increase quantity or price.",
    -1021: "Timestamp outside recvWindow — sync your system clock or increase RECV_WINDOW.",
    -1022: "Invalid signature — verify SECRET_KEY in .env matches your API key.",
    -2015: "Invalid API key — use Demo Trading keys for demo-fapi, mainnet keys for fapi.",
    -1102: "Missing or invalid parameter — check symbol, side, type, quantity, and price.",
    -4046: "No need to change position side — account is already in the requested mode.",
}

NETWORK_ERROR_HINT = (
    "Network failure — check internet access and that BINANCE_FUTURES_BASE_URL is reachable."
)


def format_binance_api_error(exc: BinanceAPIError) -> str:
    """Return a CLI-friendly Binance API error message with an actionable hint."""
    hint = BINANCE_ERROR_HINTS.get(exc.code)
    base = f"Binance API error {exc.code}: {exc.message}"
    if hint:
        return f"{base}. {hint}"
    return base


def format_network_error(exc: NetworkError) -> str:
    """Return a CLI-friendly network error message."""
    return f"Network error: {exc}. {NETWORK_ERROR_HINT}"
