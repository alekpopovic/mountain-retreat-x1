"""Markdown volume generation using Jinja2."""

from dataclasses import dataclass, replace
from pathlib import Path
from typing import cast

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mountain_retreat_x1.calculators import area_summary, cost_summary, quantity_summary
from mountain_retreat_x1.calculators.results import QuantityMap
from mountain_retreat_x1.config.loader import MountainRetreatConfig
from mountain_retreat_x1.localization import load_translator
from mountain_retreat_x1.models import Room

MARKDOWN_OUTPUT_DIR = "markdown"
TEMPLATE_NAME = "volume.md.j2"
ARCHITECTURAL_TEMPLATE_NAME = "architectural_package.md.j2"
STRUCTURAL_TEMPLATE_NAME = "structural_concept.md.j2"
ELECTRICAL_TEMPLATE_NAME = "electrical_package.md.j2"
PLUMBING_TEMPLATE_NAME = "plumbing_wastewater.md.j2"
HVAC_TEMPLATE_NAME = "hvac_package.md.j2"
SMART_HOME_TEMPLATE_NAME = "smart_home_security.md.j2"
OFF_GRID_TEMPLATE_NAME = "off_grid_package.md.j2"
MAINTENANCE_TEMPLATE_NAME = "maintenance_manual.md.j2"
SELF_BUILD_TEMPLATE_NAME = "self_build_guide.md.j2"
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


@dataclass(frozen=True)
class StructuralVariant:
    """Structural variant comparison item."""

    title: str
    advantages: tuple[str, ...]
    disadvantages: tuple[str, ...]
    procurement_complexity: str
    self_build_difficulty: str
    risk_level: str
    preliminary_materials: tuple[str, ...]
    licensed_engineering_required: tuple[str, ...]


@dataclass(frozen=True)
class CircuitItem:
    """Preliminary electrical circuit schedule item."""

    code: str
    area_room: str
    load_type: str
    estimated_load_category: str
    breaker_placeholder: str
    cable_placeholder: str
    rcd_rcbo_placeholder: str
    notes: str
    review_required: str


@dataclass(frozen=True)
class FixtureItem:
    """Preliminary plumbing fixture schedule item."""

    code: str
    room: str
    fixture_type: str
    cold_water_required: str
    hot_water_required: str
    waste_required: str
    trap_vent_note: str
    freeze_risk: str
    notes: str


@dataclass(frozen=True)
class HvacZoneItem:
    """Preliminary heating zone schedule item."""

    zone_code: str
    room: str
    area: str
    design_temperature_placeholder: str
    floor_heating_loop_placeholder: str
    thermostat_required: str
    notes: str


@dataclass(frozen=True)
class HvacEquipmentItem:
    """Preliminary HVAC equipment schedule item."""

    equipment: str
    location: str
    purpose: str
    power_capacity_placeholder: str
    electrical_dependency: str
    maintenance_interval: str
    notes: str


@dataclass(frozen=True)
class SmartHomeDeviceItem:
    """Preliminary smart-home device schedule item."""

    device_code: str
    device_type: str
    room_location: str
    protocol: str
    power_source: str
    network_dependency: str
    automation_role: str
    priority: str
    notes: str


@dataclass(frozen=True)
class SensorScheduleItem:
    """Preliminary smart-home sensor schedule item."""

    sensor_code: str
    sensor_type: str
    room_location: str
    protocol: str
    alert_route: str
    priority: str
    notes: str


@dataclass(frozen=True)
class AutomationItem:
    """Preliminary smart-home automation item."""

    code: str
    name: str
    trigger: str
    action: str
    dependencies: str
    safety_note: str


@dataclass(frozen=True)
class LoadEstimateItem:
    """Preliminary off-grid load estimate item."""

    load_code: str
    device_system: str
    power_w_placeholder: str
    hours_day_placeholder: str
    daily_kwh_placeholder: str
    critical: str
    backup_priority: str
    notes: str


@dataclass(frozen=True)
class FailureScenarioItem:
    """Preliminary off-grid failure scenario item."""

    scenario: str
    likely_impact: str
    manual_response: str
    automation_monitoring: str
    professional_review: str


@dataclass(frozen=True)
class MaintenanceTask:
    """Maintenance task for the 30-year manual."""

    section: str
    task: str
    frequency: str
    responsible_person: str
    estimated_effort: str
    required_tools: str
    warning_signs: str
    notes: str


@dataclass(frozen=True)
class SelfBuildStep:
    """Step entry for the preliminary self-build planning guide."""

    number: int
    phase_number: int
    phase_title: str
    name: str
    objective: str
    prerequisites: tuple[str, ...]
    materials: tuple[str, ...]
    tools: tuple[str, ...]
    people_trades_required: tuple[str, ...]
    approximate_duration: str
    procedure: tuple[str, ...]
    quality_checks: tuple[str, ...]
    safety_risks: tuple[str, ...]
    common_mistakes: tuple[str, ...]
    professional_stop_point: str
    photos_documents: tuple[str, ...]


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
        config.materials_core.materials if group == "core" else config.materials_mep.materials
    )
    return tuple(
        f"{item.code}: {item.name} ({item.base_quantity:g} {item.unit})" for item in materials
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


def _architectural_context(
    config: MountainRetreatConfig,
    *,
    large_mode: bool = False,
) -> dict[str, object]:
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
        "large_mode": large_mode,
    }


def _structural_variants(config: MountainRetreatConfig) -> tuple[StructuralVariant, ...]:
    return (
        StructuralVariant(
            title="Variant A: standard timber hybrid",
            advantages=(
                "Good fit for the configured standard_hybrid assumption.",
                "Warm mountain-cabin expression with efficient prefabrication potential.",
                "Can combine timber superstructure with reinforced concrete foundation/slab zones.",
            ),
            disadvantages=(
                "Requires careful moisture, fire, acoustic, and connection detailing.",
                "Large glazing and terrace interfaces may need steel or engineered timber support.",
                "Quality depends heavily on shop drawings and site protection from weather.",
            ),
            procurement_complexity=(
                "Medium; regional timber supplier and engineer coordination required."
            ),
            self_build_difficulty=(
                "High; limited to non-structural tasks unless qualified and approved."
            ),
            risk_level="Medium, with elevated terrace and moisture-interface risks.",
            preliminary_materials=(
                "Reinforced concrete foundation placeholder",
                "Hybrid timber frame package",
                "Engineered connectors and hold-downs, final selection by engineer",
                "Standing seam metal roof over engineered roof structure",
            ),
            licensed_engineering_required=(
                "Final load path and lateral stability design",
                "Beam, column, joist, rafter, lintel, and connection sizing",
                "Foundation/slab reinforcement and anchorage design",
                "Terrace support, guards, and waterproofing interfaces",
            ),
        ),
        StructuralVariant(
            title="Variant B: premium CLT/glulam",
            advantages=(
                "High prefabrication potential and dimensional precision.",
                "Fast enclosure if procurement and crane access are feasible.",
                "Strong architectural expression for exposed timber interiors.",
            ),
            disadvantages=(
                "Higher procurement complexity and supplier dependency.",
                "Requires early coordination of openings, penetrations, lifting, and transport.",
                "Mountain access roads may constrain panel size and crane logistics.",
            ),
            procurement_complexity=(
                "High; specialist CLT/glulam supplier and logistics planning required."
            ),
            self_build_difficulty="Very high; not suitable for informal self-build structure work.",
            risk_level=(
                "Medium-high due to logistics, weather protection, and interface coordination."
            ),
            preliminary_materials=(
                "CLT wall/floor/roof panel placeholders",
                "Glulam beams/columns where required",
                "Specialist steel connectors and hold-downs",
                "Temporary weather protection during erection",
            ),
            licensed_engineering_required=(
                "Panel thickness, spans, openings, vibration, and diaphragm design",
                "Fire resistance and char-rate strategy",
                "Connection, lifting, temporary bracing, and erection sequence design",
                "Foundation interface and moisture separation details",
            ),
        ),
        StructuralVariant(
            title="Variant C: masonry hybrid",
            advantages=(
                "Potentially familiar trades and robust wall mass.",
                "Good thermal mass potential when properly insulated and detailed.",
                "Can suit stone/timber/glass facade expression with hybrid framing.",
            ),
            disadvantages=(
                "Heavier structure increases foundation and seismic design importance.",
                "Thermal bridges and moisture detailing require careful professional design.",
                "Large openings and panoramic glazing may require engineered lintels/frames.",
            ),
            procurement_complexity=(
                "Medium; common materials but detailed engineering coordination needed."
            ),
            self_build_difficulty="High; structural masonry work requires qualified supervision.",
            risk_level="Medium-high in seismic, slope, frost, and moisture conditions.",
            preliminary_materials=(
                "Masonry block wall placeholder",
                "Reinforced concrete foundation and slab placeholders",
                "Engineered lintels/ring beams/vertical reinforcement placeholders",
                "Hybrid roof and terrace support system",
            ),
            licensed_engineering_required=(
                "Wall thickness, reinforcement, lintels, ring beams, and lateral stability",
                "Seismic detailing and anchorage",
                "Foundation sizing and frost/drainage detailing",
                "Openings, terrace loads, and roof-to-wall connections",
            ),
        ),
    )


