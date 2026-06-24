"""Markdown volume generation using Jinja2."""

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mountain_retreat_x1.calculators import area_summary, cost_summary, quantity_summary
from mountain_retreat_x1.calculators.results import QuantityMap
from mountain_retreat_x1.config.loader import MountainRetreatConfig
from mountain_retreat_x1.models import Room

MARKDOWN_OUTPUT_DIR = "markdown"
TEMPLATE_NAME = "volume.md.j2"
ARCHITECTURAL_TEMPLATE_NAME = "architectural_package.md.j2"
DEFAULT_TEMPLATE_DIR = Path("docs/templates/markdown")


@dataclass(frozen=True)
class MarkdownSection:
    """A structured section inside a generated Markdown volume."""

    heading: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class MarkdownVolume:
    """Markdown volume specification."""

    filename: str
    title: str
    assumptions: tuple[str, ...]
    limitations: tuple[str, ...]
    required_review: tuple[str, ...]
    sections: tuple[MarkdownSection, ...]
    qa_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScheduleItem:
    """Door/window schedule item."""

    code: str
    location: str
    type: str
    approximate_size: str
    glazing_note: str
    thermal_performance_placeholder: str
    safety_glass_placeholder: str
    notes: str


@dataclass(frozen=True)
class ArchitecturalRoomSheet:
    """Room data for the architectural package."""

    code: str
    name: str
    floor: str
    area_m2: float
    length_m: float
    width_m: float
    function: str
    furniture_assumptions: str
    window_assumptions: str
    door_assumptions: str
    floor_finish: str
    wall_finish: str
    ceiling_finish: str
    light_point_count: int
    socket_count: int
    heating_type: str
    ventilation_type: str
    notes: str


def _shared_limitations(config: MountainRetreatConfig) -> tuple[str, ...]:
    return (
        config.project.disclaimer,
        (
            "Generated content is a planning aid only and must not be treated as "
            "construction documentation."
        ),
        (
            "Quantities, costs, schedules, and system descriptions require review "
            "against local conditions."
        ),
    )


def _shared_assumptions(config: MountainRetreatConfig) -> tuple[str, ...]:
    return (
        f"Project status is {config.project.status}.",
        f"Configured gross area is {config.building.gross_area_m2:g} m2.",
        f"Configured net area is {config.building.net_area_m2:g} m2.",
        f"Configured terrace area is {config.terrace.terrace_area_m2:g} m2.",
        f"Construction variant is {config.building.construction_variant}.",
        config.calculator_assumptions.warning,
    )


def _material_lines(config: MountainRetreatConfig, group: str) -> tuple[str, ...]:
    materials = (
        config.materials_core.materials
        if group == "core"
        else config.materials_mep.materials
    )
    return tuple(
        f"{item.code}: {item.name} ({item.base_quantity:g} {item.unit})"
        for item in materials
    )


def _phase_lines(config: MountainRetreatConfig) -> tuple[str, ...]:
    return tuple(
        (
            f"{phase.wbs} {phase.name}: {phase.duration_days} days; "
            f"responsible party: {phase.responsible_party}."
        )
        for phase in config.construction_phases.phases
    )


def _cost_metric_lines(costs: QuantityMap) -> tuple[str, ...]:
    total = costs["cost.total"]
    gross = costs["cost.per_m2.gross"]
    net = costs["cost.per_m2.net"]
    return (
        f"Total preliminary cost: {total.value:g} {total.unit}.",
        f"Cost per m2 gross: {gross.value:g} {gross.unit}.",
        f"Cost per m2 net: {net.value:g} {net.unit}.",
    )


