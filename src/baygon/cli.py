"""Command line interface for Baygon."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import typer
from rich.console import Console

from . import __version__
from .loader import ConfigSyntaxError, SyntaxIssue, load_file, locate_config_file

console = Console()
err_console = Console(stderr=True)


@dataclass(slots=True)
class CLIState:
    """Runtime configuration shared across commands."""

    verbosity: int = 0


app = typer.Typer(add_completion=False, help="Utilities to inspect Baygon configuration files.")


def _version_callback(value: bool) -> None:
    if value:
        console.print(__version__)
        raise typer.Exit()


def _configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    logging.basicConfig(level=level, format="%(message)s", force=True)


@app.callback()
def main(
    ctx: typer.Context,
    verbose: int = typer.Option(
        0,
        "-v",
        "--verbose",
        count=True,
        help="Increase verbosity. Repeat up to three times for more detail.",
    ),
    version: bool = typer.Option(
        False, "--version", help="Show the Baygon version and exit.", callback=_version_callback, is_eager=True
    ),
) -> None:
    """Configure the CLI before dispatching to a sub-command."""

    _ = version  # Typer passes the processed value, but it is handled eagerly by the callback.

    ctx.obj = CLIState(verbosity=verbose)
    _configure_logging(verbose)


def _render_issue(issue: SyntaxIssue) -> str:
    location = issue.format_location()
    hint = f" ({issue.hint})" if issue.hint else ""
    return f"[{issue.parser}] {location}: {issue.message}{hint}"


@app.command()
def check(
    ctx: typer.Context,
    config: Path | None = typer.Argument(
        None,
        help=(
            "Path to the Baygon configuration file to validate. When omitted, "
            "Baygon will search for a suitable configuration file."
        ),
    ),
) -> None:
    """Validate a configuration file without executing it."""

    state = ctx.obj or CLIState()
    logger = logging.getLogger(__name__)
    logger.debug("Checking configuration file %s", config)

    try:
        resolved_config = locate_config_file(config)
    except FileNotFoundError as exc:
        target = str(config) if config is not None else "auto"
        err_console.print(
            f"[red]Error:[/] Could not read '{target}': {exc.strerror or exc}"
        )
        raise typer.Exit(code=1)
    except OSError as exc:  # pragma: no cover - unexpected I/O errors
        target = str(config) if config is not None else "auto"
        err_console.print(f"[red]Error:[/] Could not read '{target}': {exc}")
        raise typer.Exit(code=1)

    try:
        data = load_file(resolved_config)
    except ConfigSyntaxError as exc:
        err_console.print(f"[red]Syntax error(s) detected in '{resolved_config}':[/]")
        for issue in exc.issues:
            err_console.print(f"  - {_render_issue(issue)}", markup=False)
        raise typer.Exit(code=1)

    logger.debug("Configuration loaded successfully: %s", data)
    if state.verbosity >= 2:
        console.print(data)
    console.print("[green]Configuration looks good![/]")


def run() -> None:
    """Execute the Typer application."""

    app()


def main_cli() -> None:  # pragma: no cover - compatibility entry-point
    """Backward compatible entry point used by packaging tools."""

    run()


__all__ = ["app", "run", "main_cli"]