def _structural_context(config: MountainRetreatConfig) -> dict[str, object]:
    quantities = quantity_summary(config)
    roof_area = area_summary(config)["roof_rough_area"]
    return {
        "project": config.project,
        "site": config.site,
        "building": config.building,
        "terrace": config.terrace,
        "assumptions": _shared_assumptions(config),
        "limitations": _shared_limitations(config),
        "variants": _structural_variants(config),
        "quantities": quantities,
        "roof_area": roof_area,
        "foundation_depth_m": config.calculator_assumptions.foundation_depth_m,
        "gravel_depth_m": config.calculator_assumptions.gravel_depth_m,
        "frost_depth_cm": config.site.frost_depth_placeholder_cm,
        "snow_load": config.site.snow_load_placeholder_kn_m2,
        "wind_load": config.site.wind_load_placeholder_kn_m2,
        "seismic_zone": config.site.seismic_zone_placeholder,
    }


def _room_load_category(room: Room, load_type: str) -> str:
    text = f"{room.name} {room.function} {load_type}".lower()
    if "kitchen" in text or "technical" in text or "heat pump" in text:
        return "dedicated/high coordination placeholder"
    if "bathroom" in text or "laundry" in text or room.plumbing_fixtures:
        return "wet-area protected circuit placeholder"
    if "lighting" in text:
        return "low lighting load placeholder"
    if room.socket_count >= 8:
        return "medium socket load placeholder"
    return "general small-power placeholder"


def _room_circuits(config: MountainRetreatConfig) -> tuple[CircuitItem, ...]:
    circuits: list[CircuitItem] = []
    index = 1
    for room in all_config_rooms(config):
        circuits.append(
            CircuitItem(
                code=f"EL-{index:03d}",
                area_room=room.name,
                load_type="Lighting",
                estimated_load_category=_room_load_category(room, "lighting"),
                breaker_placeholder="Breaker TBD by licensed electrician",
                cable_placeholder="Cable size TBD by licensed electrician",
                rcd_rcbo_placeholder="RCD/RCBO TBD by licensed electrician",
                notes=(
                    f"Configured light points: {room.light_point_count}; switching, dimming, "
                    "emergency/egress needs, and controls are preliminary."
                ),
                review_required="Licensed electrician / electrical engineer",
            )
        )
        index += 1
        circuits.append(
            CircuitItem(
                code=f"EL-{index:03d}",
                area_room=room.name,
                load_type="Sockets / small power",
                estimated_load_category=_room_load_category(room, "sockets"),
                breaker_placeholder="Breaker TBD by licensed electrician",
                cable_placeholder="Cable size TBD by licensed electrician",
                rcd_rcbo_placeholder="RCD/RCBO TBD by licensed electrician",
                notes=(
                    f"Configured socket count: {room.socket_count}; outlet locations, "
                    "dedicated loads, and code spacing are preliminary."
                ),
                review_required="Licensed electrician / electrical engineer",
            )
        )
        index += 1
        if (
            room.plumbing_fixtures
            or "bathroom" in room.name.lower()
            or "laundry" in room.name.lower()
        ):
            circuits.append(
                CircuitItem(
                    code=f"EL-{index:03d}",
                    area_room=room.name,
                    load_type="Wet-area equipment / extract / appliance placeholder",
                    estimated_load_category="wet-area protected circuit placeholder",
                    breaker_placeholder="Breaker TBD by licensed electrician",
                    cable_placeholder="Cable size TBD by licensed electrician",
                    rcd_rcbo_placeholder="RCD/RCBO mandatory review placeholder",
                    notes=(
                        "Wet-area bonding, zoning, appliance loads, ventilation, and IP ratings "
                        "must be reviewed against local electrical rules."
                    ),
                    review_required="Licensed electrician / electrical engineer",
                )
            )
            index += 1
    return tuple(circuits)


def _system_circuits(config: MountainRetreatConfig) -> tuple[CircuitItem, ...]:
    circuits: list[CircuitItem] = []
    base = 900
    terrace_names = ", ".join(zone.name for zone in config.terrace.zones)
    system_rows = (
        (
            "Terrace and exterior",
            "Weather-exposed lighting and sockets",
            "exterior protected circuit placeholder",
            f"Terrace zones: {terrace_names}. Weatherproof equipment and RCD/RCBO review required.",
        ),
        (
            "Technical room",
            "Heat pump / underfloor heating controls",
            "dedicated mechanical equipment placeholder",
            "Final heat-pump and controls loads require HVAC/electrical coordination.",
        ),
        (
            "Off-grid option",
            "Backup generator",
            "standby generation placeholder",
            f"Generator assumption: {config.off_grid.generator}. Transfer switching TBD.",
        ),
        (
            "Off-grid option",
            "Solar PV integration",
            "PV inverter placeholder",
            f"PV assumption: {config.off_grid.pv_kwp:g} kWp. Grid/utility approval not implied.",
        ),
        (
            "Off-grid option",
            "Battery integration",
            "battery inverter/storage placeholder",
            (
                f"Battery assumption: {config.off_grid.battery_kwh:g} kWh. "
                "Protection and ventilation TBD."
            ),
        ),
        (
            "Smart home",
            "Controls/network/security",
            "low-voltage and controls placeholder",
            (
                f"Platform: {config.smart_home.platform}; protocols: "
                f"{', '.join(config.smart_home.protocols)}."
            ),
        ),
    )
    for offset, (area_room, load_type, category, notes) in enumerate(system_rows):
        circuits.append(
            CircuitItem(
                code=f"EL-{base + offset:03d}",
                area_room=area_room,
                load_type=load_type,
                estimated_load_category=category,
                breaker_placeholder="Breaker TBD by licensed electrician",
                cable_placeholder="Cable size TBD by licensed electrician",
                rcd_rcbo_placeholder="RCD/RCBO/SPD coordination TBD",
                notes=notes,
                review_required="Licensed electrician / electrical engineer",
            )
        )
    return tuple(circuits)


def _electrical_context(config: MountainRetreatConfig) -> dict[str, object]:
    room_circuits = _room_circuits(config)
    system_circuits = _system_circuits(config)
    all_circuits = (*room_circuits, *system_circuits)
    major_rooms = (
        "Kitchen",
        "Dining",
        "Living room",
        "Fireplace zone",
        "Technical room",
        "Guest bathroom",
        "Master bathroom",
        "Bathroom 2",
        "Terrace",
    )
    return {
        "project": config.project,
        "building": config.building,
        "terrace": config.terrace,
        "smart_home": config.smart_home,
        "off_grid": config.off_grid,
        "assumptions": _shared_assumptions(config),
        "limitations": _shared_limitations(config),
        "rooms": all_config_rooms(config),
        "room_circuits": room_circuits,
        "system_circuits": system_circuits,
        "circuits": all_circuits,
        "major_rooms": major_rooms,
        "total_socket_count": sum(room.socket_count for room in all_config_rooms(config)),
        "total_light_points": sum(room.light_point_count for room in all_config_rooms(config)),
    }


def _fixture_connections(fixture_type: str) -> tuple[str, str, str, str]:
    name = fixture_type.lower()
    cold = "Yes"
    hot = "Yes"
    waste = "Yes"
    trap_vent = "Trap and venting TBD by licensed plumbing/mechanical designer"
    if "wc" in name or "toilet" in name:
        hot = "No"
        trap_vent = "Soil stack, trap seal, and venting route TBD"
    elif "floor drain" in name:
        cold = "No"
        hot = "No"
        trap_vent = "Trap primer/freeze protection and venting TBD"
    elif "dishwasher" in name or "washing machine" in name:
        hot = "No/TBD"
        trap_vent = "Appliance trap, standpipe, backflow, and venting TBD"
    elif "tap" in name or "hose" in name:
        hot = "No/TBD"
        waste = "No, unless connected to drained exterior worktop"
        trap_vent = "Backflow prevention and winter shutoff/drain-down TBD"
    elif "jacuzzi" in name or "spa" in name:
        trap_vent = "Dedicated drainage, backflow, isolation, and maintenance access TBD"
    return cold, hot, waste, trap_vent


def _fixture_freeze_risk(room_name: str, fixture_type: str, config: MountainRetreatConfig) -> str:
    room_text = room_name.lower()
    fixture_text = fixture_type.lower()
    if any(marker in room_text for marker in ("terrace", "exterior", "outdoor")):
        return (
            f"High; exterior exposure and frost depth placeholder "
            f"{config.site.frost_depth_placeholder_cm:g} cm require winterization."
        )
    if any(marker in fixture_text for marker in ("tap", "hose", "jacuzzi", "spa")):
        return "High; exposed or intermittently heated plumbing requires drain-down."
    if "technical" in room_text:
        return "Medium; frost protection must remain active during vacancy."
    return "Medium; pipe routes in external walls or cold voids must be avoided."


def _fixture_notes(room_name: str, fixture_type: str) -> str:
    name = fixture_type.lower()
    if "wc" in name or "toilet" in name:
        return "Confirm soil pipe route, acoustic treatment, cleanouts, and service access."
    if "shower" in name:
        return "Confirm waterproofing, falls to drain, access to trap, and extract ventilation."
    if "washbasin" in name or "sink" in name:
        return "Confirm shutoff valves, splash protection, trap access, and fixture support."
    if "dishwasher" in name:
        return (
            "Confirm appliance valve, waste connection, leak protection, and "
            "electrical coordination."
        )
    if "washing machine" in name:
        return "Confirm valve box, standpipe, overflow risk, vibration, and floor drain strategy."
    if "floor drain" in name:
        return "Confirm trap seal protection, waterproofing interface, and cleanout access."
    if "tap" in name or "hose" in name:
        return (
            "Confirm backflow protection, isolation valve, winter drain-down, and slope to drain."
        )
    if "jacuzzi" in name or "spa" in name:
        return (
            "Placeholder only; requires structural, electrical, waterproofing, and drainage design."
        )
    return f"Confirm final fixture requirements for {room_name}."