def _furniture_assumptions(room_name: str, function: str) -> str:
    text = f"{room_name} / {function}".lower()
    if "entrance" in text or "vestibule" in text or "entry" in text:
        return "Coat storage, bench/drop zone, boot storage, and clear entry circulation TBD."
    if "kitchen" in text:
        return "Cabinetry, worktop, sink, appliance positions, and circulation clearances TBD."
    if "dining" in text:
        return "Dining table sized for occupancy assumption, with terrace circulation clearance."
    if "living" in text or "lounge" in text:
        return "Seating group oriented toward panoramic view, fireplace, and circulation paths."
    if "bedroom" in text:
        return "Bed, bedside storage, wardrobe/storage, and circulation clearances TBD."
    if "bathroom" in text or "wc" in text:
        return "Sanitary fixtures from plumbing fixture list; clearances require code review."
    if "technical" in text:
        return "MEP equipment zones, access clearances, wall space, and service routes TBD."
    if "laundry" in text or "storage" in text:
        return "Laundry/storage shelving, appliance zone, and service access TBD."
    if "stair" in text:
        return "Stair, landing, handrail, guard, and under-stair coordination TBD."
    return "Furniture layout to be confirmed during architectural design."


def _architectural_room_sheets(config: MountainRetreatConfig) -> tuple[ArchitecturalRoomSheet, ...]:
    rooms = [*config.rooms_ground_floor.rooms, *config.rooms_gallery.rooms]
    return tuple(
        ArchitecturalRoomSheet(
            code=room.code,
            name=room.name,
            floor=room.floor,
            area_m2=room.area_m2,
            length_m=room.length_m,
            width_m=room.width_m,
            function=room.function,
            furniture_assumptions=_furniture_assumptions(room.name, room.function),
            window_assumptions=(
                f"Configured total window area: {room.window_area_m2:g} m2; "
                "final dimensions, sill heights, and operation type TBD."
            ),
            door_assumptions=(
                f"Configured door count: {room.door_count}; final leaf sizes, swings, "
                "thresholds, and fire/acoustic ratings TBD."
            ),
            floor_finish=room.floor_finish,
            wall_finish=room.wall_finish,
            ceiling_finish=room.ceiling_finish,
            light_point_count=room.light_point_count,
            socket_count=room.socket_count,
            heating_type=room.heating_type,
            ventilation_type=room.ventilation_type,
            notes=room.notes,
        )
        for room in rooms
    )


def _window_type(window_area_m2: float) -> str:
    if window_area_m2 <= 0:
        return "No configured exterior window"
    if window_area_m2 >= 8:
        return "Panoramic glazing placeholder"
    if window_area_m2 >= 3:
        return "Large window/door glazing placeholder"
    return "Standard window placeholder"


def _window_schedule(config: MountainRetreatConfig) -> tuple[ScheduleItem, ...]:
    items: list[ScheduleItem] = []
    for room in [*config.rooms_ground_floor.rooms, *config.rooms_gallery.rooms]:
        if room.window_area_m2 <= 0:
            continue
        items.append(
            ScheduleItem(
                code=f"W-{room.code}",
                location=room.name,
                type=_window_type(room.window_area_m2),
                approximate_size=f"Configured glazed area: {room.window_area_m2:g} m2",
                glazing_note="Final glazing build-up, opening type, and solar control TBD.",
                thermal_performance_placeholder="U-value/SHGC target by energy review.",
                safety_glass_placeholder="Safety glass need to be reviewed by location and height.",
                notes="Derived from room.window_area_m2 YAML assumption.",
            )
        )
    return tuple(items)


def _door_schedule(config: MountainRetreatConfig) -> tuple[ScheduleItem, ...]:
    items: list[ScheduleItem] = []
    for room in [*config.rooms_ground_floor.rooms, *config.rooms_gallery.rooms]:
        if room.door_count <= 0:
            continue
        door_type = (
            "Exterior/terrace door placeholder"
            if room.floor == "ground_floor"
            else "Interior door placeholder"
        )
        items.append(
            ScheduleItem(
                code=f"D-{room.code}",
                location=room.name,
                type=door_type,
                approximate_size=f"Configured door count: {room.door_count}; dimensions TBD",
                glazing_note="Glazing only if required by final door design.",
                thermal_performance_placeholder=(
                    "Exterior doors require envelope performance review."
                ),
                safety_glass_placeholder="Safety glass placeholder where doors include glazing.",
                notes="Derived from room.door_count YAML assumption.",
            )
        )
    return tuple(items)


