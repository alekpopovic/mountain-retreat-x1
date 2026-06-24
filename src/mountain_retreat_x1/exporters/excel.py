"""Excel workbook exporters for preliminary planning documents."""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from openpyxl import Workbook  # type: ignore[import-untyped]
from openpyxl.styles import Alignment, Font, PatternFill  # type: ignore[import-untyped]
from openpyxl.utils import get_column_letter  # type: ignore[import-untyped]
from openpyxl.worksheet.worksheet import Worksheet  # type: ignore[import-untyped]

from mountain_retreat_x1.config.loader import MountainRetreatConfig
from mountain_retreat_x1.models import CostItem, MaterialItem

BOM_FILENAME = "Mountain_Retreat_X1_BOM.xlsx"
COST_FILENAME = "Mountain_Retreat_X1_Cost_Estimate.xlsx"
GANTT_FILENAME = "Mountain_Retreat_X1_Gantt_Schedule.xlsx"
BOM_OUTPUT_DIR = "excel"
COST_OUTPUT_DIR = "excel"
GANTT_OUTPUT_DIR = "excel"

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
COST_WORKBOOK_SHEETS = (
    "Executive_Summary",
    "Cost_By_Phase",
    "Cost_By_Category",
    "Materials",
    "Labor",
    "Machinery",
    "Contingency",
    "Cash_Flow",
    "Scenario_Economy",
    "Scenario_Standard",
    "Scenario_Premium",
    "Scenario_OffGrid_AddOn",
    "Assumptions",
    "Review_Notes",
)
GANTT_WORKBOOK_SHEETS = (
    "Gantt",
    "Phase_Details",
    "Milestones",
    "Dependencies",
    "Risks",
    "Inspections",
    "Cashflow_By_Week",
    "Assumptions",
)

COST_ITEM_HEADERS = (
    "Cost Code",
    "Phase",
    "Category",
    "Description",
    "Quantity",
    "Unit",
    "Unit Cost",
    "Subtotal",
    "Notes",
)

SCENARIO_HEADERS = (
    "Cost Code",
    "Description",
    "Base Subtotal Before Contingency",
    "Scenario Factor",
    "Scenario Subtotal",
    "Contingency %",
    "Total With Contingency",
    "Notes",
)

EUR_FORMAT = '#,##0.00 "EUR"'
WEEK_HEADERS = tuple(f"Week {week}" for week in range(1, 53))
GANTT_HEADERS = (
    "WBS",
    "Phase",
    "Task",
    "Duration Days",
    "Start Week",
    "End Week",
    "Dependencies",
    "Responsible Party",
    "Risk Level",
    "Inspection Required",
    "Weather Sensitive",
    "Notes",
    *WEEK_HEADERS,
)


HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
SUBHEADER_FILL = PatternFill("solid", fgColor="D9EAF7")
HEADER_FONT = Font(color="FFFFFF", bold=True)
BOLD_FONT = Font(bold=True)
NOTICE_FONT = Font(bold=True, color="9C0006")
TIMELINE_FILL = PatternFill("solid", fgColor="70AD47")
MILESTONE_FILL = PatternFill("solid", fgColor="FFC000")
RISK_FILL = PatternFill("solid", fgColor="F4B084")


@dataclass(frozen=True)
class GanttTask:
    """Preliminary Gantt task row."""

    wbs: str
    phase: str
    task: str
    duration_days: int
    start_week: int
    end_week: int
    dependencies: str
    responsible_party: str
    risk_level: str
    inspection_required: str
    weather_sensitive: str
    notes: str


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


def _cost_items(config: MountainRetreatConfig) -> list[CostItem]:
    return config.cost_assumptions_serbia_2026.cost_items


def _configure_cost_table_sheet(sheet: Worksheet) -> None:
    sheet.append(COST_ITEM_HEADERS)
    _style_header_row(sheet)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:{get_column_letter(len(COST_ITEM_HEADERS))}1"
    _set_widths(sheet, (16, 18, 18, 42, 14, 10, 16, 18, 48))


def _append_cost_component_row(
    sheet: Worksheet,
    item: CostItem,
    unit_cost_attr: str,
) -> None:
    row = sheet.max_row + 1
    unit_cost = getattr(item, unit_cost_attr)
    sheet.append(
        (
            item.code,
            item.phase,
            item.category,
            item.description,
            item.quantity,
            item.unit,
            unit_cost,
            f"=E{row}*G{row}",
            item.notes,
        )
    )
    for cell in sheet[row]:
        cell.alignment = Alignment(vertical="top", wrap_text=True)
    for column in ("E", "G", "H"):
        sheet[f"{column}{row}"].number_format = EUR_FORMAT if column in ("G", "H") else '#,##0.00'