def _wet_rooms(config: MountainRetreatConfig) -> tuple[Room, ...]:
    return tuple(room for room in all_config_rooms(config) if room.plumbing_fixtures)


def _fixture_schedule(config: MountainRetreatConfig) -> tuple[FixtureItem, ...]:
    fixtures: list[FixtureItem] = []
    index = 1
    for room in _wet_rooms(config):
        for fixture in room.plumbing_fixtures:
            cold, hot, waste, trap_vent = _fixture_connections(fixture)
            fixtures.append(
                FixtureItem(
                    code=f"PL-{index:03d}",
                    room=room.name,
                    fixture_type=fixture,
                    cold_water_required=cold,
                    hot_water_required=hot,
                    waste_required=waste,
                    trap_vent_note=trap_vent,
                    freeze_risk=_fixture_freeze_risk(room.name, fixture, config),
                    notes=_fixture_notes(room.name, fixture),
                )
            )
            index += 1

    exterior_items = (
        ("Terrace", "exterior hose tap / outdoor kitchen water placeholder"),
        ("Terrace BBQ/outdoor kitchen", "outdoor sink placeholder"),
        ("Jacuzzi-ready terrace zone", "jacuzzi/spa water and drain placeholder"),
    )
    for room_name, fixture in exterior_items:
        cold, hot, waste, trap_vent = _fixture_connections(fixture)
        fixtures.append(
            FixtureItem(
                code=f"PL-{index:03d}",
                room=room_name,
                fixture_type=fixture,
                cold_water_required=cold,
                hot_water_required=hot,
                waste_required=waste,
                trap_vent_note=trap_vent,
                freeze_risk=_fixture_freeze_risk(room_name, fixture, config),
                notes=_fixture_notes(room_name, fixture),
            )
        )
        index += 1

    return tuple(fixtures)


def _plumbing_context(config: MountainRetreatConfig) -> dict[str, object]:
    wet_rooms = _wet_rooms(config)
    fixtures = _fixture_schedule(config)
    terrace_plumbing_zones = tuple(
        zone
        for zone in config.terrace.zones
        if any(
            "water" in item.lower() or "drain" in item.lower() for item in zone.utility_requirements
        )
    )
    return {
        "project": config.project,
        "site": config.site,
        "building": config.building,
        "terrace": config.terrace,
        "off_grid": config.off_grid,
        "assumptions": _shared_assumptions(config),
        "limitations": _shared_limitations(config),
        "wet_rooms": wet_rooms,
        "fixtures": fixtures,
        "terrace_plumbing_zones": terrace_plumbing_zones,
        "wet_room_count": len(wet_rooms),
        "fixture_count": len(fixtures),
    }


def _design_temperature_placeholder(room: Room) -> str:
    room_text = f"{room.name} {room.zone} {room.function}".lower()
    if "bathroom" in room_text or "sanitary" in room_text:
        return "24 C placeholder, final by heat-loss calculation"
    if "bedroom" in room_text or "sleeping" in room_text:
        return "20 C placeholder, final by comfort brief"
    if "technical" in room_text:
        return "10-18 C placeholder, frost and equipment needs TBD"
    if "laundry" in room_text or "storage" in room_text:
        return "18-20 C placeholder, final by use and ventilation"
    if "entrance" in room_text or "vestibule" in room_text:
        return "18 C placeholder, final by envelope and air leakage"
    return "21 C placeholder, final by mechanical engineer"


def _thermostat_requirement(room: Room) -> str:
    room_text = f"{room.name} {room.zone} {room.heating_type}".lower()
    if "adjacent" in room_text or "natural transfer" in room_text:
        return "Shared/adjacent control TBD"
    if "fireplace" in room_text:
        return "Yes, coordinate with fireplace temperature influence"
    if "frost" in room_text or "technical" in room_text:
        return "Yes, frost protection/alarm control"
    return "Yes, zone thermostat placeholder"


def _floor_loop_placeholder(room: Room) -> str:
    heating = room.heating_type.lower()
    if "underfloor" in heating:
        return "Underfloor loop count/spacing TBD by heat-loss and floor build-up"
    if "radiator" in heating:
        return "No UFH loop assumed; emitter sizing TBD"
    if "fireplace" in heating:
        return "No primary UFH loop shown; comfort backup TBD"
    if "frost" in heating:
        return "Frost-protection emitter/loop TBD"
    return "Heating emitter/loop TBD by mechanical engineer"


def _hvac_zone_notes(room: Room) -> str:
    return (
        f"Heating: {room.heating_type}; ventilation: {room.ventilation_type}. "
        "No final heat loss calculation is included."
    )


def _hvac_zones(config: MountainRetreatConfig) -> tuple[HvacZoneItem, ...]:
    zones: list[HvacZoneItem] = []
    for index, room in enumerate(all_config_rooms(config), start=1):
        zones.append(
            HvacZoneItem(
                zone_code=f"HZ-{index:03d}",
                room=room.name,
                area=f"{room.area_m2:g} m2",
                design_temperature_placeholder=_design_temperature_placeholder(room),
                floor_heating_loop_placeholder=_floor_loop_placeholder(room),
                thermostat_required=_thermostat_requirement(room),
                notes=_hvac_zone_notes(room),
            )
        )
    return tuple(zones)


def _hvac_equipment(config: MountainRetreatConfig) -> tuple[HvacEquipmentItem, ...]:
    return (
        HvacEquipmentItem(
            equipment="Air-to-water heat pump",
            location="Technical room / exterior unit location TBD",
            purpose="Primary low-temperature heating source and possible cooling support",
            power_capacity_placeholder="Capacity TBD by final heat loss/gain calculation",
            electrical_dependency="Dedicated electrical supply and controls TBD",
            maintenance_interval="Seasonal inspection; manufacturer schedule TBD",
            notes=(
                "Outdoor unit placement, defrost drainage, noise, snow clearance, and access TBD."
            ),
        ),
        HvacEquipmentItem(
            equipment="Buffer tank / hydraulic separator",
            location="Technical room",
            purpose="Hydraulic stability for heat pump and distribution circuits",
            power_capacity_placeholder="Volume TBD by mechanical design",
            electrical_dependency="Controls/sensors/circulation pumps TBD",
            maintenance_interval="Annual inspection",
            notes=(
                "Clearance, insulation, valves, strainers, and drain points require layout review."
            ),
        ),
        HvacEquipmentItem(
            equipment="Underfloor heating manifold set",
            location="Ground floor and gallery manifold locations TBD",
            purpose="Room or zone heat distribution",
            power_capacity_placeholder="Loop lengths/spacing TBD by heat-loss calculation",
            electrical_dependency="Thermostats, actuators, and control wiring TBD",
            maintenance_interval="Annual balancing and actuator check",
            notes="Manifold locations must remain accessible and coordinated with finishes.",
        ),
        HvacEquipmentItem(
            equipment="Fireplace / stove system",
            location="Fireplace zone",
            purpose="Secondary heat source and cabin amenity",
            power_capacity_placeholder="Appliance output TBD by chimney/fireplace professional",
            electrical_dependency="Combustion air and fan/control power if applicable",
            maintenance_interval="Seasonal chimney and appliance service",
            notes="Combustion air, clearances, flue, CO alarms, and fire safety review required.",
        ),
        HvacEquipmentItem(
            equipment="Mechanical extract fans",
            location="Bathrooms, laundry/storage, technical room",
            purpose="Moisture and odor extraction",
            power_capacity_placeholder="Airflow TBD by ventilation calculation",
            electrical_dependency="Switched/timer/humidity controls TBD",
            maintenance_interval="Quarterly grille/filter cleaning; annual function check",
            notes="Duct routing, condensation control, backdraft dampers, and noise TBD.",
        ),
        HvacEquipmentItem(
            equipment="Heat recovery ventilation option",
            location="Technical room or service zone TBD",
            purpose="Balanced ventilation with heat recovery",
            power_capacity_placeholder="Airflow and heat recovery capacity TBD",
            electrical_dependency="Dedicated power, controls, sensors, and condensate drain TBD",
            maintenance_interval="Filter check every 3-6 months; annual service",
            notes=(
                "Optional system; duct routes, fire/smoke strategy, frost protection, "
                "and noise TBD."
            ),
        ),
        HvacEquipmentItem(
            equipment="Domestic hot water cylinder",
            location="Technical room",
            purpose="Domestic hot water storage integrated with heat pump concept",
            power_capacity_placeholder="Cylinder volume and coil/backup capacity TBD",
            electrical_dependency="Controls and backup heater power TBD",
            maintenance_interval="Annual safety and legionella-control review",
            notes=(
                "Coordinate with plumbing package, expansion, relief discharge, and service access."
            ),
        ),
    )


def _hvac_context(config: MountainRetreatConfig) -> dict[str, object]:
    zones = _hvac_zones(config)
    equipment = _hvac_equipment(config)
    wet_rooms = tuple(
        room
        for room in all_config_rooms(config)
        if room.plumbing_fixtures
        or "bathroom" in room.name.lower()
        or "laundry" in room.name.lower()
    )
    return {
        "project": config.project,
        "site": config.site,
        "building": config.building,
        "smart_home": config.smart_home,
        "off_grid": config.off_grid,
        "assumptions": _shared_assumptions(config),
        "limitations": _shared_limitations(config),
        "zones": zones,
        "equipment": equipment,
        "wet_rooms": wet_rooms,
        "zone_count": len(zones),
        "equipment_count": len(equipment),
        "total_zone_area_m2": sum(room.area_m2 for room in all_config_rooms(config)),
    }