def _architectural_context(config: MountainRetreatConfig) -> dict[str, object]:
    calculated_areas = area_summary(config)
    rooms = _architectural_room_sheets(config)
    ground_floor_rooms = tuple(room for room in rooms if room.floor == "ground_floor")
    gallery_rooms = tuple(room for room in rooms if room.floor == "gallery")
    return {
        "project": config.project,
        "site": config.site,
        "building": config.building,
        "terrace": config.terrace,
        "assumptions": _shared_assumptions(config),
        "limitations": _shared_limitations(config),
        "rooms": rooms,
        "ground_floor_rooms": ground_floor_rooms,
        "gallery_rooms": gallery_rooms,
        "ground_floor_area": round(sum(room.area_m2 for room in ground_floor_rooms), 1),
        "gallery_area": round(sum(room.area_m2 for room in gallery_rooms), 1),
        "terrace_zone_names": ", ".join(zone.name for zone in config.terrace.zones),
        "window_schedule": _window_schedule(config),
        "door_schedule": _door_schedule(config),
        "facade_area": calculated_areas["facade_rough_area"].value,
        "roof_area": calculated_areas["roof_rough_area"].value,
        "total_window_area": round(
            sum(room.window_area_m2 for room in all_config_rooms(config)),
            1,
        ),
    }


def all_config_rooms(config: MountainRetreatConfig) -> list[Room]:
    """Return all configured room models."""
    return [*config.rooms_ground_floor.rooms, *config.rooms_gallery.rooms]