def _build_cost_component_sheet(
    sheet: Worksheet,
    items: Iterable[CostItem],
    unit_cost_attr: str,
) -> None:
    _configure_cost_table_sheet(sheet)
    for item in items:
        _append_cost_component_row(sheet, item, unit_cost_attr)
    total_row = sheet.max_row + 1
    sheet.append(("", "", "", "TOTAL", "", "", "", f"=SUM(H2:H{total_row - 1})", ""))
    for cell in sheet[total_row]:
        cell.font = BOLD_FONT
        cell.fill = SUBHEADER_FILL
    sheet[f"H{total_row}"].number_format = EUR_FORMAT


def _phase_or_category_formula(
    sheet_name: str,
    lookup_column: str,
    lookup_cell: str,
) -> str:
    return (
        f"SUMIF('{sheet_name}'!${lookup_column}:${lookup_column},"
        f"{lookup_cell},'{sheet_name}'!$H:$H)"
    )


def _build_cost_aggregation_sheet(
    sheet: Worksheet,
    labels: Iterable[str],
    lookup_column: str,
    title: str,
) -> None:
    sheet.append(
        (
            title,
            "Material Subtotal",
            "Labor Subtotal",
            "Machinery Subtotal",
            "Subtotal Before Contingency",
            "Contingency 10%",
            "Contingency 15%",
            "Contingency 20%",
            "Total With 20% Contingency",
            "Cost per Gross m2",
            "Cost per Net m2",
        )
    )
    _style_header_row(sheet)
    for row, label in enumerate(sorted(labels), start=2):
        lookup_cell = f"$A{row}"
        sheet.append(
            (
                label,
                f"={_phase_or_category_formula('Materials', lookup_column, lookup_cell)}",
                f"={_phase_or_category_formula('Labor', lookup_column, lookup_cell)}",
                f"={_phase_or_category_formula('Machinery', lookup_column, lookup_cell)}",
                f"=SUM(B{row}:D{row})",
                f"=E{row}*10%",
                f"=E{row}*15%",
                f"=E{row}*20%",
                f"=E{row}+H{row}",
                f"=I{row}/Assumptions!$B$11",
                f"=I{row}/Assumptions!$B$12",
            )
        )
    total_row = sheet.max_row + 1
    sheet.append(
        (
            "TOTAL",
            f"=SUM(B2:B{total_row - 1})",
            f"=SUM(C2:C{total_row - 1})",
            f"=SUM(D2:D{total_row - 1})",
            f"=SUM(E2:E{total_row - 1})",
            f"=SUM(F2:F{total_row - 1})",
            f"=SUM(G2:G{total_row - 1})",
            f"=SUM(H2:H{total_row - 1})",
            f"=SUM(I2:I{total_row - 1})",
            f"=I{total_row}/Assumptions!$B$11",
            f"=I{total_row}/Assumptions!$B$12",
        )
    )
    for cell in sheet[total_row]:
        cell.font = BOLD_FONT
        cell.fill = SUBHEADER_FILL
    for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row, min_col=2, max_col=11):
        for cell in row:
            cell.number_format = EUR_FORMAT
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:K{sheet.max_row}"
    _set_widths(sheet, (22, 18, 16, 18, 24, 18, 18, 18, 24, 18, 18))


def _build_contingency_sheet(sheet: Worksheet, items: list[CostItem]) -> None:
    sheet.append(
        (
            "Cost Code",
            "Description",
            "Subtotal Before Contingency",
            "Item Contingency %",
            "Item Contingency",
            "Contingency 10%",
            "Contingency 15%",
            "Contingency 20%",
            "Total With Item Contingency",
        )
    )
    _style_header_row(sheet)
    for row, item in enumerate(items, start=2):
        source_row = row
        sheet.append(
            (
                item.code,
                item.description,
                f"=Materials!H{source_row}+Labor!H{source_row}+Machinery!H{source_row}",
                item.contingency_percent / 100,
                f"=C{row}*D{row}",
                f"=C{row}*10%",
                f"=C{row}*15%",
                f"=C{row}*20%",
                f"=C{row}+E{row}",
            )
        )
    total_row = sheet.max_row + 1
    sheet.append(
        (
            "TOTAL",
            "",
            f"=SUM(C2:C{total_row - 1})",
            "",
            f"=SUM(E2:E{total_row - 1})",
            f"=SUM(F2:F{total_row - 1})",
            f"=SUM(G2:G{total_row - 1})",
            f"=SUM(H2:H{total_row - 1})",
            f"=SUM(I2:I{total_row - 1})",
        )
    )
    for cell in sheet[total_row]:
        cell.font = BOLD_FONT
        cell.fill = SUBHEADER_FILL
    for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row, min_col=3, max_col=9):
        for cell in row:
            cell.number_format = "0.00%" if cell.column == 4 else EUR_FORMAT
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:I{sheet.max_row}"
    _set_widths(sheet, (16, 42, 26, 18, 18, 18, 18, 18, 26))