def _smart_home_device_schedule(config: MountainRetreatConfig) -> tuple[SmartHomeDeviceItem, ...]:
    protocols = config.smart_home.protocols
    zigbee = "Zigbee" if "Zigbee" in protocols else "Low-power mesh TBD"
    matter = "Matter" if "Matter" in protocols else "Matter/thread TBD"
    mqtt = "MQTT" if "MQTT" in protocols else "MQTT/event bus TBD"
    rows = (
        (
            "SH-001",
            "Home Assistant controller",
            config.smart_home.network_assumptions["rack_location"],
            "Ethernet",
            "UPS-backed mains",
            "Local LAN; internet optional for selected integrations",
            "Primary local automation coordinator",
            "Critical",
            "Use backups, monitored storage, and documented restore procedure.",
        ),
        (
            "SH-002",
            "Zigbee coordinator",
            config.smart_home.network_assumptions["rack_location"],
            zigbee,
            "USB/PoE adapter or powered coordinator TBD",
            "Local mesh and Home Assistant",
            "Low-power sensors and switches",
            "Critical",
            "Place away from electrical noise; final channel plan TBD.",
        ),
        (
            "SH-003",
            "Matter controller / thread border router placeholder",
            "Technical room / central living zone TBD",
            matter,
            "UPS-backed mains where practical",
            "Local LAN and vendor ecosystem dependency TBD",
            "Matter device onboarding and resilience",
            "High",
            "Avoid cloud-only dependencies for critical cabin functions.",
        ),
        (
            "SH-004",
            "MQTT broker",
            config.smart_home.network_assumptions["rack_location"],
            mqtt,
            "UPS-backed mains",
            "Local LAN",
            "Telemetry/event bus for energy, sensors, and alerts",
            "High",
            "Use authentication, least privilege, and retained-message review.",
        ),
        (
            "SH-005",
            "PoE camera set",
            "Entry, driveway, terrace, and service approach",
            "Ethernet/PoE",
            "PoE switch on UPS where practical",
            "Camera VLAN and NVR/Home Assistant integration",
            "Perimeter awareness and event recording",
            "High",
            "Privacy, signage, retention, and local surveillance law review required.",
        ),
        (
            "SH-006",
            "Smart lock",
            "Entrance vestibule",
            matter,
            "Battery with keyed/manual override",
            "Local controller plus emergency manual access",
            "Away mode, guest access, lock status alerts",
            "High",
            "Never rely on automation as the only safe means of entry or egress.",
        ),
        (
            "SH-007",
            "Motion sensor group",
            "Entrance, stair zone, living room, gallery, terrace",
            zigbee,
            "Battery",
            "Local mesh",
            "Lighting scenes, occupancy, and security modes",
            "Medium",
            "Locations require nuisance-trigger review around fireplace and windows.",
        ),
        (
            "SH-008",
            "Water leak sensor group",
            "Kitchen, bathrooms, laundry/storage, technical room",
            zigbee,
            "Battery",
            "Local mesh; optional shutoff valve dependency",
            "Leak alerts and optional water shutoff",
            "Critical",
            "Sensor alerts do not replace waterproofing, drains, or maintenance.",
        ),
        (
            "SH-009",
            "Smoke/CO sensor integration placeholder",
            "Bedrooms, living room, fireplace zone, technical room",
            "Certified detector system + integration TBD",
            "Code-required independent power per final design",
            "Life-safety system independent of smart-home platform",
            "Notification mirror only",
            "Critical",
            "Smart-home integration must not replace approved smoke/CO detection.",
        ),
        (
            "SH-010",
            "Outdoor weather station",
            "Exterior mast/location TBD",
            "Wi-Fi/Ethernet/MQTT TBD",
            "Mains/solar/battery TBD",
            "Local LAN or weather gateway",
            "Wind, temperature, freeze, and terrace/weather automations",
            "Medium",
            "Mounting must consider wind, lightning, ice, and service access.",
        ),
        (
            "SH-011",
            "Solar and battery monitoring gateway",
            "Technical room",
            "Ethernet/MQTT/API TBD",
            "UPS-backed mains where supported",
            "Local LAN plus inverter/battery gateway",
            "Production, battery, generator, and outage notifications",
            "High",
            "Electrical system data is informational unless reviewed by professionals.",
        ),
        (
            "SH-012",
            "UPS for network equipment",
            config.smart_home.network_assumptions["rack_location"],
            "Local power monitoring / USB / network card TBD",
            "Battery-backed mains",
            "Controller, router, PoE switch, and modem dependency",
            "Graceful shutdown and outage alerts",
            "Critical",
            "Runtime sizing, battery service, and safe shutdown must be tested.",
        ),
    )
    return tuple(SmartHomeDeviceItem(*row) for row in rows)


def _sensor_schedule(
    devices: tuple[SmartHomeDeviceItem, ...],
) -> tuple[SensorScheduleItem, ...]:
    sensor_devices = tuple(
        device
        for device in devices
        if any(
            marker in device.device_type.lower()
            for marker in ("sensor", "camera", "weather", "monitoring")
        )
    )
    return tuple(
        SensorScheduleItem(
            sensor_code=f"SS-{index:03d}",
            sensor_type=device.device_type,
            room_location=device.room_location,
            protocol=device.protocol,
            alert_route="Home Assistant dashboard, local notification, and alert log",
            priority=device.priority,
            notes=device.notes,
        )
        for index, device in enumerate(sensor_devices, start=1)
    )


def _automation_examples() -> tuple[AutomationItem, ...]:
    rows = (
        (
            "AU-001",
            "Winter freeze protection",
            "Low indoor/technical-room temperature or weather station frost warning",
            "Notify owner, verify heat source status, and raise heating setpoint placeholder",
            "Temperature sensors, weather station, HVAC integration, UPS/network",
            "Must not replace engineered freeze protection or winterization procedure.",
        ),
        (
            "AU-002",
            "Water leak shutoff",
            "Leak sensor alarm in wet room or technical room",
            "Send critical alert and close smart shutoff valve if installed and approved",
            "Leak sensors, optional motorized valve, local controller, power backup",
            "Shutoff valve must be manually accessible and professionally reviewed.",
        ),
        (
            "AU-003",
            "Away mode",
            "Owner activates away profile or no occupancy detected for configured period",
            "Lower heating setpoints, arm security mode, reduce lighting, and monitor leaks",
            "Occupancy sensors, smart lock state, HVAC controls, camera/security system",
            "Do not lock occupants in or disable required life-safety systems.",
        ),
        (
            "AU-004",
            "Night security mode",
            "Scheduled night period or manual scene activation",
            "Arm perimeter alerts, dim path lighting, and keep smoke/CO alerts mirrored",
            "Motion sensors, cameras, lighting controls, smart lock status",
            "Security automation is advisory and does not guarantee protection.",
        ),
        (
            "AU-005",
            "Terrace lighting scene",
            "Manual scene, sunset, or motion event",
            "Activate low-glare terrace lights and shut off after timeout",
            "Terrace lighting, motion sensors, weather condition input",
            "Exterior lighting must remain electrically safe and weather-rated.",
        ),
        (
            "AU-006",
            "Low battery warning",
            "Battery device drops below configured threshold",
            "Create maintenance task and send owner notification",
            "Battery sensors, Home Assistant, notification service",
            "Critical sensors need periodic manual checks even when automation is quiet.",
        ),
        (
            "AU-007",
            "Generator alert",
            "Generator run/fault signal or outage state detected",
            "Notify owner and log event for maintenance follow-up",
            "Generator interface, power monitor, UPS-backed network",
            "Generator controls and transfer equipment require licensed electrical design.",
        ),
        (
            "AU-008",
            "Solar production notification",
            "Solar production, battery state, or inverter fault crosses configured threshold",
            "Notify owner and log trend for review",
            "Solar monitoring gateway, MQTT/API integration, local network",
            "Energy data is informational and not a substitute for electrical commissioning.",
        ),
    )
    return tuple(AutomationItem(*row) for row in rows)


def _smart_home_context(config: MountainRetreatConfig) -> dict[str, object]:
    devices = _smart_home_device_schedule(config)
    sensors = _sensor_schedule(devices)
    automations = _automation_examples()
    return {
        "project": config.project,
        "smart_home": config.smart_home,
        "off_grid": config.off_grid,
        "terrace": config.terrace,
        "assumptions": _shared_assumptions(config),
        "limitations": _shared_limitations(config),
        "devices": devices,
        "sensors": sensors,
        "automations": automations,
        "device_count": len(devices),
        "sensor_count": len(sensors),
        "automation_count": len(automations),
    }