def _volume_specs(config: MountainRetreatConfig) -> tuple[MarkdownVolume, ...]:
    calculated_areas = area_summary(config)
    quantities = quantity_summary(config)
    costs = cost_summary(config)
    room_count = len(config.rooms_ground_floor.rooms) + len(config.rooms_gallery.rooms)
    terrace_zones = ", ".join(zone.name for zone in config.terrace.zones)

    return (
        MarkdownVolume(
            filename="01_project_charter.md",
            title="01 Project Charter",
            assumptions=_shared_assumptions(config),
            limitations=_shared_limitations(config),
            required_review=("Owner, architect, and local authority review",),
            sections=(
                MarkdownSection(
                    "Purpose",
                    (
                        "Define the preliminary planning scope for Mountain Retreat X1.",
                        (
                            "Coordinate assumptions before professional design and "
                            "permitting workflows."
                        ),
                    ),
                ),
                MarkdownSection(
                    "Project Snapshot",
                    (
                        f"Country: {config.project.country}.",
                        f"Currency: {config.project.currency}.",
                        f"Language: {config.project.language}.",
                        f"Rooms configured: {room_count}.",
                    ),
                ),
            ),
            qa_notes=("Confirm project metadata before issuing any planning package.",),
        ),
        MarkdownVolume(
            filename="02_architectural_package.md",
            title="02 Architectural Package",
            assumptions=_shared_assumptions(config),
            limitations=_shared_limitations(config),
            required_review=("Licensed architect", "Local planning/permitting authority"),
            sections=(
                MarkdownSection(
                    "Spatial Program",
                    (
                        f"Ground floor rooms: {len(config.rooms_ground_floor.rooms)}.",
                        f"Gallery rooms: {len(config.rooms_gallery.rooms)}.",
                        (
                            "Calculated room area: "
                            f"{calculated_areas['calculated_net_area'].value:g} m2."
                        ),
                        (
                            "Difference versus configured net area: "
                            f"{calculated_areas['net_area_difference'].value:g} m2."
                        ),
                    ),
                ),
                MarkdownSection(
                    "Terrace Concept",
                    (
                        f"Terrace planning zones: {terrace_zones}.",
                        (
                            "Guards, waterproofing, drainage, and exterior finishes "
                            "require detailed design."
                        ),
                    ),
                ),
            ),
            qa_notes=(
                "Review room data sheets and terrace access before schematic drawing generation.",
            ),
        ),
        MarkdownVolume(
            filename="03_structural_concept.md",
            title="03 Structural Concept",
            assumptions=_shared_assumptions(config),
            limitations=_shared_limitations(config),
            required_review=("Licensed structural engineer", "Geotechnical professional"),
            sections=(
                MarkdownSection(
                    "Preliminary Structural Quantities",
                    (
                        f"Concrete estimate: {quantities['qty.concrete.volume'].value:g} m3.",
                        f"Rebar estimate: {quantities['qty.rebar.mass'].value:g} kg.",
                        (
                            "Timber framing estimate: "
                            f"{quantities['qty.timber.standard_hybrid'].value:g} m3."
                        ),
                    ),
                ),
                MarkdownSection(
                    "Review Triggers",
                    (
                        "Snow, wind, seismic, slope, soil, and terrace loads are placeholders.",
                        "No generated structural calculation is final or signed.",
                    ),
                ),
            ),
            qa_notes=("Block use of this volume as a final structural calculation package.",),
        ),
        MarkdownVolume(
            filename="04_electrical_package.md",
            title="04 Electrical Package",
            assumptions=_shared_assumptions(config),
            limitations=_shared_limitations(config),
            required_review=("Licensed electrical engineer",),
            sections=(
                MarkdownSection(
                    "Electrical Planning Scope",
                    (
                        "Room socket and light-point counts come from YAML room data.",
                        "PV, battery, generator, smart-home, and terrace circuits are preliminary.",
                    ),
                ),
                MarkdownSection(
                    "Known Coordination Items",
                    (
                        f"Optional PV array: {config.off_grid.pv_kwp:g} kWp.",
                        f"Optional battery storage: {config.off_grid.battery_kwh:g} kWh.",
                        "Final load calculations and protection design are excluded.",
                    ),
                ),
            ),
            qa_notes=("Confirm all electrical notes preserve licensed-review requirements.",),
        ),
        MarkdownVolume(
            filename="05_plumbing_wastewater.md",
            title="05 Plumbing and Wastewater",
            assumptions=_shared_assumptions(config),
            limitations=_shared_limitations(config),
            required_review=(
                "Licensed plumbing/mechanical engineer",
                "Local water/wastewater authority",
            ),
            sections=(
                MarkdownSection(
                    "Water Planning",
                    (
                        f"Optional water tank: {config.off_grid.water_tank_l:,} L.",
                        "Potable water quality, pressure, freezing, and pump sizing are not final.",
                    ),
                ),
                MarkdownSection(
                    "Wastewater Planning",
                    tuple(config.off_grid.wastewater_options),
                ),
            ),
            qa_notes=(
                "Confirm wastewater assumptions with local authority before any design reliance.",
            ),
        ),
        MarkdownVolume(
            filename="06_hvac_package.md",
            title="06 HVAC Package",
            assumptions=_shared_assumptions(config),
            limitations=_shared_limitations(config),
            required_review=("Licensed mechanical engineer",),
            sections=(
                MarkdownSection(
                    "Heating Concept",
                    (
                        (
                            "Heating assumption: air-to-water heat pump + underfloor "
                            "heating + fireplace."
                        ),
                        (
                            "Heat-loss, ventilation, chimney, and combustion-air "
                            "calculations are excluded."
                        ),
                    ),
                ),
                MarkdownSection(
                    "Room Coordination",
                    (
                        "Heating and ventilation types are listed in room data sheets.",
                        "Wet rooms require mechanical extract review.",
                    ),
                ),
            ),
            qa_notes=("Do not treat HVAC descriptions as final equipment sizing.",),
        ),
        MarkdownVolume(
            filename="07_smart_home_security.md",
            title="07 Smart Home and Security",
            assumptions=_shared_assumptions(config),
            limitations=_shared_limitations(config),
            required_review=("Licensed electrical engineer", "Smart-home integrator"),
            sections=(
                MarkdownSection(
                    "Platform",
                    (
                        f"Platform: {config.smart_home.platform}.",
                        f"Protocols: {', '.join(config.smart_home.protocols)}.",
                        (
                            "Rack location assumption: "
                            f"{config.smart_home.network_assumptions['rack_location']}."
                        ),
                    ),
                ),
                MarkdownSection("Systems", tuple(config.smart_home.systems)),
            ),
            qa_notes=("Verify life-safety/security claims are not overstated.",),
        ),
        MarkdownVolume(
            filename="08_off_grid_package.md",
            title="08 Off-Grid Package",
            assumptions=_shared_assumptions(config),
            limitations=(*_shared_limitations(config), *tuple(config.off_grid.limitations)),
            required_review=("Licensed electrical engineer", "Water/wastewater authority"),
            sections=(
                MarkdownSection(
                    "Optional Energy Package",
                    (
                        f"PV: {config.off_grid.pv_kwp:g} kWp.",
                        f"Battery: {config.off_grid.battery_kwh:g} kWh.",
                        f"Generator: {config.off_grid.generator}.",
                    ),
                ),
                MarkdownSection("Water and Wastewater", tuple(config.off_grid.wastewater_options)),
            ),
            qa_notes=("Confirm off-grid package remains optional and preliminary.",),
        ),
        MarkdownVolume(
            filename="09_bom_summary.md",
            title="09 BOM Summary",
            assumptions=_shared_assumptions(config),
            limitations=_shared_limitations(config),
            required_review=("Architect", "Structural engineer", "MEP engineers", "Contractor"),
            sections=(
                MarkdownSection(
                    "Core Material Groups",
                    _material_lines(config, "core"),
                ),
                MarkdownSection(
                    "MEP Material Groups",
                    _material_lines(config, "mep"),
                ),
            ),
            qa_notes=("Verify every BOM quantity has a formula note or assumption reference.",),
        ),
        MarkdownVolume(
            filename="10_cost_estimate_summary.md",
            title="10 Cost Estimate Summary",
            assumptions=(
                *_shared_assumptions(config),
                config.cost_assumptions_serbia_2026.source_policy,
                config.cost_assumptions_serbia_2026.estimate_warning,
            ),
            limitations=_shared_limitations(config),
            required_review=("Qualified contractor or cost estimator",),
            sections=(
                MarkdownSection(
                    "Calculated Cost Metrics",
                    _cost_metric_lines(costs),
                ),
                MarkdownSection(
                    "Cost Notes",
                    (
                        f"Assumption year: {config.cost_assumptions_serbia_2026.assumption_year}.",
                        f"VAT included: {config.cost_assumptions_serbia_2026.vat_included}.",
                        (
                            "Contingency: "
                            f"{config.cost_assumptions_serbia_2026.contingency_percent:g}%."
                        ),
                    ),
                ),
            ),
            qa_notes=("Do not present static planning costs as live prices or contractor quotes.",),
        ),
        MarkdownVolume(
            filename="11_construction_management.md",
            title="11 Construction Management",
            assumptions=_shared_assumptions(config),
            limitations=_shared_limitations(config),
            required_review=("Contractor", "Site safety coordinator", "Licensed design team"),
            sections=(
                MarkdownSection(
                    "Planning Phases",
                    _phase_lines(config),
                ),
                MarkdownSection(
                    "Safety Coordination",
                    (
                        "A real construction safety plan is required before work.",
                        (
                            "Mountain access, weather, lifting, excavation, and terrace "
                            "work require site-specific planning."
                        ),
                    ),
                ),
            ),
            qa_notes=("Confirm schedule remains a preliminary management aid.",),
        ),
        MarkdownVolume(
            filename="12_maintenance_manual.md",
            title="12 Maintenance Manual",
            assumptions=_shared_assumptions(config),
            limitations=_shared_limitations(config),
            required_review=("Architect", "MEP engineers", "Owner/operator"),
            sections=(
                MarkdownSection(
                    "Seasonal Maintenance",
                    (
                        (
                            "Inspect standing seam roof, gutters, snow guards, and "
                            "terrace drainage before winter."
                        ),
                        "Check timber, stone, and glass facade interfaces for water ingress.",
                        (
                            "Review heat pump, underfloor heating, fireplace, and "
                            "ventilation service requirements."
                        ),
                    ),
                ),
                MarkdownSection(
                    "Smart and Off-Grid Systems",
                    (
                        "Back up Home Assistant configuration after commissioning.",
                        (
                            "Inspect PV, battery, generator, and water systems per "
                            "manufacturer guidance."
                        ),
                    ),
                ),
            ),
            qa_notes=(
                (
                    "Replace planning maintenance notes with manufacturer and "
                    "professional guidance later."
                ),
            ),
        ),
        MarkdownVolume(
            filename="13_self_build_guide.md",
            title="13 Self-Build Guide",
            assumptions=_shared_assumptions(config),
            limitations=_shared_limitations(config),
            required_review=("Licensed professionals", "Contractor or qualified site supervisor"),
            sections=(
                MarkdownSection(
                    "Appropriate Self-Build Scope",
                    (
                        "Use this guide only to understand sequencing and documentation needs.",
                        (
                            "Do not self-perform structural, electrical, mechanical, fire, "
                            "or wastewater work without required qualifications and approvals."
                        ),
                    ),
                ),
                MarkdownSection(
                    "Preparation Checklist",
                    (
                        "Confirm drawings and permits through local processes.",
                        (
                            "Confirm site safety plan, insurance, access, weather windows, "
                            "and inspections."
                        ),
                    ),
                ),
            ),
            qa_notes=("Keep self-build guidance conservative and safety-first.",),
        ),
        MarkdownVolume(
            filename="14_legal_and_professional_limits.md",
            title="14 Legal and Professional Limits",
            assumptions=_shared_assumptions(config),
            limitations=_shared_limitations(config),
            required_review=tuple(config.project.review_required_by),
            sections=(
                MarkdownSection(
                    "Non-Replacement Statement",
                    (
                        "This package does not replace licensed architects or engineers.",
                        "This package does not replace local permitting authorities.",
                        "This package does not create permits, approvals, stamps, or signatures.",
                    ),
                ),
                MarkdownSection(
                    "Use Restrictions",
                    (
                        "Do not use generated documents for construction.",
                        "Do not use generated documents as final structural calculations.",
                        "Do not use generated documents as legal approval.",
                    ),
                ),
            ),
            qa_notes=("This volume must remain present in every final document package.",),
        ),
    )


def _environment(template_dir: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def generate_markdown_volumes(
    config: MountainRetreatConfig,
    output_dir: Path,
    template_dir: Path = DEFAULT_TEMPLATE_DIR,
) -> list[Path]:
    """Generate all Markdown source volumes and return their paths."""
    markdown_dir = output_dir / MARKDOWN_OUTPUT_DIR
    markdown_dir.mkdir(parents=True, exist_ok=True)

    env = _environment(template_dir)
    template = env.get_template(TEMPLATE_NAME)
    architectural_template = env.get_template(ARCHITECTURAL_TEMPLATE_NAME)
    paths: list[Path] = []
    for volume in _volume_specs(config):
        if volume.filename == "02_architectural_package.md":
            rendered = architectural_template.render(**_architectural_context(config))
        else:
            rendered = template.render(project=config.project, volume=volume)
        path = markdown_dir / volume.filename
        path.write_text(rendered, encoding="utf-8")
        paths.append(path)

    return paths