def _build_scenario_sheet(
    sheet: Worksheet,
    items: list[CostItem],
    factor: float,
    contingency_percent: float,
) -> None:
    sheet.append(SCENARIO_HEADERS)
    _style_header_row(sheet)
    for row, item in enumerate(items, start=2):
        source_row = row
        sheet.append(
            (
                item.code,
                item.description,
                f"=Materials!H{source_row}+Labor!H{source_row}+Machinery!H{source_row}",
                factor,
                f"=C{row}*D{row}",
                contingency_percent,
                f"=E{row}*(1+F{row})",
                "Static placeholder scenario; contractor quotes required.",
            )
        )
    total_row = sheet.max_row + 1
    sheet.append(
        (
            "TOTAL",
            "",
            f"=SUM(C2:C{total_row - 1})",
            "",
            f"=SUM(E2:E{total_row - 1})",
            "",
            f"=SUM(G2:G{total_row - 1})",
            "",
        )
    )
    for cell in sheet[total_row]:
        cell.font = BOLD_FONT
        cell.fill = SUBHEADER_FILL
    for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row, min_col=3, max_col=7):
        for cell in row:
            cell.number_format = "0.00%" if cell.column == 6 else EUR_FORMAT
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:H{sheet.max_row}"
    _set_widths(sheet, (16, 42, 30, 16, 18, 16, 24, 46))


def _build_off_grid_addon_sheet(sheet: Worksheet, config: MountainRetreatConfig) -> None:
    sheet.append(
        (
            "Add-on Code",
            "System",
            "Quantity Placeholder",
            "Unit",
            "Unit Cost Placeholder",
            "Subtotal",
            "Notes",
        )
    )
    _style_header_row(sheet)
    rows = (
        ("OG-001", f"Solar PV {config.off_grid.pv_kwp:g} kWp placeholder", 1, "system", 18000),
        ("OG-002", f"Battery {config.off_grid.battery_kwh:g} kWh placeholder", 1, "system", 24000),
        ("OG-003", "Backup generator placeholder", 1, "system", 6500),
        ("OG-004", f"Water tank {config.off_grid.water_tank_l:g} L placeholder", 1, "system", 3200),
        ("OG-005", "Wastewater independence placeholder", 1, "system", 8000),
    )
    for row, (code, system, quantity, unit, unit_cost) in enumerate(rows, start=2):
        sheet.append(
            (
                code,
                system,
                quantity,
                unit,
                unit_cost,
                f"=C{row}*E{row}",
                "Optional planning add-on only; professional design and quotes required.",
            )
        )
    total_row = sheet.max_row + 1
    sheet.append(("TOTAL", "", "", "", "", f"=SUM(F2:F{total_row - 1})", ""))
    for cell in sheet[total_row]:
        cell.font = BOLD_FONT
        cell.fill = SUBHEADER_FILL
    for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row, min_col=5, max_col=6):
        for cell in row:
            cell.number_format = EUR_FORMAT
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:G{sheet.max_row}"
    _set_widths(sheet, (16, 42, 20, 12, 22, 18, 58))


def _build_cash_flow_sheet(sheet: Worksheet, phases: Iterable[str]) -> None:
    sheet.append(("Phase", "Phase Total With 20% Contingency", "Cash Flow %", "Cash Flow EUR"))
    _style_header_row(sheet)
    for row, phase in enumerate(sorted(phases), start=2):
        sheet.append(
            (
                phase,
                f"=SUMIF(Cost_By_Phase!$A:$A,A{row},Cost_By_Phase!$I:$I)",
                f"=B{row}/SUM(B:B)",
                f"=B{row}",
            )
        )
    total_row = sheet.max_row + 1
    sheet.append(
        (
            "TOTAL",
            f"=SUM(B2:B{total_row - 1})",
            f"=SUM(C2:C{total_row - 1})",
            f"=SUM(D2:D{total_row - 1})",
        )
    )
    for cell in sheet[total_row]:
        cell.font = BOLD_FONT
        cell.fill = SUBHEADER_FILL
    for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row, min_col=2, max_col=4):
        for cell in row:
            cell.number_format = "0.00%" if cell.column == 3 else EUR_FORMAT
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:D{sheet.max_row}"
    _set_widths(sheet, (22, 30, 16, 18))


