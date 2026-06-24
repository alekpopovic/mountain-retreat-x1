"""Excel workbook exporters for preliminary planning documents."""

from collections.abc import Iterable
from pathlib import Path

from openpyxl import Workbook  # type: ignore[import-untyped]
from openpyxl.styles import Alignment, Font, PatternFill  # type: ignore[import-untyped]
from openpyxl.utils import get_column_letter  # type: ignore[import-untyped]
from openpyxl.worksheet.worksheet import Worksheet  # type: ignore[import-untyped]

from mountain_retreat_x1.config.loader import MountainRetreatConfig
from mountain_retreat_x1.models import CostItem, MaterialItem

BOM_FILENAME = "Mountain_Retreat_X1_BOM.xlsx"
COST_FILENAME = "Mountain_Retreat_X1_Cost_Estimate.xlsx"
BOM_OUTPUT_DIR = "excel"
COST_OUTPUT_DIR = "excel"

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