def _load_estimates() -> tuple[LoadEstimateItem, ...]:
    rows = (
        (
            "LD-001",
            "Heating controls and circulation pumps",
            "150 W placeholder",
            "12 h/day placeholder",
            "1.8 kWh/day planning assumption",
            "Yes",
            "1",
            "Keep heat distribution and frost protection available during outages.",
        ),
        (
            "LD-002",
            "Refrigerator/freezer",
            "120 W placeholder average",
            "10 h/day equivalent placeholder",
            "1.2 kWh/day planning assumption",
            "Yes",
            "1",
            "Food safety load; actual use depends on appliance selection and ambient temperature.",
        ),
        (
            "LD-003",
            "Network, router, Home Assistant, and sensors",
            "80 W placeholder",
            "24 h/day placeholder",
            "1.9 kWh/day planning assumption",
            "Yes",
            "1",
            "UPS-backed monitoring and alerts; actual power depends on equipment.",
        ),
        (
            "LD-004",
            "Water pump / pressure system",
            "750 W placeholder",
            "1 h/day placeholder",
            "0.75 kWh/day planning assumption",
            "Yes",
            "2",
            "Pump starting current and pressure-vessel sizing require professional review.",
        ),
        (
            "LD-005",
            "Lighting critical circuits",
            "250 W placeholder",
            "4 h/day placeholder",
            "1.0 kWh/day planning assumption",
            "Yes",
            "2",
            "Critical lighting should be limited to safety/pathway/task zones.",
        ),
        (
            "LD-006",
            "Mechanical ventilation / bathroom extract",
            "120 W placeholder",
            "6 h/day placeholder",
            "0.72 kWh/day planning assumption",
            "Yes",
            "2",
            "Humidity control remains important in winter and during vacancy.",
        ),
        (
            "LD-007",
            "PoE cameras and security devices",
            "100 W placeholder",
            "24 h/day placeholder",
            "2.4 kWh/day planning assumption",
            "Yes",
            "2",
            "Can be reduced in emergency mode if battery state becomes critical.",
        ),
        (
            "LD-008",
            "Domestic hot water backup element",
            "2000 W placeholder",
            "1 h/day placeholder",
            "2.0 kWh/day planning assumption",
            "No",
            "3",
            "High load; may be disabled during islanded or low-battery operation.",
        ),
        (
            "LD-009",
            "Cooking / kitchen appliances",
            "3000 W placeholder",
            "1 h/day placeholder",
            "3.0 kWh/day planning assumption",
            "No",
            "4",
            "Use pattern dominates energy demand; not guaranteed by battery reserve.",
        ),
        (
            "LD-010",
            "Laundry appliances",
            "2500 W placeholder",
            "0.5 h/day placeholder",
            "1.25 kWh/day planning assumption",
            "No",
            "5",
            "Defer during low solar, generator faults, or emergency mode.",
        ),
        (
            "LD-011",
            "Terrace / exterior comfort loads",
            "1000 W placeholder",
            "1 h/day placeholder",
            "1.0 kWh/day planning assumption",
            "No",
            "5",
            "Includes optional exterior amenities; disable during off-grid constraints.",
        ),
        (
            "LD-012",
            "EV charging placeholder",
            "7000 W placeholder",
            "0 h/day default placeholder",
            "0 kWh/day default planning assumption",
            "No",
            "Lowest",
            "Not included in autonomy assumptions unless explicitly engineered.",
        ),
    )
    return tuple(LoadEstimateItem(*row) for row in rows)


def _failure_scenarios() -> tuple[FailureScenarioItem, ...]:
    rows = (
        (
            "Extended snow cover on PV array",
            "Solar production can fall sharply for multiple days.",
            "Clear snow only if safe; switch to critical loads and generator plan.",
            "Solar production notification and low battery warning.",
            "PV layout, snow guards, roof access, and winter maintenance review.",
        ),
        (
            "Battery reaches low state of charge",
            "Non-critical loads must be shed to preserve monitoring and frost protection.",
            "Disable DHW boost, laundry, terrace loads, and other low-priority circuits.",
            "Battery monitoring, load-shed notification, and owner alert.",
            "Electrical engineer to define thresholds, interlocks, and safe load shedding.",
        ),
        (
            "Backup generator fails to start",
            "Autonomy is not guaranteed; cabin may lose critical loads after battery depletion.",
            "Use manual troubleshooting checklist and arrange service.",
            "Generator fault alert and outage event log.",
            "Generator professional to review fuel, starting, transfer, exhaust, and maintenance.",
        ),
        (
            "Inverter/charger fault",
            "Islanded power may be unavailable or unstable.",
            "Move to safe shutdown and manual backup plan.",
            "Inverter fault notification where supported.",
            "Licensed electrical review of bypass, transfer, protection, and commissioning.",
        ),
        (
            "Water tank/pump unavailable",
            "Water service may stop even if electrical power remains available.",
            "Conserve water, check pump protection, and use manual supply plan if available.",
            "Pump power monitoring and leak/pressure alert placeholder.",
            "Plumbing/mechanical review of pump, filtration, drain-down, and access.",
        ),
        (
            "Internet outage",
            "Remote monitoring and notifications may fail.",
            "Rely on local control, local alarms, and manual checks.",
            "Local dashboard remains preferred; cellular backup TBD.",
            "Network integrator to review WAN failover, VPN, and alert routes.",
        ),
    )
    return tuple(FailureScenarioItem(*row) for row in rows)


def _off_grid_context(config: MountainRetreatConfig) -> dict[str, object]:
    loads = _load_estimates()
    failures = _failure_scenarios()
    return {
        "project": config.project,
        "site": config.site,
        "building": config.building,
        "off_grid": config.off_grid,
        "smart_home": config.smart_home,
        "assumptions": (*_shared_assumptions(config), *tuple(config.off_grid.limitations)),
        "limitations": (*_shared_limitations(config), *tuple(config.off_grid.limitations)),
        "loads": loads,
        "failure_scenarios": failures,
        "critical_loads": tuple(load for load in loads if load.critical == "Yes"),
        "non_critical_loads": tuple(load for load in loads if load.critical == "No"),
        "load_count": len(loads),
        "failure_count": len(failures),
    }


MAINTENANCE_SECTIONS = (
    "Maintenance philosophy",
    "Owner responsibilities",
    "Monthly checklist",
    "Seasonal checklist",
    "Annual checklist",
    "5-year maintenance",
    "10-year maintenance",
    "20-year maintenance",
    "30-year renewal planning",
    "Roof maintenance",
    "Timber facade maintenance",
    "Stone facade maintenance",
    "Terrace maintenance",
    "Window and door maintenance",
    "HVAC maintenance",
    "Fireplace maintenance",
    "Solar PV maintenance",
    "Battery maintenance",
    "Generator maintenance",
    "Water system maintenance",
    "Wastewater system maintenance",
    "Smart home maintenance",
    "Emergency plan",
    "Maintenance log template",
)


