"""HMAC-SHA256 signing helpers for Binance signed endpoints."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode


def get_timestamp_ms() -> int:
    """Return current UTC time in milliseconds."""
    return int(time.time() * 1000)


def build_query_string(params: dict[str, Any]) -> str:
    """Encode request parameters as a URL query string."""
    filtered = {key: value for key, value in params.items() if value is not None}
    return urlencode(filtered, doseq=True)


def sign_payload(payload: str, secret: str) -> str:
    """Create an HMAC-SHA256 signature for a Binance signed request."""
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
