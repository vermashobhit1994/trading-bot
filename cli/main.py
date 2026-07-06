"""CLI entry point for the trading bot."""

from __future__ import annotations

import logging

import typer

from bot import __version__
from bot.config import load_settings
from bot.exceptions import ConfigurationError, TradingBotError
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


@app.command("version")
def version() -> None:
    """Print application version."""
    typer.echo(__version__)


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