def _maintenance_task_rows(config: MountainRetreatConfig) -> tuple[tuple[str, ...], ...]:
    return (
        (
            "Monthly checklist",
            "Walk roof edges, terrace drains, technical room, bathrooms, and windows for leaks.",
            "Monthly",
            "Owner/operator",
            "1-2 hours",
            "Flashlight, camera, moisture meter if available",
            "Staining, swelling, musty smell, ponding, active drips",
            "Record photos and call qualified trades if water ingress is suspected.",
        ),
        (
            "Monthly checklist",
            "Review heat pump, smart-home dashboard, leak sensors, and battery alerts.",
            "Monthly",
            "Owner/operator",
            "30 minutes",
            "Home Assistant dashboard, equipment manuals",
            "Offline sensors, repeated alarms, unusual cycling, temperature drift",
            "Alerts are planning aids and do not replace physical inspection.",
        ),
        (
            "Seasonal checklist",
            "Prepare cabin for winter freeze, snow, wind, and access constraints.",
            "Autumn / before first frost",
            "Owner with HVAC/plumbing trades as needed",
            "0.5-1 day",
            "Drain-down checklist, insulation check, snow tools",
            "Unheated pipe routes, blocked drains, low antifreeze/frost protection",
            (
                f"Use frost depth placeholder {config.site.frost_depth_placeholder_cm:g} "
                "cm as a risk reminder only."
            ),
        ),
        (
            "Seasonal checklist",
            (
                "Inspect terrace surface falls, scuppers/drains, guards, exterior "
                "lighting, and furniture."
            ),
            "Spring and autumn",
            "Owner/operator",
            "2-4 hours",
            "Hose test by professional if needed, level, hand tools",
            "Loose guards, ponding, cracked sealant, blocked outlets",
            "Jacuzzi-ready and fire-pit zones remain placeholders until professionally designed.",
        ),
        (
            "Annual checklist",
            "Complete annual owner inspection and update maintenance binder.",
            "Annual",
            "Owner/operator",
            "0.5 day",
            "Maintenance log, camera, manuals, warranty file",
            "Missing records, unresolved defects, repeated alarms",
            "Use the Excel maintenance calendar as the working log.",
        ),
        (
            "Annual checklist",
            (
                "Schedule professional review of roof, envelope, MEP systems, and "
                "safety-critical items."
            ),
            "Annual",
            "Qualified contractor / licensed trades",
            "1 day allowance",
            "Access equipment, inspection reports, as-built notes",
            "Movement, leaks, corrosion, poor combustion, electrical faults",
            "Professional inspections do not create permits unless issued by proper authorities.",
        ),
        (
            "5-year maintenance",
            (
                "Plan first medium-cycle review of coatings, sealants, membranes, "
                "and MEP service history."
            ),
            "Every 5 years",
            "Owner with architect/contractor",
            "1-3 days",
            "Inspection checklist, access equipment, supplier manuals",
            "UV damage, sealant cracking, timber finish breakdown, recurring leaks",
            "Budget for selective renewal rather than waiting for failure.",
        ),
        (
            "10-year maintenance",
            (
                "Review roof accessories, facade finish strategy, window hardware, "
                "HVAC major service needs."
            ),
            "Every 10 years",
            "Owner with specialist contractors",
            "2-5 days",
            "Inspection report, service records, replacement budget",
            "Corrosion, hardware wear, coating failure, lower HVAC efficiency",
            "Use real contractor quotes; this package does not provide live prices.",
        ),
        (
            "20-year maintenance",
            (
                "Plan major system renewal study for roof, facade, terrace, HVAC, "
                "PV, battery, and controls."
            ),
            "Year 20",
            "Owner with design team",
            "1-2 weeks planning",
            "Condition survey, budget model, energy review",
            "End-of-life equipment, repeated water ingress, obsolete controls",
            "Treat as a redesign checkpoint with licensed professional review.",
        ),
        (
            "30-year renewal planning",
            (
                "Prepare 30-year renewal plan for envelope, structure interfaces, "
                "MEP systems, and interiors."
            ),
            "Year 30",
            "Owner with architect, engineers, and cost estimator",
            "2-4 weeks planning",
            "Condition survey, measured drawings, contractor quotes",
            "System obsolescence, hidden moisture, structural movement, code changes",
            "Do not assume original planning documents remain valid after 30 years.",
        ),
        (
            "Roof maintenance",
            (
                f"Inspect {config.building.roof_type}, valleys, gutters, snow guards, "
                "flashings, and penetrations."
            ),
            "Seasonal and after severe storms",
            "Owner for visual checks; roofer for access work",
            "2-4 hours",
            "Binoculars, camera, safe access equipment by qualified personnel",
            "Loose panels, corrosion, ice dams, blocked gutters, damaged flashing",
            "No roof access without fall protection and competent supervision.",
        ),
        (
            "Timber facade maintenance",
            (
                "Inspect timber cladding finish, ventilation gaps, end grain, "
                "fasteners, and splash zones."
            ),
            "Annual; refinish cycle TBD",
            "Owner / facade contractor",
            "0.5-1 day",
            "Moisture meter, camera, cleaning tools",
            "Greying beyond design intent, cupping, rot, loose boards, trapped debris",
            "Final coating cycles depend on selected product and exposure.",
        ),
        (
            "Stone facade maintenance",
            "Inspect stone veneer/supports, joints, weeps, movement joints, and staining.",
            "Annual",
            "Masonry/facade contractor",
            "0.5 day",
            "Camera, joint probe by specialist, cleaning tools",
            "Cracked joints, displaced stone, efflorescence, blocked weeps",
            "Avoid aggressive cleaning without facade specialist review.",
        ),
        (
            "Terrace maintenance",
            (
                "Inspect deck boards/pavers, waterproofing terminations, drains, "
                "guards, stairs, and lighting."
            ),
            "Monthly in use season; seasonal deep check",
            "Owner / terrace contractor",
            "2-6 hours",
            "Hand tools, level, drain cleaning tools",
            "Ponding, loose guards, slippery surfaces, blocked drains, movement",
            f"Terrace area assumption is {config.terrace.terrace_area_m2:g} m2.",
        ),
        (
            "Window and door maintenance",
            (
                "Clean and inspect glazing, seals, drainage slots, thresholds, hinges, "
                "locks, and weatherstrips."
            ),
            "Seasonal",
            "Owner / window contractor",
            "2-4 hours",
            "Non-abrasive cleaner, silicone-free hardware lubricant, camera",
            "Condensation between panes, air leakage, stiff operation, water at thresholds",
            (
                "Large panoramic glazing requires specialist inspection if movement "
                "or cracking appears."
            ),
        ),
        (
            "HVAC maintenance",
            (
                "Service heat pump, underfloor manifolds, filters, pumps, valves, "
                "and frost-protection settings."
            ),
            "Annual; filters 3-6 months",
            "Licensed mechanical/HVAC contractor",
            "0.5-1 day",
            "Manufacturer service kit, pressure/temperature readings",
            "Short cycling, low pressure, cold rooms, unusual noise, fault codes",
            "No final heat-loss calculation is included in this repository.",
        ),
        (
            "Fireplace maintenance",
            (
                "Inspect fireplace/stove, flue, combustion air, hearth, clearances, "
                "ash handling, and CO alarms."
            ),
            "Before heating season",
            "Certified chimney/fireplace professional",
            "2-4 hours",
            "Chimney brushes/tools by professional, CO alarm tester",
            "Soot smell, poor draft, cracked glass, smoke spillage, CO alarm events",
            "Never operate fireplace after a suspected flue or CO issue until inspected.",
        ),
        (
            "Solar PV maintenance",
            (
                "Inspect PV production, roof interfaces, isolators, labels, snow "
                "shading, and monitoring."
            ),
            "Quarterly visual; annual professional check",
            "Owner / licensed solar electrician",
            "1-3 hours",
            "Monitoring dashboard, camera, electrician test equipment",
            "Production drop, damaged cables, inverter faults, water at penetrations",
            f"PV assumption is {config.off_grid.pv_kwp:g} kWp and remains preliminary.",
        ),
        (
            "Battery maintenance",
            (
                "Review battery room/area, BMS alarms, ventilation, temperature, "
                "clearances, and shutdown labels."
            ),
            "Monthly dashboard; annual professional check",
            "Owner / licensed electrical professional",
            "1-2 hours",
            "BMS dashboard, thermal scan by professional if needed",
            "Swelling, heat, odor, repeated faults, communication loss",
            (
                f"Battery assumption is {config.off_grid.battery_kwh:g} kWh and "
                "requires specialist review."
            ),
        ),
        (
            "Generator maintenance",
            (
                "Test generator start, fuel condition, exhaust route, transfer "
                "arrangement, and service interval."
            ),
            "Monthly exercise; annual service",
            "Owner / generator specialist / electrician",
            "1-3 hours",
            "Generator manual, fuel stabilizer if applicable, load test equipment by professional",
            "Hard starting, exhaust smell, fuel leaks, transfer faults, low runtime",
            f"Generator assumption: {config.off_grid.generator}. Transfer design is not finalized.",
        ),
        (
            "Water system maintenance",
            (
                "Inspect tank, pump, filters, pressure, insulation, valves, leak "
                "sensors, and drain-down points."
            ),
            "Monthly; seasonal winterization",
            "Owner / licensed plumber",
            "1-4 hours",
            "Pressure gauge, filter cartridges, leak sensor test",
            "Pressure loss, cloudy water, pump cycling, leaks, frozen sections",
            f"Water tank option assumption: {config.off_grid.water_tank_l:g} L.",
        ),
        (
            "Wastewater system maintenance",
            (
                "Review septic/biological treatment option, access covers, alarms, "
                "odors, and service contract."
            ),
            "Per authority/manufacturer; visual monthly",
            "Licensed wastewater service provider",
            "1-3 hours",
            "Service log, access tools by provider, alarm test",
            "Odor, backups, wet ground, alarm events, blocked venting",
            "Local wastewater approval and maintenance rules must govern final operation.",
        ),
        (
            "Smart home maintenance",
            (
                "Back up Home Assistant, test Zigbee/Matter/MQTT devices, cameras, "
                "UPS, alerts, and credentials."
            ),
            "Monthly backup; annual security review",
            "Owner / smart-home integrator",
            "1-3 hours",
            "Admin dashboard, password manager, UPS test, spare batteries",
            "Offline devices, failed backups, stale updates, weak passwords, missing alerts",
            f"Configured platform assumption: {config.smart_home.platform}.",
        ),
        (
            "Emergency plan",
            (
                "Review emergency contacts, shutoff locations, generator procedure, "
                "freeze response, and evacuation."
            ),
            "Annual and after major changes",
            "Owner/operator",
            "1-2 hours",
            "Printed emergency sheet, labels, flashlight, first-aid kit",
            "Unlabeled shutoffs, inaccessible equipment, expired fire extinguishers",
            "Keep paper instructions available because internet or power may fail.",
        ),
        (
            "Maintenance log template",
            (
                "Update maintenance log with date, task, observations, photos, "
                "responsible person, and next action."
            ),
            "Every maintenance event",
            "Owner/operator",
            "10-20 minutes per entry",
            "Excel calendar, photo folder, document register",
            "Missing photos, unresolved defects, no assigned follow-up",
            "The log supports planning and does not replace formal inspection certificates.",
        ),
    )


def _maintenance_tasks(config: MountainRetreatConfig) -> tuple[MaintenanceTask, ...]:
    return tuple(MaintenanceTask(*row) for row in _maintenance_task_rows(config))


def _maintenance_context(config: MountainRetreatConfig) -> dict[str, object]:
    tasks = _maintenance_tasks(config)
    return {
        "project": config.project,
        "site": config.site,
        "building": config.building,
        "terrace": config.terrace,
        "smart_home": config.smart_home,
        "off_grid": config.off_grid,
        "assumptions": _shared_assumptions(config),
        "limitations": _shared_limitations(config),
        "sections": MAINTENANCE_SECTIONS,
        "tasks": tasks,
        "task_count": len(tasks),
    }


