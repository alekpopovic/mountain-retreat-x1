"""Command line interface for Mountain Retreat X1."""

import json
from dataclasses import replace
from pathlib import Path
from typing import Annotated
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import typer
from rich.console import Console
from rich.table import Table

from mountain_retreat_x1 import __version__
from mountain_retreat_x1.calculators import area_summary, cost_summary, quantity_summary
from mountain_retreat_x1.calculators.results import QuantityMap
from mountain_retreat_x1.config import ConfigLoadError, load_config, with_variant
from mountain_retreat_x1.config.loader import MountainRetreatConfig
from mountain_retreat_x1.exporters import (
    generate_bom_workbook,
    generate_cost_estimate_workbook,
    generate_gantt_schedule_workbook,
    generate_maintenance_calendar_workbook,
    generate_qa_checklist_workbook,
)
from mountain_retreat_x1.generators import (
    generate_markdown_volumes,
    generate_pdf_volumes,
    generate_svg_drawings,
)
from mountain_retreat_x1.localization import LocalizationError, load_translator, normalize_language

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
ZIP_FILENAME = "Mountain_Retreat_X1_Professional_Documentation_Package.zip"
MANIFEST_FILENAME = "BUILD_MANIFEST.json"
INDEX_FILENAME = "INDEX.md"
ASSUMPTIONS_SUMMARY_FILENAME = "ASSUMPTIONS_SUMMARY.md"
DETERMINISTIC_ZIP_TIMESTAMP = (2026, 6, 24, 0, 0, 0)


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
        "--output",
        "--output-dir",
        "-o",
        file_okay=False,
        dir_okay=True,
        writable=True,
        help="Directory for generated artifacts.",
    ),
]