def _build_cost_assumptions_sheet(sheet: Worksheet, config: MountainRetreatConfig) -> None:
    cost_config = config.cost_assumptions_serbia_2026
    rows = (
        ("Project", config.project.project_name),
        ("Status", config.project.status),
        ("Currency", cost_config.currency),
        ("Assumption year", str(cost_config.assumption_year)),
        ("last_updated", cost_config.last_updated.isoformat()),
        ("Source policy", cost_config.source_policy),
        ("VAT included", str(cost_config.vat_included)),
        ("Default contingency", f"{cost_config.contingency_percent:g}%"),
        ("Regional adjustment note", cost_config.regional_adjustment_note),
        ("Estimate warning", cost_config.estimate_warning),
        ("Gross area m2", f"{config.building.gross_area_m2:g}"),
        ("Net area m2", f"{config.building.net_area_m2:g}"),
        ("Off-grid PV kWp", f"{config.off_grid.pv_kwp:g}"),
        ("Off-grid battery kWh", f"{config.off_grid.battery_kwh:g}"),
        ("Professional limit", config.project.disclaimer),
        ("Quote requirement", "Contractor quotes are required before procurement or budgeting."),
    )
    sheet.append(("Assumption", "Value"))
    _style_header_row(sheet)
    for row in rows:
        sheet.append(row)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:B{sheet.max_row}"
    _set_widths(sheet, (30, 100))
    for cell in sheet["B"]:
        cell.alignment = Alignment(wrap_text=True, vertical="top")


def _build_review_notes_sheet(sheet: Worksheet, config: MountainRetreatConfig) -> None:
    notes = (
        "All prices are placeholders and static planning assumptions.",
        "Prices are not current market quotes and must not be represented as supplier offers.",
        "Contractor quotes are required before procurement, financing, or construction decisions.",
        config.cost_assumptions_serbia_2026.source_policy,
        config.cost_assumptions_serbia_2026.regional_adjustment_note,
        config.cost_assumptions_serbia_2026.estimate_warning,
        (
            "Licensed professionals must review structural, electrical, mechanical, "
            "plumbing, and off-grid systems."
        ),
    )
    sheet.append(("Review Note",))
    _style_header_row(sheet)
    for note in notes:
        sheet.append((note,))
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:A{sheet.max_row}"
    _set_widths(sheet, (120,))
    for cell in sheet["A"]:
        cell.alignment = Alignment(wrap_text=True, vertical="top")


def _build_executive_summary(sheet: Worksheet, config: MountainRetreatConfig) -> None:
    sheet.append(("Metric", "Value", "Notes"))
    _style_header_row(sheet)
    rows = (
        ("Material subtotal", "=SUM(Materials!H:H)", "Formula from Materials sheet."),
        ("Labor subtotal", "=SUM(Labor!H:H)", "Formula from Labor sheet."),
        ("Machinery subtotal", "=SUM(Machinery!H:H)", "Formula from Machinery sheet."),
        ("Subtotal before contingency", "=SUM(B2:B4)", "Materials + labor + machinery."),
        ("Contingency 10%", "=B5*10%", "Planning sensitivity."),
        ("Contingency 15%", "=B5*15%", "Planning sensitivity."),
        ("Contingency 20%", "=B5*20%", "Planning sensitivity."),
        ("Total with contingency", "=B5+B8", "Uses 20% contingency by default."),
        ("Cost per gross m2", "=B9/Assumptions!$B$11", "Gross area denominator."),
        ("Cost per net m2", "=B9/Assumptions!$B$12", "Net area denominator."),
        ("Optional off-grid add-on", "=Scenario_OffGrid_AddOn!F7", "Separate optional add-on."),
        ("Total with off-grid add-on", "=B9+B12", "Base total + optional add-on."),
        ("Economy scenario", "=Scenario_Economy!G5", "Scenario comparison total."),
        ("Standard scenario", "=Scenario_Standard!G5", "Scenario comparison total."),
        ("Premium scenario", "=Scenario_Premium!G5", "Scenario comparison total."),
        (
            "last_updated",
            config.cost_assumptions_serbia_2026.last_updated.isoformat(),
            "From YAML cost assumptions.",
        ),
        ("Quote requirement", "Contractor quotes required", "Prices are placeholders."),
    )
    for row in rows:
        sheet.append(row)
    for row in sheet.iter_rows(min_row=2, max_row=16, min_col=2, max_col=2):
        for cell in row:
            if isinstance(cell.value, str) and cell.value.startswith("="):
                cell.number_format = EUR_FORMAT
    for row_number in (5, 8, 9, 13):
        for cell in sheet[row_number]:
            cell.font = BOLD_FONT
            cell.fill = SUBHEADER_FILL
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:C{sheet.max_row}"
    _set_widths(sheet, (34, 24, 58))


