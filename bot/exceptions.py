"""Application-specific exceptions."""


class TradingBotError(Exception):
    """Base exception for all trading-bot errors."""


class ConfigurationError(TradingBotError):
    """Raised when configuration or environment variables are invalid."""


class ValidationError(TradingBotError):
    """Raised when user input fails validation."""


class BinanceAPIError(TradingBotError):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class NetworkError(TradingBotError):
    """Raised on HTTP timeouts, connection failures, or malformed responses."""
