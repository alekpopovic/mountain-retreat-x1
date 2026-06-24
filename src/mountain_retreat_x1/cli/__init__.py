"""Command line interface for Mountain Retreat X1."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from mountain_retreat_x1 import __version__
from mountain_retreat_x1.config import ConfigLoadError, load_config

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
def validate(
    config_dir: Annotated[
        Path,
        typer.Option(
            "--config-dir",
            "-c",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing Mountain Retreat X1 YAML configuration.",
        ),
    ] = Path("config"),
) -> None:
    """Validate project YAML configuration files."""
    try:
        config = load_config(config_dir)
    except ConfigLoadError as exc:
        console.print(f"[red]Configuration validation failed:[/red]\n{exc}")
        raise typer.Exit(code=1) from exc

    room_count = len(config.rooms_ground_floor.rooms) + len(config.rooms_gallery.rooms)
    material_count = len(config.materials_core.materials) + len(config.materials_mep.materials)
    console.print(
        "[green]Configuration validation completed.[/green] "
        f"{room_count} rooms, {material_count} materials, "
        f"{len(config.construction_phases.phases)} phases."
    )


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