def _apply_cost_workbook_metadata(workbook: Workbook, config: MountainRetreatConfig) -> None:
    workbook.properties.title = "Mountain Retreat X1 Preliminary Cost Estimate"
    workbook.properties.subject = "Preliminary planning cost estimate"
    workbook.properties.creator = config.project.author
    workbook.properties.keywords = "PRELIMINARY, placeholder prices, contractor quotes required"


def generate_cost_estimate_workbook(config: MountainRetreatConfig, output_dir: Path) -> Path:
    """Generate the preliminary cost estimate workbook and return its path."""
    excel_dir = output_dir / COST_OUTPUT_DIR
    excel_dir.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    workbook.active.title = "Executive_Summary"
    for sheet_name in COST_WORKBOOK_SHEETS[1:]:
        workbook.create_sheet(sheet_name)

    items = _cost_items(config)
    phases = {item.phase for item in items}
    categories = {item.category for item in items}

    _build_cost_component_sheet(workbook["Materials"], items, "material_unit_cost")
    _build_cost_component_sheet(workbook["Labor"], items, "labor_unit_cost")
    _build_cost_component_sheet(workbook["Machinery"], items, "machinery_unit_cost")
    _build_cost_aggregation_sheet(workbook["Cost_By_Phase"], phases, "B", "Phase")
    _build_cost_aggregation_sheet(workbook["Cost_By_Category"], categories, "C", "Category")
    _build_contingency_sheet(workbook["Contingency"], items)
    _build_cash_flow_sheet(workbook["Cash_Flow"], phases)
    _build_scenario_sheet(workbook["Scenario_Economy"], items, 0.9, 0.10)
    _build_scenario_sheet(workbook["Scenario_Standard"], items, 1.0, 0.15)
    _build_scenario_sheet(workbook["Scenario_Premium"], items, 1.25, 0.20)
    _build_off_grid_addon_sheet(workbook["Scenario_OffGrid_AddOn"], config)
    _build_cost_assumptions_sheet(workbook["Assumptions"], config)
    _build_review_notes_sheet(workbook["Review_Notes"], config)
    _build_executive_summary(workbook["Executive_Summary"], config)
    _apply_cost_workbook_metadata(workbook, config)

    path = excel_dir / COST_FILENAME
    workbook.save(path)
    return path


