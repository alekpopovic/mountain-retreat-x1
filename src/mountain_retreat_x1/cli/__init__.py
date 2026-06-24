"""Command line interface for Mountain Retreat X1."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from mountain_retreat_x1 import __version__
from mountain_retreat_x1.calculators import area_summary, cost_summary, quantity_summary
from mountain_retreat_x1.calculators.results import QuantityMap
from mountain_retreat_x1.config import ConfigLoadError, load_config
from mountain_retreat_x1.config.loader import MountainRetreatConfig
from mountain_retreat_x1.exporters import generate_bom_workbook, generate_cost_estimate_workbook
from mountain_retreat_x1.generators import generate_markdown_volumes

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
OUTPUT_SUBDIRS = ("markdown", "pdf", "excel", "drawings", "zip")


ConfigDirOption = Annotated[
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
]
OutputDirOption = Annotated[
    Path,
    typer.Option(
        "--output-dir",
        "-o",
        file_okay=False,
        dir_okay=True,
        writable=True,
        help="Directory for generated artifacts.",
    ),
]


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


def _load_config_or_exit(config_dir: Path) -> MountainRetreatConfig:
    try:
        return load_config(config_dir)
    except ConfigLoadError as exc:
        console.print(f"[red]Configuration validation failed:[/red]\n{exc}")
        raise typer.Exit(code=1) from exc


def _room_count(config: MountainRetreatConfig) -> int:
    return len(config.rooms_ground_floor.rooms) + len(config.rooms_gallery.rooms)


def _material_count(config: MountainRetreatConfig) -> int:
    return len(config.materials_core.materials) + len(config.materials_mep.materials)


def _ensure_output_dirs(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for subdir in OUTPUT_SUBDIRS:
        (output_dir / subdir).mkdir(parents=True, exist_ok=True)


def _config_summary_table(config: MountainRetreatConfig) -> Table:
    table = Table(title="Mountain Retreat X1 Configuration")
    table.add_column("Area", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Details")
    table.add_row("Project", "valid", f"{config.project.project_name} ({config.project.status})")
    table.add_row("Site", "valid", f"{config.site.location_name}, {config.site.country}")
    table.add_row(
        "Building",
        "valid",
        f"{config.building.gross_area_m2:g} m2 gross, {config.building.floors} floors",
    )
    table.add_row("Rooms", "valid", f"{_room_count(config)} room data sheets")
    table.add_row("Terrace", "valid", f"{config.terrace.terrace_area_m2:g} m2, preliminary")
    table.add_row("Materials", "valid", f"{_material_count(config)} catalog items")
    table.add_row("Costs", "valid", f"{len(config.cost_assumptions_serbia_2026.cost_items)} items")
    table.add_row("Phases", "valid", f"{len(config.construction_phases.phases)} phases")
    table.add_row("Calculator assumptions", "valid", config.calculator_assumptions.status)
    table.add_row(
        "Checklists",
        "valid",
        f"{len(config.checklists_seed.checklist_items)} seed items",
    )
    table.add_row("Localization", "valid", config.localization.default_language)
    return table


def _project_summary_table(config: MountainRetreatConfig) -> Table:
    table = Table(title="Project Summary")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value")
    table.add_row("Project", config.project.project_name)
    table.add_row("Code", config.project.project_code)
    table.add_row("Version", config.project.version)
    table.add_row("Status", config.project.status)
    table.add_row("Language", config.project.language)
    table.add_row("Country", config.project.country)
    table.add_row("Currency", config.project.currency)
    table.add_row("Revision date", config.project.revision_date.isoformat())
    return table


def _area_summary_table(config: MountainRetreatConfig) -> Table:
    table = Table(title="Area Summary")
    table.add_column("Area", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Gross area", f"{config.building.gross_area_m2:g} m2")
    table.add_row("Net area", f"{config.building.net_area_m2:g} m2")
    table.add_row("Terrace", f"{config.building.terrace_area_m2:g} m2")
    table.add_row(
        "Footprint",
        f"{config.building.footprint_length_m:g} x {config.building.footprint_width_m:g} m",
    )
    return table


def _room_summary_table(config: MountainRetreatConfig) -> Table:
    ground_floor_area = sum(room.area_m2 for room in config.rooms_ground_floor.rooms)
    gallery_area = sum(room.area_m2 for room in config.rooms_gallery.rooms)
    table = Table(title="Room Summary")
    table.add_column("Floor", style="cyan")
    table.add_column("Rooms", justify="right")
    table.add_column("Configured Area", justify="right")
    table.add_row(
        "ground_floor",
        str(len(config.rooms_ground_floor.rooms)),
        f"{ground_floor_area:.1f} m2",
    )
    table.add_row("gallery", str(len(config.rooms_gallery.rooms)), f"{gallery_area:.1f} m2")
    table.add_row("total", str(_room_count(config)), f"{ground_floor_area + gallery_area:.1f} m2")
    return table


def _assumptions_table(config: MountainRetreatConfig) -> Table:
    table = Table(title="Key Assumptions")
    table.add_column("Topic", style="cyan")
    table.add_column("Assumption")
    table.add_row("Construction variant", config.building.construction_variant)
    table.add_row("Alternatives", "premium_clt, masonry_hybrid")
    table.add_row("Roof", config.building.roof_type)
    table.add_row("Facade", config.building.facade_type)
    table.add_row("Heating", "air-to-water heat pump + underfloor heating + fireplace")
    table.add_row(
        "Off-grid",
        f"{config.off_grid.pv_kwp:g} kWp PV + {config.off_grid.battery_kwh:g} kWh battery",
    )
    table.add_row("Water", f"{config.off_grid.water_tank_l:,} L tank option")
    table.add_row("Wastewater", "; ".join(config.off_grid.wastewater_options))
    table.add_row(
        "Smart home",
        f"{config.smart_home.platform} + {', '.join(config.smart_home.protocols)}",
    )
    table.add_row("Professional limits", config.project.disclaimer)
    return table


def _calculated_summary_table(title: str, quantities: QuantityMap, keys: tuple[str, ...]) -> Table:
    table = Table(title=title)
    table.add_column("Quantity", style="cyan")
    table.add_column("Value", justify="right")
    table.add_column("Formula / Assumptions")
    for key in keys:
        quantity = quantities[key]
        table.add_row(
            quantity.label,
            f"{quantity.value:g} {quantity.unit}",
            f"{quantity.formula_note} Assumptions: {', '.join(quantity.assumptions_used)}",
        )
    return table


@app.command()
def validate(
    config_dir: ConfigDirOption = Path("config"),
) -> None:
    """Validate project YAML configuration files."""
    config = _load_config_or_exit(config_dir)
    console.print(_config_summary_table(config))
    console.print(
        "[green]Configuration validation completed.[/green] "
        f"{_room_count(config)} rooms, {_material_count(config)} materials, "
        f"{len(config.construction_phases.phases)} phases."
    )


@app.command()
def summary(
    config_dir: ConfigDirOption = Path("config"),
) -> None:
    """Print project, area, room, variant, and assumption summaries."""
    config = _load_config_or_exit(config_dir)
    console.print(_project_summary_table(config))
    console.print(_area_summary_table(config))
    console.print(_room_summary_table(config))
    console.print(_assumptions_table(config))
    console.print(
        _calculated_summary_table(
            "Calculated Area Summary",
            area_summary(config),
            (
                "calculated_net_area",
                "net_area_difference",
                "facade_rough_area",
                "roof_rough_area",
            ),
        )
    )
    console.print(
        _calculated_summary_table(
            "Calculated Quantity Summary",
            quantity_summary(config),
            (
                "qty.concrete.volume",
                "qty.rebar.mass",
                "qty.roof.covering",
                "qty.terrace.decking",
            ),
        )
    )
    console.print(
        _calculated_summary_table(
            "Calculated Cost Summary",
            cost_summary(config),
            ("cost.total", "cost.per_m2.gross", "cost.per_m2.net"),
        )
    )


def _print_placeholder_generation(kind: str, output_dir: Path) -> None:
    _ensure_output_dirs(output_dir)
    console.print(f"[green]{kind} generation placeholder completed.[/green]")
    console.print(f"Output directory prepared: {output_dir}")


@generate_app.command("all")
def generate_all(
    config_dir: ConfigDirOption = Path("config"),
    output_dir: OutputDirOption = Path("output"),
) -> None:
    """Generate all preliminary planning artifacts."""
    _ensure_output_dirs(output_dir)
    config = _load_config_or_exit(config_dir)
    markdown_paths = generate_markdown_volumes(config, output_dir)
    table = Table(title="Planned Generators")
    table.add_column("Artifact", style="cyan")
    table.add_column("Future Output")
    table.add_row("Markdown", f"{len(markdown_paths)} source volumes generated")
    table.add_row("PDF", "Placeholder: documentation volumes with disclaimers and page numbers")
    table.add_row("Excel", "BOM, cost estimate, Gantt schedule, QA/QC checklists")
    table.add_row("Drawings", "Plain SVG schematic drawings marked preliminary")
    table.add_row("ZIP", "Final package with YAML, manifest, and generated artifacts")
    console.print(table)
    console.print(
        f"[green]Generate-all placeholder completed.[/green] Output prepared: {output_dir}"
    )


@generate_app.command("markdown")
def generate_markdown(
    config_dir: ConfigDirOption = Path("config"),
    output_dir: OutputDirOption = Path("output"),
) -> None:
    """Generate preliminary Markdown source volumes."""
    _ensure_output_dirs(output_dir)
    config = _load_config_or_exit(config_dir)
    paths = generate_markdown_volumes(config, output_dir)

    table = Table(title="Generated Markdown Volumes")
    table.add_column("File", style="cyan")
    table.add_column("Status")
    for path in paths:
        table.add_row(str(path), "generated")
    console.print(table)
    console.print(f"[green]Markdown generation completed.[/green] {len(paths)} files.")


@generate_app.command("pdf")
def generate_pdf(
    output_dir: OutputDirOption = Path("output"),
) -> None:
    """Generate preliminary PDF volumes."""
    _print_placeholder_generation("PDF", output_dir)


@generate_app.command("excel")
def generate_excel(
    config_dir: ConfigDirOption = Path("config"),
    output_dir: OutputDirOption = Path("output"),
    bom: Annotated[
        bool,
        typer.Option(
            "--bom",
            help="Generate the preliminary Excel BOM workbook.",
        ),
    ] = False,
    cost: Annotated[
        bool,
        typer.Option(
            "--cost",
            help="Generate the preliminary Excel cost estimate workbook.",
        ),
    ] = False,
) -> None:
    """Generate preliminary Excel workbooks."""
    if bom or cost:
        _ensure_output_dirs(output_dir)
        config = _load_config_or_exit(config_dir)
        generated_paths: list[Path] = []
        if bom:
            generated_paths.append(generate_bom_workbook(config, output_dir))
        if cost:
            generated_paths.append(generate_cost_estimate_workbook(config, output_dir))
        table = Table(title="Generated Excel Workbooks")
        table.add_column("File", style="cyan")
        table.add_column("Status")
        for path in generated_paths:
            table.add_row(str(path), "generated")
        console.print(table)
        console.print(
            f"[green]Excel generation completed.[/green] {len(generated_paths)} workbook(s)."
        )
        return
    _print_placeholder_generation("Excel", output_dir)


@generate_app.command("drawings")
def generate_drawings(
    output_dir: OutputDirOption = Path("output"),
) -> None:
    """Generate preliminary schematic drawings."""
    _print_placeholder_generation("Drawing", output_dir)


@app.command()
def clean(
    output_dir: OutputDirOption = Path("output"),
) -> None:
    """Clean generated output folders while preserving .gitkeep files."""
    _ensure_output_dirs(output_dir)
    removed_count = 0
    for path in output_dir.rglob("*"):
        if path.name == ".gitkeep":
            continue
        if path.is_file() or path.is_symlink():
            path.unlink()
            removed_count += 1

    for subdir in OUTPUT_SUBDIRS:
        (output_dir / subdir).mkdir(parents=True, exist_ok=True)
        keep_file = output_dir / subdir / ".gitkeep"
        keep_file.touch(exist_ok=True)

    console.print(f"[green]Clean completed.[/green] Removed {removed_count} generated paths.")
