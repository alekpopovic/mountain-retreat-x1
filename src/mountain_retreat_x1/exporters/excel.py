"""Excel workbook exporters for preliminary planning documents."""

from collections.abc import Iterable
from pathlib import Path

from openpyxl import Workbook  # type: ignore[import-untyped]
from openpyxl.styles import Alignment, Font, PatternFill  # type: ignore[import-untyped]
from openpyxl.utils import get_column_letter  # type: ignore[import-untyped]
from openpyxl.worksheet.worksheet import Worksheet  # type: ignore[import-untyped]

from mountain_retreat_x1.config.loader import MountainRetreatConfig
from mountain_retreat_x1.models import MaterialItem

BOM_FILENAME = "Mountain_Retreat_X1_BOM.xlsx"
BOM_OUTPUT_DIR = "excel"

ITEM_HEADERS = (
    "Item Code",
    "Category",
    "Subcategory",
    "Description",
    "Specification",
    "Unit",
    "Base Quantity",
    "Waste %",
    "Quantity With Waste",
    "Unit Cost Low",
    "Unit Cost Standard",
    "Unit Cost Premium",
    "Subtotal Low",
    "Subtotal Standard",
    "Subtotal Premium",
    "Formula Note",
    "Assumption Ref",
    "Notes",
)

ITEM_SHEETS = (
    "Concrete_and_Foundations",
    "Rebar_and_Steel",
    "Timber_and_Glulam",
    "CLT_Optional",
    "Masonry_Optional",
    "Roof",
    "Facade",
    "Windows_and_Doors",
    "Insulation_and_Membranes",
    "Terrace",
    "Electrical",
    "Plumbing",
    "HVAC",
    "Smart_Home",
    "Off_Grid",
    "Interior_Finishes",
    "Tools",
    "Machinery",
    "Waste_Factors",
)

WORKBOOK_SHEETS = ("Summary", *ITEM_SHEETS, "Assumptions")


HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
SUBHEADER_FILL = PatternFill("solid", fgColor="D9EAF7")
HEADER_FONT = Font(color="FFFFFF", bold=True)
BOLD_FONT = Font(bold=True)
NOTICE_FONT = Font(bold=True, color="9C0006")


def _all_materials(config: MountainRetreatConfig) -> list[MaterialItem]:
    return [*config.materials_core.materials, *config.materials_mep.materials]


def _sheet_for_material(item: MaterialItem) -> str:
    text = f"{item.category} {item.subcategory} {item.name}".lower()
    if any(marker in text for marker in ("foundation", "concrete", "slab")):
        return "Concrete_and_Foundations"
    if any(marker in text for marker in ("rebar", "steel", "reinforcement")):
        return "Rebar_and_Steel"
    if any(marker in text for marker in ("timber", "glulam", "lvl", "wood")):
        return "Timber_and_Glulam"
    if "clt" in text:
        return "CLT_Optional"
    if any(marker in text for marker in ("masonry", "block", "brick")):
        return "Masonry_Optional"
    if "roof" in text:
        return "Roof"
    if "facade" in text or "cladding" in text:
        return "Facade"
    if any(marker in text for marker in ("window", "door", "glazing")):
        return "Windows_and_Doors"
    if any(marker in text for marker in ("insulation", "membrane", "barrier")):
        return "Insulation_and_Membranes"
    if any(marker in text for marker in ("terrace", "decking", "outdoor")):
        return "Terrace"
    if any(marker in text for marker in ("smart home", "zigbee", "matter", "mqtt")):
        return "Smart_Home"
    if any(marker in text for marker in ("pv", "battery", "generator", "off-grid")):
        return "Off_Grid"
    if "electrical" in text:
        return "Electrical"
    if any(marker in text for marker in ("plumbing", "water", "wastewater", "tank")):
        return "Plumbing"
    if any(marker in text for marker in ("hvac", "heating", "mechanical", "heat pump")):
        return "HVAC"
    if any(marker in text for marker in ("finish", "interior", "floor", "wall", "ceiling")):
        return "Interior_Finishes"
    if "tool" in text:
        return "Tools"
    if any(marker in text for marker in ("machine", "machinery", "equipment")):
        return "Machinery"
    return "Interior_Finishes"