PipelineOutputOption = Annotated[
    Path,
    typer.Option(
        "--output",
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


def _apply_variant_or_exit(
    config: MountainRetreatConfig,
    variant: str | None,
) -> MountainRetreatConfig:
    try:
        return with_variant(config, variant)
    except ConfigLoadError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


def _room_count(config: MountainRetreatConfig) -> int:
    return len(config.rooms_ground_floor.rooms) + len(config.rooms_gallery.rooms)


def _material_count(config: MountainRetreatConfig) -> int:
    return len(config.materials_core.materials) + len(config.materials_mep.materials)


def _ensure_output_dirs(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for subdir in OUTPUT_SUBDIRS:
        (output_dir / subdir).mkdir(parents=True, exist_ok=True)


def _clean_generated_outputs(output_dir: Path) -> int:
    _ensure_output_dirs(output_dir)
    removed_count = 0
    for path in sorted(output_dir.rglob("*"), reverse=True):
        if path.name == ".gitkeep":
            continue
        if path.is_file():
            path.unlink()
            removed_count += 1
        elif path.is_dir() and path.name not in OUTPUT_SUBDIRS and not any(path.iterdir()):
            path.rmdir()
    _ensure_output_dirs(output_dir)
    return removed_count


def _config_dir_from_project(project: Path | None, config_dir: Path) -> Path:
    if project is None:
        return config_dir
    if project.name != "project.yaml":
        console.print("[red]--project must point to a project.yaml file.[/red]")
        raise typer.Exit(1)
    return project.parent


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
    table.add_row(
        "Variants",
        "valid",
        f"{len(config.variants)} variants; active {config.variant.code}",
    )
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
    table.add_row("Construction variant", config.variant.name)
    table.add_row("Variant code", config.variant.code)
    table.add_row("Procurement complexity", config.variant.procurement_complexity)
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


def _language_or_exit(language: str | None) -> str:
    try:
        return normalize_language(language)
    except LocalizationError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


def _localized_config_or_exit(
    config: MountainRetreatConfig,
    language: str,
) -> MountainRetreatConfig:
    try:
        translator = load_translator(language)
    except LocalizationError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    review_notes = translator.list_text("professional_review_notes")
    project = config.project.model_copy(
        update={
            "language": translator.language,
            "disclaimer": translator.text("disclaimer_text", config.project.disclaimer),
            "review_required_by": review_notes or config.project.review_required_by,
        }
    )
    return replace(config, project=project)


def _mandatory_notice(config: MountainRetreatConfig) -> str:
    return (
        f"{config.project.disclaimer} Generated documents are preliminary planning "
        "documents only. They are not permits, approvals, stamped or signed engineering "
        "documents, final calculations, procurement instructions, financing-grade "
        "estimates, or documents for legal reliance."
    )


def _relative_output_files(output_dir: Path) -> list[Path]:
    files: list[Path] = []
    for subdir in ("markdown", "pdf", "excel", "drawings"):
        root = output_dir / subdir
        if root.exists():
            files.extend(path for path in root.rglob("*") if path.is_file())
    for filename in (INDEX_FILENAME, ASSUMPTIONS_SUMMARY_FILENAME, MANIFEST_FILENAME):
        path = output_dir / filename
        if path.exists():
            files.append(path)
    return sorted(files)


def _write_assumptions_summary(
    config: MountainRetreatConfig,
    output_dir: Path,
    language: str,
    large_mode: bool,
) -> Path:
    areas = area_summary(config)
    quantities = quantity_summary(config)
    costs = cost_summary(config)
    path = output_dir / ASSUMPTIONS_SUMMARY_FILENAME
    lines = [
        "# Assumptions Summary",
        "",
        f"Project: {config.project.project_name}",
        f"Version: {config.project.version}",
        f"Language: {language}",
        f"Large mode: {large_mode}",
        f"Status: {config.project.status}",
        "",
        "## Mandatory Notice",
        "",
        _mandatory_notice(config),
        "",
        "## Key Geometry",
        "",
        f"- Gross area: {config.building.gross_area_m2:g} m2",
        f"- Net area: {config.building.net_area_m2:g} m2",
        f"- Terrace area: {config.terrace.terrace_area_m2:g} m2",
        f"- Construction variant: {config.building.construction_variant}",
        f"- Active variant: {config.variant.name}",
        f"- Variant procurement complexity: {config.variant.procurement_complexity}",
        "",
        "## Calculated Planning Quantities",
        "",
    ]
    for key in (
        "calculated_net_area",
        "net_area_difference",
        "facade_rough_area",
        "roof_rough_area",
    ):
        result = areas[key]
        lines.append(f"- {result.label}: {result.value:g} {result.unit}; {result.formula_note}")
    for key in (
        "qty.concrete.volume",
        "qty.rebar.mass",
        "qty.structure.active_variant",
        "qty.roof.covering",
        "qty.terrace.decking",
    ):
        result = quantities[key]
        lines.append(f"- {result.label}: {result.value:g} {result.unit}; {result.formula_note}")
    lines.extend(
        [
            "",
            "## Cost Metrics",
            "",
            f"- Total preliminary cost: {costs['cost.total'].value:g} {costs['cost.total'].unit}",
            (
                "- Cost per gross m2: "
                f"{costs['cost.per_m2.gross'].value:g} {costs['cost.per_m2.gross'].unit}"
            ),
            (
                "- Cost per net m2: "
                f"{costs['cost.per_m2.net'].value:g} {costs['cost.per_m2.net'].unit}"
            ),
            "",
            "## Professional Review Required",
            "",
        ]
    )
    lines.extend(f"- {reviewer}" for reviewer in config.project.review_required_by)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_index_file(
    config: MountainRetreatConfig,
    output_dir: Path,
    language: str,
    large_mode: bool,
    generated_paths: list[Path],
) -> Path:
    path = output_dir / INDEX_FILENAME
    lines = [
        "# Mountain Retreat X1 Generated Package Index",
        "",
        f"Project: {config.project.project_name}",
        f"Version: {config.project.version}",
        f"Language: {language}",
        f"Large mode: {large_mode}",
        f"Status: {config.project.status}",
        "",
        _mandatory_notice(config),
        "",
        "## Files",
        "",
    ]
    for generated_path in sorted(generated_paths):
        lines.append(f"- {generated_path.relative_to(output_dir)}")
    lines.extend(
        [
            "",
            "## Required Professional Review",
            "",
            *[f"- {reviewer}" for reviewer in config.project.review_required_by],
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_build_manifest(
    config: MountainRetreatConfig,
    output_dir: Path,
    language: str,
    large_mode: bool,
    files: list[str],
) -> Path:
    manifest_path = output_dir / MANIFEST_FILENAME
    manifest = {
        "project_name": config.project.project_name,
        "version": config.project.version,
        "generated_at": f"{config.project.revision_date.isoformat()}T00:00:00+00:00",
        "language": language,
        "large_mode": large_mode,
        "files": sorted(files),
        "warnings": [
            _mandatory_notice(config),
            "Generated documents are preliminary planning documents only.",
            (
                "No generated document is a permit, approval, stamp, signature, "
                "or final engineering calculation."
            ),
        ],
        "professional_review_required": list(config.project.review_required_by),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _package_file_names(output_dir: Path, config_dir: Path) -> list[str]:
    names = [path.relative_to(output_dir).as_posix() for path in _relative_output_files(output_dir)]
    names.extend(
        path.relative_to(config_dir.parent).as_posix()
        for path in sorted(config_dir.rglob("*.yaml"))
    )
    for root_file_name in ("README.md", "LEGAL_AND_PROFESSIONAL_LIMITS.md"):
        if Path(root_file_name).exists():
            names.append(root_file_name)
    names.append(MANIFEST_FILENAME)
    names.append(f"zip/{ZIP_FILENAME}")
    return sorted(set(names))


def _zip_package(
    output_dir: Path,
    config_dir: Path,
    output_files: list[Path],
) -> Path:
    zip_path = output_dir / "zip" / ZIP_FILENAME
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
        for path in sorted(output_files):
            _write_zip_file(archive, path, path.relative_to(output_dir).as_posix())
        for yaml_path in sorted(config_dir.rglob("*.yaml")):
            _write_zip_file(
                archive,
                yaml_path,
                yaml_path.relative_to(config_dir.parent).as_posix(),
            )
        for root_file_name in ("README.md", "LEGAL_AND_PROFESSIONAL_LIMITS.md"):
            root_file = Path(root_file_name)
            if root_file.exists():
                _write_zip_file(archive, root_file, root_file.name)
    return zip_path


def _write_zip_file(archive: ZipFile, source_path: Path, archive_name: str) -> None:
    info = ZipInfo(archive_name, DETERMINISTIC_ZIP_TIMESTAMP)
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, source_path.read_bytes())


@generate_app.command("all")
def generate_all(
    config_dir: ConfigDirOption = Path("config"),
    project: Annotated[
        Path | None,
        typer.Option(
            "--project",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to project.yaml; its parent is used as the config directory.",
        ),
    ] = None,
    output_dir: PipelineOutputOption = Path("output"),
    lang: str = typer.Option(
        "sr-Latn",
        "--lang",
        help="Visible output language: sr-Latn or en.",
    ),
    large: bool = typer.Option(
        False,
        "--large",
        help="Generate expanded planning binder artifacts.",
    ),
    clean: bool = typer.Option(
        False,
        "--clean",
        help="Clean generated output folders before building.",
    ),
    variant: str = typer.Option(
        "standard_hybrid",
        "--variant",
        help="Construction variant: standard_hybrid, premium_clt, or masonry_hybrid.",
    ),
) -> None:
    """Generate all preliminary planning artifacts."""
    active_config_dir = _config_dir_from_project(project, config_dir)
    if clean:
        removed_count = _clean_generated_outputs(output_dir)
        console.print(
            f"[yellow]Cleaned generated outputs.[/yellow] Removed {removed_count} file(s)."
        )
    _ensure_output_dirs(output_dir)
    language = _language_or_exit(lang)
    config = _load_config_or_exit(active_config_dir)
    config = _apply_variant_or_exit(config, variant)
    config = _localized_config_or_exit(config, language)
    assumptions_path = _write_assumptions_summary(config, output_dir, language, large)
    markdown_paths = generate_markdown_volumes(
        config,
        output_dir,
        large_mode=large,
        language=language,
    )
    excel_paths = [
        generate_bom_workbook(config, output_dir, large_mode=large),
        generate_cost_estimate_workbook(config, output_dir),
        generate_gantt_schedule_workbook(config, output_dir),
        generate_qa_checklist_workbook(config, output_dir, large_mode=large),
        generate_maintenance_calendar_workbook(config, output_dir),
    ]
    drawing_paths = generate_svg_drawings(config, output_dir)
    pdf_paths = generate_pdf_volumes(config, output_dir, large_mode=large, language=language)
    generated_paths = [*markdown_paths, *excel_paths, *drawing_paths, *pdf_paths, assumptions_path]
    index_path = _write_index_file(config, output_dir, language, large, generated_paths)
    files_for_manifest = _package_file_names(output_dir, active_config_dir)
    manifest_path = _write_build_manifest(
        config,
        output_dir,
        language,
        large,
        files_for_manifest,
    )
    package_files = _relative_output_files(output_dir)
    zip_path = _zip_package(output_dir, active_config_dir, package_files)

    table = Table(title="Generated Planning Binder")
    table.add_column("Artifact", style="cyan")
    table.add_column("Output")
    table.add_row("Markdown", f"{len(markdown_paths)} source volumes generated")
    table.add_row("PDF", f"{len(pdf_paths)} preliminary documentation PDFs generated")
    table.add_row("Excel", f"{len(excel_paths)} planning workbooks generated")
    table.add_row("Drawings", f"{len(drawing_paths)} schematic SVG drawings generated")
    table.add_row("Index", str(index_path))
    table.add_row("Manifest", str(manifest_path))
    table.add_row("ZIP", str(zip_path))
    table.add_row("Mode", "large" if large else "normal")
    console.print(table)
    console.print(
        f"[green]Generate-all completed.[/green] Output prepared: {output_dir}"
    )


@generate_app.command("markdown")
def generate_markdown(
    config_dir: ConfigDirOption = Path("config"),
    output_dir: OutputDirOption = Path("output"),
    lang: str = typer.Option(
        "sr-Latn",
        "--lang",
        help="Visible output language: sr-Latn or en.",
    ),
    large: bool = typer.Option(
        False,
        "--large",
        help="Expand supported Markdown volumes with large-mode detail.",
    ),
) -> None:
    """Generate preliminary Markdown source volumes."""
    _ensure_output_dirs(output_dir)
    config = _load_config_or_exit(config_dir)
    language = _language_or_exit(lang)
    paths = generate_markdown_volumes(
        config,
        output_dir,
        large_mode=large,
        language=language,
    )

    table = Table(title="Generated Markdown Volumes")
    table.add_column("File", style="cyan")
    table.add_column("Status")
    for path in paths:
        table.add_row(str(path), "generated")
    console.print(table)
    console.print(f"[green]Markdown generation completed.[/green] {len(paths)} files.")


@generate_app.command("pdf")
def generate_pdf(
    config_dir: ConfigDirOption = Path("config"),
    output_dir: OutputDirOption = Path("output"),
    lang: str = typer.Option(
        "sr-Latn",
        "--lang",
        help="Visible output language: sr-Latn or en.",
    ),
    large: bool = typer.Option(
        False,
        "--large",
        help="Regenerate Markdown sources with large-mode detail before PDF rendering.",
    ),
) -> None:
    """Generate preliminary PDF volumes."""
    _ensure_output_dirs(output_dir)
    language = _language_or_exit(lang)
    config = _localized_config_or_exit(_load_config_or_exit(config_dir), language)
    paths = generate_pdf_volumes(config, output_dir, large_mode=large, language=language)

    table = Table(title="Generated PDF Volumes")
    table.add_column("File", style="cyan")
    table.add_column("Status")
    for path in paths:
        table.add_row(str(path), "generated")
    console.print(table)
    console.print(f"[green]PDF generation completed.[/green] {len(paths)} files.")


@generate_app.command("excel")
def generate_excel(
    config_dir: ConfigDirOption = Path("config"),
    output_dir: OutputDirOption = Path("output"),
    lang: str = typer.Option(
        "sr-Latn",
        "--lang",
        help="Visible safety language for workbook assumptions: sr-Latn or en.",
    ),
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
    gantt: Annotated[
        bool,
        typer.Option(
            "--gantt",
            help="Generate the preliminary 52-week Gantt schedule workbook.",
        ),
    ] = False,
    qa: Annotated[
        bool,
        typer.Option(
            "--qa",
            help="Generate the preliminary QA/QC checklist workbook.",
        ),
    ] = False,
    maintenance: Annotated[
        bool,
        typer.Option(
            "--maintenance",
            help="Generate the preliminary 30-year maintenance calendar workbook.",
        ),
    ] = False,
    large: Annotated[
        bool,
        typer.Option(
            "--large",
            help="Use large-mode expansions where supported.",
        ),
    ] = False,
) -> None:
    """Generate preliminary Excel workbooks."""
    _ensure_output_dirs(output_dir)
    language = _language_or_exit(lang)
    config = _localized_config_or_exit(_load_config_or_exit(config_dir), language)
    generate_all_excel = not any((bom, cost, gantt, qa, maintenance))
    generated_paths: list[Path] = []
    if bom or generate_all_excel:
        generated_paths.append(generate_bom_workbook(config, output_dir, large_mode=large))
    if cost or generate_all_excel:
        generated_paths.append(generate_cost_estimate_workbook(config, output_dir))
    if gantt or generate_all_excel:
        generated_paths.append(generate_gantt_schedule_workbook(config, output_dir))
    if qa or generate_all_excel:
        generated_paths.append(
            generate_qa_checklist_workbook(config, output_dir, large_mode=large)
        )
    if maintenance or generate_all_excel:
        generated_paths.append(generate_maintenance_calendar_workbook(config, output_dir))
    table = Table(title="Generated Excel Workbooks")
    table.add_column("File", style="cyan")
    table.add_column("Status")
    for path in generated_paths:
        table.add_row(str(path), "generated")
    console.print(table)
    console.print(f"[green]Excel generation completed.[/green] {len(generated_paths)} workbook(s).")


@generate_app.command("drawings")
def generate_drawings(
    config_dir: ConfigDirOption = Path("config"),
    output_dir: OutputDirOption = Path("output"),
    lang: str = typer.Option(
        "sr-Latn",
        "--lang",
        help="Visible safety language for drawing metadata: sr-Latn or en.",
    ),
) -> None:
    """Generate preliminary schematic drawings."""
    _ensure_output_dirs(output_dir)
    language = _language_or_exit(lang)
    config = _localized_config_or_exit(_load_config_or_exit(config_dir), language)
    paths = generate_svg_drawings(config, output_dir)

    table = Table(title="Generated SVG Schematic Drawings")
    table.add_column("File", style="cyan")
    table.add_column("Status")
    for path in paths:
        table.add_row(str(path), "generated")
    console.print(table)
    console.print(f"[green]Drawing generation completed.[/green] {len(paths)} files.")


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