def _construction_management_sections(
    config: MountainRetreatConfig,
    *,
    large_mode: bool,
) -> tuple[MarkdownSection, ...]:
    base_sections = (
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
    )
    if not large_mode:
        return base_sections

    phase_lines = tuple(
        (
            f"{phase.wbs} {phase.name}: risk owner {phase.responsible_party}; "
            f"duration {phase.duration_days} days; inspection required: "
            f"{phase.inspection_required}; safety note: {phase.safety_notes}"
        )
        for phase in config.construction_phases.phases
    )
    procurement_lines = tuple(
        (
            f"{item.code}: procure {item.name} ({item.specification}) as "
            f"{item.base_quantity:g} {item.unit} plus {item.waste_percent:g}% waste; "
            f"assumption ref {item.assumption_ref}; supplier remains placeholder."
        )
        for item in [*config.materials_core.materials, *config.materials_mep.materials]
    )
    inspection_lines = tuple(
        (
            f"{item.id}: {item.phase} / {item.discipline} - {item.inspection_item}; "
            f"criteria: {item.acceptance_criteria}; responsible: {item.responsible_party}."
        )
        for item in config.checklists_seed.checklist_items
    )
    document_lines = (
        "Register every drawing issue with date, version, author, reviewer, and superseded status.",
        (
            "Register every submittal with supplier placeholder, real supplier quote, "
            "reviewer, and decision."
        ),
        (
            "Register every inspection with required photo, required document, "
            "reviewer, and closeout note."
        ),
        (
            "Register every change with cost, schedule, safety, permitting, and "
            "professional-review impact."
        ),
        "Register every assumption update back into YAML before regenerating planning documents.",
    )
    return (
        *base_sections,
        MarkdownSection("Large-Mode Risk Register", phase_lines),
        MarkdownSection("Large-Mode Procurement Log", procurement_lines),
        MarkdownSection("Large-Mode Inspection Log", inspection_lines),
        MarkdownSection("Large-Mode Document Register", document_lines),
    )


SELF_BUILD_PHASES = (
    "Project preparation",
    "Professional review checklist",
    "Permits and legal preparation",
    "Budgeting and procurement",
    "Site setup",
    "Temporary power and water",
    "Safety setup",
    "Access road and logistics",
    "Excavation",
    "Drainage",
    "Foundation preparation",
    "Rebar preparation",
    "Concrete pour planning",
    "Waterproofing",
    "Timber/structure procurement",
    "Structural assembly",
    "Roof installation",
    "Exterior closure",
    "Windows and doors",
    "Facade",
    "Electrical rough-in",
    "Plumbing rough-in",
    "HVAC rough-in",
    "Insulation and membranes",
    "Interior walls",
    "Flooring",
    "Bathrooms",
    "Kitchen",
    "Terrace construction",
    "Smart home installation",
    "Solar/off-grid installation",
    "Commissioning",
    "Final inspection",
    "Handover binder",
    "Maintenance start",
)

SELF_BUILD_NORMAL_TASKS = (
    "scope and information check",
    "work area and resource readiness",
    "quality hold point",
)

SELF_BUILD_LARGE_TASKS = (
    *SELF_BUILD_NORMAL_TASKS,
    "material delivery and storage",
    "layout and coordination",
    "trade interface review",
    "weather and access contingency",
    "photo record and document control",
    "closeout and next-phase release",
)


def _phase_detail_profile(phase_title: str, config: MountainRetreatConfig) -> dict[str, object]:
    text = phase_title.lower()
    common_materials = (
        "current YAML assumptions and generated preliminary drawings",
        "approved-by-professional documents only where the law requires them",
        "site notebook, photo log, and inspection register",
    )
    common_tools = (
        "tape measure / laser measure",
        "camera or phone for photo records",
        "checklist clipboard or site tablet",
    )
    common_trades = (
        "owner/self-builder",
        "qualified site supervisor",
        "licensed professional reviewer where required",
    )
    profile: dict[str, object] = {
        "materials": common_materials,
        "tools": common_tools,
        "trades": common_trades,
        "duration": "0.5-1 day planning allowance",
        "risks": (
            "acting on preliminary information as if it were approved construction data",
            "missing inspection hold points or local authority requirements",
        ),
        "mistakes": (
            "starting work before professional review is recorded",
            "not updating assumptions when site conditions change",
        ),
        "checks": (
            "confirm the step is consistent with the latest YAML assumptions",
            "confirm required inspections are listed before work proceeds",
        ),
        "documents": (
            "dated checklist entry",
            "photos of existing condition and completed work area",
            "review notes or inspection record where applicable",
        ),
    }

    if any(word in text for word in ("permit", "legal", "professional review")):
        profile.update(
            materials=(
                "planning package marked PRELIMINARY",
                "professional review comments",
                "local authority forms and submission checklist",
            ),
            tools=("document register", "revision tracker", "meeting minutes template"),
            trades=("owner", "architect", "licensed engineers", "local authority"),
            duration="1-5 days depending on authority and reviewer availability",
            risks=(
                "mistaking generated documents for permits or legal approvals",
                "omitting required architect, engineer, utility, or authority review",
            ),
            mistakes=(
                "submitting unreviewed placeholder values",
                "not tracking reviewer comments through closure",
            ),
        )
    elif any(word in text for word in ("budget", "procurement")):
        profile.update(
            materials=(
                "BOM workbook and cost estimate workbook",
                "supplier placeholders replaced by real quotations",
                "procurement log with lead times and substitutions",
            ),
            tools=("spreadsheet tracker", "quote comparison sheet", "delivery calendar"),
            trades=("owner", "cost estimator", "contractor", "suppliers"),
            duration="1-3 days per procurement package",
            risks=(
                "ordering from preliminary quantities",
                "accepting substitutions without design review",
            ),
            mistakes=("ignoring waste factors", "not reserving contingency for mountain logistics"),
        )
    elif any(word in text for word in ("site", "safety", "access", "logistics", "temporary")):
        profile.update(
            materials=(
                "temporary fencing and signage",
                "welfare, storage, first-aid, and fire-extinguisher provisions",
                "temporary power/water equipment approved by qualified trades",
            ),
            tools=("traffic plan", "PPE register", "weather log", "delivery route map"),
            trades=(
                "site supervisor",
                "safety coordinator",
                "licensed electrician/plumber as needed",
            ),
            duration="0.5-2 days before physical works",
            risks=("unstable access road", "temporary services installed without licensed review"),
            mistakes=(
                "placing storage in drainage paths",
                "not planning snow, mud, or crane access",
            ),
        )
    elif any(
        word in text for word in ("excavation", "drainage", "foundation", "rebar", "concrete")
    ):
        profile.update(
            materials=(
                "survey set-out stakes and batter boards",
                (
                    "gravel/tampon assumption depth "
                    f"{config.calculator_assumptions.gravel_depth_m:g} m"
                ),
                "reinforcement, formwork, membranes, and concrete placeholders from BOM",
            ),
            tools=("level/laser", "compaction equipment", "excavator access", "concrete tools"),
            trades=(
                "groundworks contractor",
                "licensed structural engineer",
                "surveyor",
                "concrete crew",
            ),
            duration="1-3 days per hold point, weather dependent",
            risks=("slope instability", "frost and drainage failure", "uninspected reinforcement"),
            mistakes=(
                "covering rebar before inspection",
                "pouring concrete without weather and access plan",
            ),
            checks=(
                "confirm levels, dimensions, compaction, drainage falls, and frost protection",
                "record structural engineer inspection before concrete is placed",
            ),
        )
    elif any(word in text for word in ("waterproof", "roof", "exterior", "windows", "facade")):
        profile.update(
            materials=(
                config.building.roof_type,
                config.building.facade_type,
                "flashing, tapes, membranes, sealants, and drainage accessories",
            ),
            tools=("moisture meter", "scaffold/edge protection", "sealant/tape tools"),
            trades=("architect", "envelope specialist", "roofer", "window/facade installer"),
            duration="0.5-2 days per elevation or zone",
            risks=("water ingress", "fall hazards", "incorrect flashing sequence"),
            mistakes=(
                "burying membranes without photo record",
                "installing windows before opening review",
            ),
        )
    elif any(word in text for word in ("timber", "structure", "structural assembly")):
        profile.update(
            materials=(
                f"structural variant: {config.building.construction_variant}",
                "engineered timber/CLT/masonry package as professionally designed",
                "connectors, hold-downs, bracing, and lifting accessories",
            ),
            tools=("lifting plan", "torque tools", "temporary bracing", "fall protection"),
            trades=("licensed structural engineer", "qualified erector", "crane/lifting crew"),
            duration="1-5 days depending on package and weather",
            risks=("unstable partially erected structure", "incorrect connection installation"),
            mistakes=(
                "removing temporary bracing early",
                "substituting connectors without engineer approval",
            ),
        )
    elif any(word in text for word in ("electrical", "smart home", "solar", "off-grid")):
        profile.update(
            materials=(
                "electrical package with placeholders clearly marked",
                f"smart-home platform assumption: {config.smart_home.platform}",
                (
                    f"off-grid option: {config.off_grid.pv_kwp:g} kWp PV / "
                    f"{config.off_grid.battery_kwh:g} kWh battery"
                ),
            ),
            tools=("cable schedule", "label printer", "continuity tester for qualified trade use"),
            trades=("licensed electrician", "electrical engineer", "network/smart-home integrator"),
            duration="0.5-3 days per circuit or system zone",
            risks=(
                "shock/fire risk",
                "unapproved cable/breaker sizing",
                "unsafe generator/PV transfer",
            ),
            mistakes=(
                "covering cables before inspection",
                "mixing low-voltage and mains routes incorrectly",
            ),
        )
    elif any(word in text for word in ("plumbing", "bathroom", "kitchen")):
        profile.update(
            materials=(
                "fixture schedule from plumbing package",
                "isolation valves, traps, vents, waterproofing accessories",
                "leak sensors and access panels where configured",
            ),
            tools=("pressure test kit", "pipe labeling", "waterproofing checklist"),
            trades=("licensed plumber/mechanical contractor", "waterproofing installer", "tiler"),
            duration="0.5-3 days per wet room or fixture group",
            risks=(
                "leaks hidden behind finishes",
                "frost damage",
                "unapproved wastewater connection",
            ),
            mistakes=("closing walls before pressure test", "omitting access to valves and traps"),
        )
    elif any(word in text for word in ("hvac", "insulation", "membranes")):
        profile.update(
            materials=(
                "heat pump and underfloor-heating assumptions",
                "insulation, vapor barrier, tapes, sleeves, and pipe insulation",
                "ventilation/extract components as professionally designed",
            ),
            tools=("thermal camera if available", "air-sealing tools", "manifold labels"),
            trades=("licensed mechanical engineer", "HVAC installer", "energy/envelope reviewer"),
            duration="0.5-3 days per zone",
            risks=("condensation", "poor winterization", "unverified heat-loss assumptions"),
            mistakes=(
                "compressing insulation",
                "puncturing vapor barriers without sealed penetrations",
            ),
        )
    elif any(word in text for word in ("interior", "flooring")):
        profile.update(
            materials=(
                "room finish schedule",
                "substrate primers, boards, fasteners, adhesives, and trim",
                "manufacturer installation instructions",
            ),
            tools=("straightedge", "moisture meter", "dust control equipment"),
            trades=("finish carpenter", "drywall installer", "flooring installer"),
            duration="0.5-2 days per room group",
            risks=("trapping moisture", "covering unresolved MEP defects"),
            mistakes=("starting finishes before commissioning tests", "ignoring expansion gaps"),
        )
    elif "terrace" in text:
        zone_names = ", ".join(zone.name for zone in config.terrace.zones)
        profile.update(
            materials=(
                f"terrace zones: {zone_names}",
                "decking, guards, drainage, waterproofing, and exterior-rated fixings",
                "jacuzzi/fire-pit placeholders only after structural and fire review",
            ),
            tools=("fall protection", "slope level", "exterior fastening tools"),
            trades=(
                "structural engineer",
                "waterproofing specialist",
                "qualified terrace installer",
            ),
            duration="1-4 days depending on zone and weather",
            risks=("fall from edge", "ponding water", "overloading jacuzzi-ready area"),
            mistakes=(
                "not confirming guard requirements",
                "blocking drainage with decking or furniture",
            ),
        )
    elif any(word in text for word in ("commissioning", "inspection", "handover", "maintenance")):
        profile.update(
            materials=(
                "commissioning forms and test certificates",
                "manufacturer manuals and warranties",
                "handover binder with as-built notes and maintenance schedule",
            ),
            tools=("document register", "defect list", "label printer", "maintenance calendar"),
            trades=(
                "owner",
                "site supervisor",
                "licensed trades",
                "local authority where required",
            ),
            duration="1-5 days depending on defects and inspection availability",
            risks=("occupying before required approvals", "missing safety or warranty documents"),
            mistakes=(
                "not collecting test certificates",
                "not documenting shutoff locations and backups",
            ),
        )
    return profile


