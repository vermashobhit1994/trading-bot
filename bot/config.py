"""Load and validate application settings from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

from bot.exceptions import ConfigurationError

DEFAULT_TESTNET_URL = "https://demo-fapi.binance.com"
DEFAULT_MAINNET_URL = "https://fapi.binance.com"


class TradingEnvironment(str, Enum):
    TESTNET = "testnet"
    MAINNET = "mainnet"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _resolve_base_url(trading_env: TradingEnvironment, explicit_url: str | None) -> str:
    if explicit_url:
        return explicit_url.rstrip("/")

    if trading_env is TradingEnvironment.TESTNET:
        return DEFAULT_TESTNET_URL

    return DEFAULT_MAINNET_URL


def _parse_trading_env(raw: str | None) -> TradingEnvironment:
    value = (raw or TradingEnvironment.TESTNET.value).strip().lower()
    try:
        return TradingEnvironment(value)
    except ValueError as exc:
        valid = ", ".join(env.value for env in TradingEnvironment)
        raise ConfigurationError(
            f"Invalid TRADING_ENV '{raw}'. Expected one of: {valid}."
        ) from exc


def _parse_recv_window(raw: str | None) -> int:
    value = (raw or "5000").strip()
    try:
        recv_window = int(value)
    except ValueError as exc:
        raise ConfigurationError(
            f"Invalid RECV_WINDOW '{raw}'. Must be a positive integer."
        ) from exc

    if recv_window <= 0:
        raise ConfigurationError("RECV_WINDOW must be greater than zero.")

    return recv_window


def _require_non_empty(name: str, value: str | None) -> str:
    if value is None or not value.strip():
        raise ConfigurationError(f"Missing required environment variable: {name}")
    return value.strip()


@dataclass(frozen=True)
class Settings:
    api_key: str
    api_secret: str
    base_url: str
    trading_env: TradingEnvironment
    recv_window: int
    log_level: str
    log_dir: Path
    project_root: Path

    @property
    def is_testnet(self) -> bool:
        return self.trading_env is TradingEnvironment.TESTNET

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> Settings:
        root = _project_root()
        load_dotenv(env_file or root / ".env")

        trading_env = _parse_trading_env(os.getenv("TRADING_ENV"))
        api_secret = os.getenv("SECRET_KEY") or os.getenv("BINANCE_API_SECRET")

        return cls(
            api_key=_require_non_empty("BINANCE_API_KEY", os.getenv("BINANCE_API_KEY")),
            api_secret=_require_non_empty("SECRET_KEY", api_secret),
            base_url=_resolve_base_url(
                trading_env,
                os.getenv("BINANCE_FUTURES_BASE_URL"),
            ),
            trading_env=trading_env,
            recv_window=_parse_recv_window(os.getenv("RECV_WINDOW")),
            log_level=(os.getenv("LOG_LEVEL") or "INFO").strip().upper(),
            log_dir=root / "logs",
            project_root=root,
        )


def load_settings(env_file: Path | None = None) -> Settings:
    """Load settings from the environment, raising ConfigurationError on failure."""
    return Settings.from_env(env_file=env_file)
