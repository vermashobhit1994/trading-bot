"""CLI entry point for the trading bot."""

from __future__ import annotations

import json
import logging

import typer

from bot import __version__
from bot.client import create_client
from bot.config import load_settings
from bot.exceptions import BinanceAPIError, ConfigurationError, NetworkError, TradingBotError
from bot.logging_config import setup_logging

app = typer.Typer(
    name="trading-bot",
    help="Place MARKET and LIMIT orders on Binance Futures Testnet (USDT-M).",
    add_completion=False,
    no_args_is_help=True,
)

logger = logging.getLogger(__name__)


def _bootstrap() -> None:
    """Load settings and initialize logging."""
    settings = load_settings()
    setup_logging(settings.log_dir, settings.log_level)


def _handle_client_errors(exc: Exception) -> None:
    if isinstance(exc, BinanceAPIError):
        typer.secho(f"Binance API error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    if isinstance(exc, NetworkError):
        typer.secho(f"Network error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    raise exc


@app.callback()
def main() -> None:
    """Initialize shared runtime configuration before subcommands run."""
    try:
        _bootstrap()
    except ConfigurationError as exc:
        typer.secho(f"Configuration error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc


@app.command("check-config")
def check_config() -> None:
    """Validate environment configuration without placing orders."""
    try:
        settings = load_settings()
    except ConfigurationError as exc:
        typer.secho(f"Configuration error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo("=== Configuration ===")
    typer.echo(f"Version:      {__version__}")
    typer.echo(f"Environment:  {settings.trading_env.value}")
    typer.echo(f"Base URL:     {settings.base_url}")
    typer.echo(f"Recv window:  {settings.recv_window} ms")
    typer.echo(f"Log level:    {settings.log_level}")
    typer.echo(f"Log dir:      {settings.log_dir}")
    typer.echo(f"API key:      {'configured' if settings.api_key else 'missing'}")
    typer.echo(f"API secret:   {'configured' if settings.api_secret else 'missing'}")
    typer.secho("Configuration OK.", fg=typer.colors.GREEN)


@app.command("ping")
def ping_api() -> None:
    """Test public connectivity to the Binance Futures API."""
    settings = load_settings()
    try:
        with create_client(settings) as client:
            response = client.ping()
    except (BinanceAPIError, NetworkError) as exc:
        _handle_client_errors(exc)
    else:
        typer.echo("=== Ping ===")
        typer.echo(json.dumps(response, indent=2))
        typer.secho("Ping successful.", fg=typer.colors.GREEN)


@app.command("server-time")
def server_time() -> None:
    """Fetch Binance server time (public endpoint)."""
    settings = load_settings()
    try:
        with create_client(settings) as client:
            response = client.get_server_time()
    except (BinanceAPIError, NetworkError) as exc:
        _handle_client_errors(exc)
    else:
        typer.echo("=== Server Time ===")
        typer.echo(json.dumps(response, indent=2))
        typer.secho("Server time fetched successfully.", fg=typer.colors.GREEN)


@app.command("test-auth")
def test_auth() -> None:
    """Verify API key, secret, and request signing via a signed balance call."""
    settings = load_settings()
    try:
        with create_client(settings) as client:
            balances = client.get_account_balance()
    except (BinanceAPIError, NetworkError) as exc:
        _handle_client_errors(exc)
    else:
        non_zero = [
            balance
            for balance in balances
            if float(balance.get("balance", 0)) != 0.0
            or float(balance.get("availableBalance", 0)) != 0.0
        ]

        typer.echo("=== Signed Auth Test ===")
        typer.echo(f"Assets returned: {len(balances)}")
        typer.echo(f"Non-zero assets: {len(non_zero)}")
        for balance in non_zero[:5]:
            typer.echo(
                f"  {balance.get('asset')}: "
                f"balance={balance.get('balance')} "
                f"available={balance.get('availableBalance')}"
            )
        if len(non_zero) > 5:
            typer.echo(f"  ... and {len(non_zero) - 5} more")
        typer.secho("Signed request authentication OK.", fg=typer.colors.GREEN)


@app.command("version")
def version() -> None:
    """Print application version."""
    typer.echo(__version__)


# Windows-friendly aliases (avoid hyphen parsing issues in PowerShell/cmd)
app.command("server_time")(server_time)
app.command("test_auth")(test_auth)
app.command("check_config")(check_config)


def run() -> None:
    """Run the Typer application with a top-level error handler."""
    try:
        app()
    except TradingBotError as exc:
        logger.exception("Application error")
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc


if __name__ == "__main__":
    run()
