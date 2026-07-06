"""Binance USDT-M Futures REST HTTP client."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from bot.client.base import (
    EXCHANGE_INFO_ENDPOINT,
    PING_ENDPOINT,
    TIME_ENDPOINT,
)
from bot.client.signer import build_query_string, get_timestamp_ms, sign_payload
from bot.config import Settings
from bot.exceptions import BinanceAPIError, NetworkError

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10.0
MAX_RETRIES = 2
ACCOUNT_BALANCE_ENDPOINT = "/fapi/v2/balance"
REDACTED = "***REDACTED***"


class BinanceFuturesClient:
    """HTTP client for Binance USDT-M Futures public and signed REST endpoints."""

    def __init__(
        self,
        settings: Settings,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self._settings = settings
        self._timeout = timeout
        self._max_retries = max_retries
        self._client = httpx.Client(
            base_url=settings.base_url,
            timeout=timeout,
            headers={"X-MBX-APIKEY": settings.api_key},
        )

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._client.close()

    def __enter__(self) -> BinanceFuturesClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def ping(self) -> dict[str, Any]:
        """Check API connectivity."""
        return self.send_public_request("GET", PING_ENDPOINT)

    def get_server_time(self) -> dict[str, Any]:
        """Fetch Binance server time."""
        return self.send_public_request("GET", TIME_ENDPOINT)

    def get_exchange_info(self, symbol: str | None = None) -> dict[str, Any]:
        """Fetch exchange rules; optionally filter by symbol."""
        params: dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol.upper()
        return self.send_public_request("GET", EXCHANGE_INFO_ENDPOINT, params=params)

    def get_account_balance(self) -> list[dict[str, Any]]:
        """Fetch futures wallet balances (signed; useful for auth smoke tests)."""
        response = self.send_signed_request("GET", ACCOUNT_BALANCE_ENDPOINT)
        if not isinstance(response, list):
            raise NetworkError("Unexpected account balance response format.")
        return response

    def send_public_request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send an unsigned market-data request."""
        return self._dispatch(method, endpoint, params=params or {}, signed=False)

    def send_signed_request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Send a signed USER_DATA or TRADE request."""
        return self._dispatch(method, endpoint, params=params or {}, signed=True)

    def _dispatch(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any],
        signed: bool,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        request_params = dict(params)
        if signed:
            request_params["timestamp"] = get_timestamp_ms()
            request_params["recvWindow"] = self._settings.recv_window
            query_string = build_query_string(request_params)
            signature = sign_payload(query_string, self._settings.api_secret)
            request_params["signature"] = signature
        else:
            query_string = build_query_string(request_params)

        log_params = self._redact_params(request_params)
        logger.debug(
            "API request (full) | %s %s | params=%s",
            method.upper(),
            endpoint,
            log_params,
        )
        logger.info(
            "API request | %s %s | params=%s",
            method.upper(),
            endpoint,
            log_params,
        )

        response = self._send_with_retries(
            method=method.upper(),
            endpoint=endpoint,
            params=request_params,
        )

        payload = self._parse_response(response)
        logger.debug(
            "API response (full) | %s %s | status=%s | body=%s",
            method.upper(),
            endpoint,
            response.status_code,
            self._full_payload(payload),
        )
        logger.info(
            "API response | %s %s | status=%s | body=%s",
            method.upper(),
            endpoint,
            response.status_code,
            self._summarize_payload(payload),
        )
        return payload

    def _send_with_retries(
        self,
        *,
        method: str,
        endpoint: str,
        params: dict[str, Any],
    ) -> httpx.Response:
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.request(method, endpoint, params=params)
                if response.status_code >= 500 and attempt < self._max_retries:
                    logger.warning(
                        "Server error %s on %s %s (attempt %s/%s)",
                        response.status_code,
                        method,
                        endpoint,
                        attempt + 1,
                        self._max_retries + 1,
                    )
                    continue
                return response
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                logger.warning(
                    "Network failure on %s %s (attempt %s/%s): %s",
                    method,
                    endpoint,
                    attempt + 1,
                    self._max_retries + 1,
                    exc,
                )

        raise NetworkError(
            f"Request failed after {self._max_retries + 1} attempts: {last_error}"
        ) from last_error

    def _parse_response(
        self,
        response: httpx.Response,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise NetworkError(
                f"Invalid JSON response (HTTP {response.status_code}): {response.text}"
            ) from exc

        if isinstance(payload, dict) and "code" in payload and payload.get("code", 0) < 0:
            raise BinanceAPIError(
                code=int(payload["code"]),
                message=str(payload.get("msg", "Unknown API error")),
            )

        if response.status_code >= 400:
            message = payload if isinstance(payload, str) else json.dumps(payload)
            raise NetworkError(f"HTTP {response.status_code}: {message}")

        return payload

    @staticmethod
    def _redact_params(params: dict[str, Any]) -> dict[str, Any]:
        redacted = dict(params)
        if "signature" in redacted:
            redacted["signature"] = REDACTED
        return redacted

    @staticmethod
    def _summarize_payload(payload: dict[str, Any] | list[dict[str, Any]]) -> str:
        if isinstance(payload, list):
            return f"[list len={len(payload)}]"

        symbols = payload.get("symbols")
        if isinstance(symbols, list):
            if len(symbols) == 1:
                symbol_name = symbols[0].get("symbol", "?")
                return (
                    f'{{"exchangeInfo": "1 symbol ({symbol_name})", '
                    f'"serverTime": {payload.get("serverTime")}}}'
                )
            return (
                f'{{"exchangeInfo": "{len(symbols)} symbols", '
                f'"serverTime": {payload.get("serverTime")}}}'
            )

        if "orderId" in payload:
            return json.dumps(
                {
                    "orderId": payload.get("orderId"),
                    "symbol": payload.get("symbol"),
                    "status": payload.get("status"),
                    "executedQty": payload.get("executedQty"),
                    "avgPrice": payload.get("avgPrice"),
                },
                separators=(",", ":"),
            )

        text = json.dumps(payload, separators=(",", ":"))
        if len(text) > 300:
            return f"{text[:300]}...[truncated]"
        return text

    @staticmethod
    def _full_payload(payload: dict[str, Any] | list[dict[str, Any]]) -> str:
        """Serialize the full response for DEBUG file logging."""
        return json.dumps(payload, separators=(",", ":"))


def create_client(settings: Settings) -> BinanceFuturesClient:
    """Create a configured Binance Futures client."""
    return BinanceFuturesClient(settings)