def _default_gantt_tasks() -> tuple[GanttTask, ...]:
    return (
        GanttTask(
            "1.0",
            "Design and professional review",
            "Surveys, geotechnical brief, and licensed review",
            20,
            1,
            4,
            "",
            "Owner with licensed professionals",
            "Medium",
            "Yes",
            "Yes",
            "Mountain site access and weather windows must be confirmed.",
        ),
        GanttTask(
            "2.0",
            "Permits and site preparation",
            "Permitting pathway, temporary services, and site setup",
            15,
            5,
            7,
            "1.0",
            "Owner / architect / local authority",
            "High",
            "Yes",
            "Yes",
            "No generated document is a permit or approval.",
        ),
        GanttTask(
            "3.0",
            "Access road and logistics",
            "Access road verification, delivery planning, laydown zones",
            15,
            6,
            8,
            "1.0",
            "Contractor / civil consultant",
            "High",
            "Yes",
            "Yes",
            "Mountain logistics can control the real schedule.",
        ),
        GanttTask(
            "4.0",
            "Earthworks",
            "Excavation, slope control, and temporary erosion measures",
            15,
            8,
            10,
            "2.0, 3.0",
            "Civil contractor",
            "High",
            "Yes",
            "Yes",
            "Weather and soil assumptions must be verified on site.",
        ),
        GanttTask(
            "5.0",
            "Drainage",
            "Temporary and permanent drainage routes",
            10,
            9,
            11,
            "4.0",
            "Civil contractor / drainage designer",
            "High",
            "Yes",
            "Yes",
            "Drainage must be coordinated before foundations are closed.",
        ),
        GanttTask(
            "6.0",
            "Foundations",
            "Foundation works and slab concept execution",
            20,
            11,
            14,
            "4.0, 5.0",
            "Structural contractor",
            "High",
            "Yes",
            "Yes",
            "Requires geotechnical and structural design before construction.",
        ),
        GanttTask(
            "7.0",
            "Structural frame",
            "Timber/hybrid structural frame erection",
            20,
            15,
            18,
            "6.0",
            "Structural contractor",
            "High",
            "Yes",
            "Yes",
            "Lifting plan, bracing, and inspection hold points required.",
        ),
        GanttTask(
            "8.0",
            "Roof",
            "Roof structure, underlay, and standing seam concept",
            15,
            18,
            20,
            "7.0",
            "Roofing contractor",
            "High",
            "Yes",
            "Yes",
            "Snow, wind, fall protection, and weather closure are key risks.",
        ),
        GanttTask(
            "9.0",
            "Exterior closure",
            "Windows, doors, air/water barrier, temporary dry-in",
            15,
            20,
            22,
            "8.0",
            "Envelope contractor",
            "Medium",
            "Yes",
            "Yes",
            "Protect interior works from mountain weather.",
        ),
        GanttTask(
            "10.0",
            "Facade",
            "Timber, stone, and glass facade works",
            20,
            22,
            25,
            "9.0",
            "Facade contractor",
            "Medium",
            "Yes",
            "Yes",
            "Thermal bridges and waterproofing details require review.",
        ),
        GanttTask(
            "11.0",
            "Electrical rough-in",
            "Electrical containment, rough wiring, boards, exterior routes",
            15,
            24,
            26,
            "9.0",
            "Licensed electrician",
            "High",
            "Yes",
            "No",
            "Final cable sizing and code compliance by licensed professionals.",
        ),
        GanttTask(
            "12.0",
            "Plumbing rough-in",
            "Water, waste, vent, and drainage rough-in",
            15,
            24,
            26,
            "9.0",
            "Licensed plumber",
            "High",
            "Yes",
            "Yes",
            "Freeze protection and slopes must be inspected.",
        ),
        GanttTask(
            "13.0",
            "HVAC rough-in",
            "UFH manifolds, heat-pump interfaces, ventilation routes",
            15,
            25,
            27,
            "9.0, 11.0, 12.0",
            "Mechanical contractor",
            "High",
            "Yes",
            "Yes",
            "No final heat-loss calculation is generated by this project.",
        ),
        GanttTask(
            "14.0",
            "Interior walls and insulation",
            "Partitions, insulation, vapor control, service closures",
            20,
            27,
            30,
            "11.0, 12.0, 13.0",
            "Interior contractor",
            "Medium",
            "Yes",
            "No",
            "Do not close walls before MEP inspections.",
        ),
        GanttTask(
            "15.0",
            "Floors and finishes",
            "Floor build-ups, wall finishes, ceiling finishes",
            20,
            31,
            34,
            "14.0",
            "Finishing contractor",
            "Medium",
            "No",
            "No",
            "Moisture and temperature conditions affect finish quality.",
        ),
        GanttTask(
            "16.0",
            "Bathrooms",
            "Bathroom waterproofing, fixtures, extraction, finishes",
            15,
            32,
            34,
            "12.0, 14.0",
            "Bathroom contractor / plumber",
            "High",
            "Yes",
            "No",
            "Waterproofing hold points and ventilation checks required.",
        ),
        GanttTask(
            "17.0",
            "Kitchen",
            "Kitchen installation and appliance interfaces",
            10,
            35,
            36,
            "11.0, 12.0, 15.0",
            "Kitchen installer",
            "Medium",
            "No",
            "No",
            "Appliance loads and plumbing connections require review.",
        ),
        GanttTask(
            "18.0",
            "Terrace",
            "Terrace structure, drainage, guard, decking, utility placeholders",
            25,
            34,
            38,
            "7.0, 8.0, 10.0",
            "Terrace contractor / structural engineer",
            "High",
            "Yes",
            "Yes",
            "Terrace load, waterproofing, guard, and drainage risks are high.",
        ),
        GanttTask(
            "19.0",
            "Smart home",
            "Controller, network, sensors, cameras, scenes, tests",
            10,
            37,
            38,
            "11.0, 15.0",
            "Smart-home integrator",
            "Medium",
            "No",
            "No",
            "Security and life-safety integrations must remain advisory.",
        ),
        GanttTask(
            "20.0",
            "Solar/off-grid",
            "PV, battery, generator, water/off-grid placeholders",
            20,
            39,
            42,
            "8.0, 11.0, 13.0",
            "Licensed electrical/mechanical specialists",
            "High",
            "Yes",
            "Yes",
            "Winter performance and utility approvals are not guaranteed.",
        ),
        GanttTask(
            "21.0",
            "Landscaping",
            "Final grading, paths, erosion control, planting",
            20,
            43,
            46,
            "5.0, 18.0",
            "Landscape / civil contractor",
            "Medium",
            "Yes",
            "Yes",
            "Weather, slope, and drainage can shift sequencing.",
        ),
        GanttTask(
            "22.0",
            "Testing and handover",
            "Commissioning, inspections, owner handover, defect list",
            20,
            47,
            50,
            "16.0, 17.0, 18.0, 19.0, 20.0",
            "Contractor with licensed professionals",
            "High",
            "Yes",
            "Yes",
            "Contractor quotes, approvals, and commissioning records required.",
        ),
    )


