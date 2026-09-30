from __future__ import annotations

from enum import StrEnum
from pathlib import Path

import typer
from rich.console import Console

from approval_testkit import reporters
from approval_testkit.adapter import ConfigError, load_adapter
from approval_testkit.config import load_config
from approval_testkit.mutations import MUTATIONS
from approval_testkit.runner import run_all

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Check that your agent executes exactly what the human approved.",
)


class Format(StrEnum):
    terminal = "terminal"
    json = "json"
    markdown = "markdown"


@app.command()
def run(
    path: Path = typer.Argument(Path("."), help="Project dir containing approval-test.toml"),
    format: Format = typer.Option(Format.terminal, "--format", "-f"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Write report to a file"),
) -> None:
    """Run all configured approval-integrity checks. Exit 1 on any failure, 2 on config error."""
    err = Console(stderr=True)
    try:
        config = load_config(path)
        factory = load_adapter(config.adapter, path)
    except ConfigError as e:
        err.print(f"[bold red]config error:[/] {e}")
        raise typer.Exit(2) from None
    try:
        report = run_all(factory, config.request, config.mutations)
    except Exception as e:
        err.print(f"[bold red]adapter crashed:[/] {type(e).__name__}: {e}")
        raise typer.Exit(2) from None

    if format is Format.terminal:
        console = Console(record=output is not None)
        reporters.terminal(report, console)
        text = console.export_text() if output else None
    else:
        render = reporters.to_json if format is Format.json else reporters.to_markdown
        text = render(report)
        if not output:
            typer.echo(text)
    if output:
        output.write_text(text, encoding="utf-8")
    raise typer.Exit(report.exit_code)


@app.command("list-mutations")
def list_mutations() -> None:
    """Show available mutation classes."""
    for m in MUTATIONS:
        typer.echo(f"{m.name:<10} {m.invariant:<24} {m.description}")