def _self_build_step_name(phase_title: str, task_label: str) -> str:
    return f"{phase_title} - {task_label}"


def _self_build_stop_point(phase_title: str, task_label: str) -> str:
    return (
        f"Stop after {phase_title.lower()} {task_label}; obtain the required licensed "
        "trade, engineer, architect, site supervisor, or authority review before "
        "covering work, ordering final materials, energizing systems, or moving to "
        "the next dependent phase."
    )


def _profile_tuple(profile: dict[str, object], key: str) -> tuple[str, ...]:
    return cast(tuple[str, ...], profile[key])


def _self_build_steps(config: MountainRetreatConfig, large_mode: bool) -> tuple[SelfBuildStep, ...]:
    task_labels = SELF_BUILD_LARGE_TASKS if large_mode else SELF_BUILD_NORMAL_TASKS
    steps: list[SelfBuildStep] = []
    step_number = 1
    for phase_number, phase_title in enumerate(SELF_BUILD_PHASES, start=1):
        profile = _phase_detail_profile(phase_title, config)
        for task_label in task_labels:
            materials = _profile_tuple(profile, "materials")
            tools = _profile_tuple(profile, "tools")
            trades = _profile_tuple(profile, "trades")
            risks = _profile_tuple(profile, "risks")
            mistakes = _profile_tuple(profile, "mistakes")
            checks = _profile_tuple(profile, "checks")
            documents = _profile_tuple(profile, "documents")
            steps.append(
                SelfBuildStep(
                    number=step_number,
                    phase_number=phase_number,
                    phase_title=phase_title,
                    name=_self_build_step_name(phase_title, task_label),
                    objective=(
                        f"Plan and control the {task_label} for {phase_title.lower()} "
                        "without treating preliminary documents as approved construction "
                        "instructions."
                    ),
                    prerequisites=(
                        f"Latest {config.project.project_code} YAML assumptions reviewed.",
                        "Relevant preliminary drawings/checklists available on site.",
                        (
                            "Required licensed reviewer or qualified trade identified "
                            "before work starts."
                        ),
                    ),
                    materials=materials,
                    tools=tools,
                    people_trades_required=trades,
                    approximate_duration=str(profile["duration"]),
                    procedure=(
                        f"Review the {phase_title.lower()} scope against current drawings, "
                        "BOM, schedule, and inspection requirements.",
                        (
                            "Confirm dimensions, quantities, product selections, weather window, "
                            "and access constraints before physical work or procurement."
                        ),
                        (
                            "Execute only owner-appropriate tasks; reserve regulated, structural, "
                            "electrical, mechanical, fire, and wastewater work for "
                            "qualified trades."
                        ),
                        (
                            "Record deviations immediately and route them back to the "
                            "design/review team."
                        ),
                    ),
                    quality_checks=checks,
                    safety_risks=risks,
                    common_mistakes=mistakes,
                    professional_stop_point=_self_build_stop_point(phase_title, task_label),
                    photos_documents=documents,
                )
            )
            step_number += 1
    return tuple(steps)


def _self_build_context(
    config: MountainRetreatConfig,
    large_mode: bool,
) -> dict[str, object]:
    steps = _self_build_steps(config, large_mode)
    return {
        "project": config.project,
        "site": config.site,
        "building": config.building,
        "terrace": config.terrace,
        "smart_home": config.smart_home,
        "off_grid": config.off_grid,
        "assumptions": _shared_assumptions(config),
        "limitations": _shared_limitations(config),
        "phases": SELF_BUILD_PHASES,
        "steps": steps,
        "step_count": len(steps),
        "large_mode": large_mode,
    }


def all_config_rooms(config: MountainRetreatConfig) -> list[Room]:
    """Return all configured room models."""
    return [*config.rooms_ground_floor.rooms, *config.rooms_gallery.rooms]


def _localized_config(
    config: MountainRetreatConfig,
    language: str | None,
) -> MountainRetreatConfig:
    translator = load_translator(language or config.project.language)
    review_notes = translator.list_text("professional_review_notes")
    project = config.project.model_copy(
        update={
            "language": translator.language,
            "disclaimer": translator.text("disclaimer_text", config.project.disclaimer),
            "review_required_by": review_notes or config.project.review_required_by,
        }
    )
    return replace(config, project=project)


def _volume_specs(
    config: MountainRetreatConfig,
    *,
    large_mode: bool = False,
) -> tuple[MarkdownVolume, ...]:
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
            sections=_construction_management_sections(config, large_mode=large_mode),
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
    *,
    large_mode: bool = False,
    language: str | None = None,
) -> list[Path]:
    """Generate all Markdown source volumes and return their paths."""
    config = _localized_config(config, language)
    markdown_dir = output_dir / MARKDOWN_OUTPUT_DIR
    markdown_dir.mkdir(parents=True, exist_ok=True)

    env = _environment(template_dir)
    template = env.get_template(TEMPLATE_NAME)
    architectural_template = env.get_template(ARCHITECTURAL_TEMPLATE_NAME)
    structural_template = env.get_template(STRUCTURAL_TEMPLATE_NAME)
    electrical_template = env.get_template(ELECTRICAL_TEMPLATE_NAME)
    plumbing_template = env.get_template(PLUMBING_TEMPLATE_NAME)
    hvac_template = env.get_template(HVAC_TEMPLATE_NAME)
    smart_home_template = env.get_template(SMART_HOME_TEMPLATE_NAME)
    off_grid_template = env.get_template(OFF_GRID_TEMPLATE_NAME)
    maintenance_template = env.get_template(MAINTENANCE_TEMPLATE_NAME)
    self_build_template = env.get_template(SELF_BUILD_TEMPLATE_NAME)
    paths: list[Path] = []
    for volume in _volume_specs(config, large_mode=large_mode):
        if volume.filename == "02_architectural_package.md":
            rendered = architectural_template.render(
                **_architectural_context(config, large_mode=large_mode)
            )
        elif volume.filename == "03_structural_concept.md":
            rendered = structural_template.render(**_structural_context(config))
        elif volume.filename == "04_electrical_package.md":
            rendered = electrical_template.render(**_electrical_context(config))
        elif volume.filename == "05_plumbing_wastewater.md":
            rendered = plumbing_template.render(**_plumbing_context(config))
        elif volume.filename == "06_hvac_package.md":
            rendered = hvac_template.render(**_hvac_context(config))
        elif volume.filename == "07_smart_home_security.md":
            rendered = smart_home_template.render(**_smart_home_context(config))
        elif volume.filename == "08_off_grid_package.md":
            rendered = off_grid_template.render(**_off_grid_context(config))
        elif volume.filename == "12_maintenance_manual.md":
            rendered = maintenance_template.render(**_maintenance_context(config))
        elif volume.filename == "13_self_build_guide.md":
            rendered = self_build_template.render(
                **_self_build_context(config, large_mode),
            )
        else:
            rendered = template.render(project=config.project, volume=volume)
        path = markdown_dir / volume.filename
        path.write_text(rendered, encoding="utf-8")
        paths.append(path)

    return paths