def _configure_gantt_sheet(sheet: Worksheet) -> None:
    sheet.append(GANTT_HEADERS)
    _style_header_row(sheet)
    sheet.freeze_panes = "M2"
    sheet.auto_filter.ref = f"A1:{get_column_letter(len(GANTT_HEADERS))}1"
    _set_widths(sheet, (10, 24, 42, 14, 12, 10, 24, 28, 12, 18, 18, 56, *([4] * 52)))
    for column in range(13, 65):
        sheet.cell(row=1, column=column).alignment = Alignment(
            text_rotation=90,
            horizontal="center",
            vertical="bottom",
        )


def _append_gantt_task(sheet: Worksheet, task: GanttTask) -> None:
    row = sheet.max_row + 1
    sheet.append(
        (
            task.wbs,
            task.phase,
            task.task,
            task.duration_days,
            task.start_week,
            task.end_week,
            task.dependencies,
            task.responsible_party,
            task.risk_level,
            task.inspection_required,
            task.weather_sensitive,
            task.notes,
            *("" for _ in range(52)),
        )
    )
    for cell in sheet[row]:
        cell.alignment = Alignment(vertical="top", wrap_text=True)
    if task.risk_level == "High":
        sheet[f"I{row}"].fill = RISK_FILL
    for week in range(task.start_week, task.end_week + 1):
        cell = sheet.cell(row=row, column=12 + week)
        cell.value = "■"
        cell.fill = TIMELINE_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")


def _build_gantt_sheet(sheet: Worksheet, tasks: tuple[GanttTask, ...]) -> None:
    _configure_gantt_sheet(sheet)
    for task in tasks:
        _append_gantt_task(sheet, task)


def _build_phase_details_sheet(sheet: Worksheet, tasks: tuple[GanttTask, ...]) -> None:
    sheet.append(("WBS", "Phase", "Task", "Duration Days", "Window", "Responsible Party", "Notes"))
    _style_header_row(sheet)
    for task in tasks:
        sheet.append(
            (
                task.wbs,
                task.phase,
                task.task,
                task.duration_days,
                f"Week {task.start_week} to Week {task.end_week}",
                task.responsible_party,
                task.notes,
            )
        )
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:G{sheet.max_row}"
    _set_widths(sheet, (10, 28, 44, 14, 20, 32, 70))


def _build_milestones_sheet(sheet: Worksheet, tasks: tuple[GanttTask, ...]) -> None:
    sheet.append(("Milestone", "Target Week", "Related WBS", "Notes"))
    _style_header_row(sheet)
    milestones = (
        ("Professional review complete", 4, "1.0", "Proceed only with required licensed input."),
        ("Site ready for earthworks", 8, "2.0, 3.0", "Access and logistics confirmed."),
        ("Foundations complete", 14, "6.0", "Inspection and hold-point records required."),
        ("Weather-tight shell", 22, "8.0, 9.0", "Dry-in before interior closures."),
        ("MEP rough-ins complete", 27, "11.0, 12.0, 13.0", "Do not close walls before review."),
        ("Terrace complete", 38, "18.0", "Guard, drainage, waterproofing checks required."),
        ("Off-grid systems tested", 42, "20.0", "No autonomy guarantee implied."),
        ("Handover complete", 50, "22.0", "Commissioning and owner documentation complete."),
    )
    for row in milestones:
        sheet.append(row)
        sheet.cell(row=sheet.max_row, column=2).fill = MILESTONE_FILL
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:D{sheet.max_row}"
    _set_widths(sheet, (34, 14, 18, 70))


def _build_dependencies_sheet(sheet: Worksheet, tasks: tuple[GanttTask, ...]) -> None:
    sheet.append(("WBS", "Phase", "Dependencies", "Dependency Warning"))
    _style_header_row(sheet)
    for task in tasks:
        warning = (
            "No predecessor listed; verify readiness before starting."
            if not task.dependencies
            else "Starting before predecessors close may create rework, inspection, or safety risk."
        )
        sheet.append((task.wbs, task.phase, task.dependencies or "None listed", warning))
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:D{sheet.max_row}"
    _set_widths(sheet, (10, 30, 36, 78))


def _build_risks_sheet(sheet: Worksheet, tasks: tuple[GanttTask, ...]) -> None:
    sheet.append(("WBS", "Phase", "Risk Level", "Weather Sensitive", "Risk Notes"))
    _style_header_row(sheet)
    for task in tasks:
        notes = task.notes
        if task.weather_sensitive == "Yes":
            notes = f"{notes} Mountain weather can delay or resequence this phase."
        sheet.append((task.wbs, task.phase, task.risk_level, task.weather_sensitive, notes))
        if task.risk_level == "High":
            sheet.cell(row=sheet.max_row, column=3).fill = RISK_FILL
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:E{sheet.max_row}"
    _set_widths(sheet, (10, 30, 14, 18, 90))