def _materials_by_sheet(materials: Iterable[MaterialItem]) -> dict[str, list[MaterialItem]]:
    grouped: dict[str, list[MaterialItem]] = {sheet: [] for sheet in ITEM_SHEETS}
    for item in materials:
        grouped[_sheet_for_material(item)].append(item)
    return grouped


def _style_header_row(sheet: Worksheet, row: int = 1) -> None:
    for cell in sheet[row]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _set_widths(sheet: Worksheet, widths: tuple[float, ...]) -> None:
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width


def _configure_item_sheet(sheet: Worksheet) -> None:
    sheet.append(ITEM_HEADERS)
    _style_header_row(sheet)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:{get_column_letter(len(ITEM_HEADERS))}1"
    _set_widths(
        sheet,
        (
            16,
            16,
            22,
            32,
            46,
            12,
            14,
            10,
            18,
            14,
            18,
            18,
            16,
            20,
            18,
            42,
            26,
            48,
        ),
    )


def _append_material_row(sheet: Worksheet, item: MaterialItem) -> None:
    row = sheet.max_row + 1
    notes = f"{item.notes} Supplier placeholder: {item.supplier_placeholder}".strip()
    sheet.append(
        (
            item.code,
            item.category,
            item.subcategory,
            item.name,
            item.specification,
            item.unit,
            item.base_quantity,
            item.waste_percent,
            f"=G{row}*(1+H{row}/100)",
            item.unit_price_low,
            item.unit_price_standard,
            item.unit_price_premium,
            f"=I{row}*J{row}",
            f"=I{row}*K{row}",
            f"=I{row}*L{row}",
            item.formula_note,
            item.assumption_ref,
            notes,
        )
    )
    for cell in sheet[row]:
        cell.alignment = Alignment(vertical="top", wrap_text=True)
    for column in ("G", "H", "I", "J", "K", "L", "M", "N", "O"):
        sheet[f"{column}{row}"].number_format = '#,##0.00'


def _build_summary_sheet(
    sheet: Worksheet,
    materials: Iterable[MaterialItem],
) -> None:
    headers = (
        "Category",
        "Subtotal Low",
        "Subtotal Standard",
        "Subtotal Premium",
        "Source Sheets",
        "Notes",
    )
    sheet.append(headers)
    _style_header_row(sheet)
    categories = sorted({item.category for item in materials})
    source_sheets = ", ".join(ITEM_SHEETS)
    for row, category in enumerate(categories, start=2):
        low_formula = "+".join(
            f"SUMIF('{sheet_name}'!$B:$B,$A{row},'{sheet_name}'!$M:$M)"
            for sheet_name in ITEM_SHEETS
        )
        standard_formula = "+".join(
            f"SUMIF('{sheet_name}'!$B:$B,$A{row},'{sheet_name}'!$N:$N)"
            for sheet_name in ITEM_SHEETS
        )
        premium_formula = "+".join(
            f"SUMIF('{sheet_name}'!$B:$B,$A{row},'{sheet_name}'!$O:$O)"
            for sheet_name in ITEM_SHEETS
        )
        sheet.append(
            (
                category,
                f"={low_formula}",
                f"={standard_formula}",
                f"={premium_formula}",
                source_sheets,
                "Preliminary category subtotal from BOM item sheets.",
            )
        )
    total_row = sheet.max_row + 1
    sheet.append(
        (
            "TOTAL",
            f"=SUM(B2:B{total_row - 1})",
            f"=SUM(C2:C{total_row - 1})",
            f"=SUM(D2:D{total_row - 1})",
            "",
            "Preliminary total; not a procurement quote.",
        )
    )
    for cell in sheet[total_row]:
        cell.font = BOLD_FONT
        cell.fill = SUBHEADER_FILL
    for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row, min_col=2, max_col=4):
        for cell in row:
            cell.number_format = '#,##0.00'
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:F{sheet.max_row}"
    _set_widths(sheet, (22, 18, 20, 18, 48, 42))


