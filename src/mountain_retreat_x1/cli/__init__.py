"""Command line interface for Mountain Retreat X1."""

from typing import Annotated

import typer
from rich.console import Console

from mountain_retreat_x1 import __version__

app = typer.Typer(
    name="mrx1",
    help=(
        "Mountain Retreat X1 preliminary planning documentation generator. "
        "Outputs are not for construction, permitting, or legal reliance."
    ),
    no_args_is_help=True,
)
generate_app = typer.Typer(help="Generate preliminary planning artifacts.")
app.add_typer(generate_app, name="generate")
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"mrx1 {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", callback=_version_callback, help="Show the version and exit."),
    ] = False,
) -> None:
    """Run the Mountain Retreat X1 CLI."""


@app.command()
def validate() -> None:
    """Validate project configuration placeholders."""
    console.print("[green]Validation placeholder completed.[/green]")


@generate_app.command("all")
def generate_all() -> None:
    """Generate all preliminary planning artifacts."""
    console.print("[green]Generate-all placeholder completed.[/green]")


@generate_app.command("pdf")
def generate_pdf() -> None:
    """Generate preliminary PDF volumes."""
    console.print("[green]PDF generation placeholder completed.[/green]")


@generate_app.command("excel")
def generate_excel() -> None:
    """Generate preliminary Excel workbooks."""
    console.print("[green]Excel generation placeholder completed.[/green]")


@generate_app.command("drawings")
def generate_drawings() -> None:
    """Generate preliminary schematic drawings."""
    console.print("[green]Drawing generation placeholder completed.[/green]")


@app.command()
def clean() -> None:
    """Clean generated output placeholders."""
    console.print("[green]Clean placeholder completed.[/green]")