def _build_inspections_sheet(
    sheet: Worksheet,
    config: MountainRetreatConfig,
    tasks: tuple[GanttTask, ...],
) -> None:
    sheet.append(("WBS/Checklist", "Phase", "Inspection Required", "Responsible Party", "Notes"))
    _style_header_row(sheet)
    for task in tasks:
        if task.inspection_required == "Yes":
            sheet.append((task.wbs, task.phase, "Yes", task.responsible_party, task.notes))
    for item in config.checklists_seed.checklist_items:
        sheet.append((item.id, item.phase, "Yes", item.responsible_party, item.inspection_item))
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:E{sheet.max_row}"
    _set_widths(sheet, (18, 32, 20, 34, 86))


def _build_weekly_cashflow_sheet(sheet: Worksheet, tasks: tuple[GanttTask, ...]) -> None:
    sheet.append(("Week", "Planned Activity Count", "Planning Cashflow Weight", "Notes"))
    _style_header_row(sheet)
    for week in range(1, 53):
        active_count = sum(1 for task in tasks if task.start_week <= week <= task.end_week)
        sheet.append(
            (
                f"Week {week}",
                active_count,
                f"=B{week + 1}/SUM($B$2:$B$53)",
                "Placeholder distribution only; contractor cashflow required.",
            )
        )
    total_row = sheet.max_row + 1
    sheet.append(("TOTAL", f"=SUM(B2:B{total_row - 1})", f"=SUM(C2:C{total_row - 1})", ""))
    for cell in sheet[total_row]:
        cell.font = BOLD_FONT
        cell.fill = SUBHEADER_FILL
    for cell in sheet["C"]:
        cell.number_format = "0.00%"
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:D{sheet.max_row}"
    _set_widths(sheet, (14, 24, 24, 70))


def _build_gantt_assumptions_sheet(sheet: Worksheet, config: MountainRetreatConfig) -> None:
    rows = (
        ("Project", config.project.project_name),
        ("Status", config.project.status),
        ("Disclaimer", config.project.disclaimer),
        ("Schedule duration", "12 months / 52 weeks"),
        ("Schedule basis", "Preliminary planning sequence only; not a contractor baseline."),
        ("Country", config.project.country),
        ("Climate zone", config.site.climate_zone),
        ("Altitude m", f"{config.site.altitude_m:g}"),
        ("Drainage risk", config.site.drainage_risk),
        ("Access road", config.site.access_road_type),
        ("Mountain weather note", "Snow, frost, rain, wind, and access limits can delay work."),
        (
            "Dependency warning",
            "Predecessor phases must be verified before starting dependent work.",
        ),
        ("Professional review", ", ".join(config.project.review_required_by)),
        ("YAML seed phases", str(len(config.construction_phases.phases))),
    )
    sheet.append(("Assumption", "Value"))
    _style_header_row(sheet)
    for row in rows:
        sheet.append(row)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:B{sheet.max_row}"
    _set_widths(sheet, (30, 100))
    for cell in sheet["B"]:
        cell.alignment = Alignment(wrap_text=True, vertical="top")


def _apply_gantt_workbook_metadata(workbook: Workbook, config: MountainRetreatConfig) -> None:
    workbook.properties.title = "Mountain Retreat X1 Preliminary Gantt Schedule"
    workbook.properties.subject = "Preliminary 52-week planning schedule"
    workbook.properties.creator = config.project.author
    workbook.properties.keywords = "PRELIMINARY, Gantt, not a contractor baseline"


def generate_gantt_schedule_workbook(config: MountainRetreatConfig, output_dir: Path) -> Path:
    """Generate the preliminary 52-week Gantt schedule workbook and return its path."""
    excel_dir = output_dir / GANTT_OUTPUT_DIR
    excel_dir.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    workbook.active.title = "Gantt"
    for sheet_name in GANTT_WORKBOOK_SHEETS[1:]:
        workbook.create_sheet(sheet_name)

    tasks = _default_gantt_tasks()
    _build_gantt_sheet(workbook["Gantt"], tasks)
    _build_phase_details_sheet(workbook["Phase_Details"], tasks)
    _build_milestones_sheet(workbook["Milestones"], tasks)
    _build_dependencies_sheet(workbook["Dependencies"], tasks)
    _build_risks_sheet(workbook["Risks"], tasks)
    _build_inspections_sheet(workbook["Inspections"], config, tasks)
    _build_weekly_cashflow_sheet(workbook["Cashflow_By_Week"], tasks)
    _build_gantt_assumptions_sheet(workbook["Assumptions"], config)
    _apply_gantt_workbook_metadata(workbook, config)

    path = excel_dir / GANTT_FILENAME
    workbook.save(path)
    return path