def _assumption_rows(config: MountainRetreatConfig) -> tuple[tuple[str, str], ...]:
    return (
        ("Project name", config.project.project_name),
        ("Project code", config.project.project_code),
        ("Version", config.project.version),
        ("Status", config.project.status),
        ("Disclaimer", config.project.disclaimer),
        ("Country", config.project.country),
        ("Currency", config.project.currency),
        ("Revision date", config.project.revision_date.isoformat()),
        ("Author", config.project.author),
        ("Professional review required by", ", ".join(config.project.review_required_by)),
        ("Gross area m2", f"{config.building.gross_area_m2:g}"),
        ("Net area m2", f"{config.building.net_area_m2:g}"),
        ("Terrace area m2", f"{config.terrace.terrace_area_m2:g}"),
        ("Construction variant", config.building.construction_variant),
        ("Roof type", config.building.roof_type),
        ("Facade type", config.building.facade_type),
        ("Site", config.site.location_name),
        ("Climate zone", config.site.climate_zone),
        ("Altitude m", f"{config.site.altitude_m:g}"),
        ("Soil assumption", config.site.soil_assumption),
        ("Drainage risk", config.site.drainage_risk),
        ("Calculator warning", config.calculator_assumptions.warning),
        ("Smart home", f"{config.smart_home.platform} + {', '.join(config.smart_home.protocols)}"),
        ("Off-grid PV kWp", f"{config.off_grid.pv_kwp:g}"),
        ("Off-grid battery kWh", f"{config.off_grid.battery_kwh:g}"),
        ("Generator", config.off_grid.generator),
        ("Water tank L", f"{config.off_grid.water_tank_l:g}"),
        ("Wastewater options", "; ".join(config.off_grid.wastewater_options)),
        (
            "Supplier policy",
            "Use supplier placeholders only until real supplier quotations are provided.",
        ),
    )


def _build_assumptions_sheet(sheet: Worksheet, config: MountainRetreatConfig) -> None:
    sheet.append(("Assumption", "Value"))
    _style_header_row(sheet)
    for row in _assumption_rows(config):
        sheet.append(row)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:B{sheet.max_row}"
    _set_widths(sheet, (34, 100))
    for cell in sheet["B"]:
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    sheet["B5"].font = NOTICE_FONT


def _apply_workbook_metadata(workbook: Workbook, config: MountainRetreatConfig) -> None:
    workbook.properties.title = "Mountain Retreat X1 Preliminary BOM"
    workbook.properties.subject = "Preliminary planning bill of materials"
    workbook.properties.creator = config.project.author
    workbook.properties.keywords = "PRELIMINARY, not for construction, Mountain Retreat X1"


def generate_bom_workbook(config: MountainRetreatConfig, output_dir: Path) -> Path:
    """Generate the preliminary BOM workbook and return its path."""
    excel_dir = output_dir / BOM_OUTPUT_DIR
    excel_dir.mkdir(parents=True, exist_ok=True)

    materials = _all_materials(config)
    grouped = _materials_by_sheet(materials)
    workbook = Workbook()
    summary = workbook.active
    summary.title = "Summary"

    for sheet_name in ITEM_SHEETS:
        workbook.create_sheet(sheet_name)
    assumptions = workbook.create_sheet("Assumptions")

    _build_summary_sheet(summary, materials)
    for sheet_name in ITEM_SHEETS:
        sheet = workbook[sheet_name]
        _configure_item_sheet(sheet)
        for item in grouped[sheet_name]:
            _append_material_row(sheet, item)
    _build_assumptions_sheet(assumptions, config)
    _apply_workbook_metadata(workbook, config)

    path = excel_dir / BOM_FILENAME
    workbook.save(path)
    return path
