"""Pure Python SVG schematic drawing generation."""

from collections.abc import Callable
from dataclasses import dataclass
from html import escape
from pathlib import Path

from mountain_retreat_x1.config.loader import MountainRetreatConfig
from mountain_retreat_x1.models import Room

DRAWINGS_OUTPUT_DIR = "drawings"

DRAWING_FILES = (
    "A001_site_plan.svg",
    "A101_ground_floor_plan.svg",
    "A102_gallery_plan.svg",
    "A103_terrace_plan.svg",
    "A201_front_elevation.svg",
    "A202_side_elevation.svg",
    "A301_longitudinal_section.svg",
    "A302_cross_section.svg",
    "S101_foundation_concept.svg",
    "E101_electrical_zones.svg",
    "P101_plumbing_zones.svg",
    "H101_heating_zones.svg",
    "SM101_smart_home_zones.svg",
    "OG101_off_grid_system_diagram.svg",
)


@dataclass(frozen=True)
class Rect:
    """Simple drawing rectangle."""

    x: float
    y: float
    width: float
    height: float


def _svg(width: int, height: int, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        "<defs>\n"
        '<marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" '
        'orient="auto" markerUnits="strokeWidth">'
        '<path d="M0,0 L0,6 L9,3 z" fill="#333" />'
        "</marker>\n"
        "</defs>\n"
        '<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>\n'
        f"{body}\n"
        "</svg>\n"
    )


def _text(x: float, y: float, value: str, size: int = 12, weight: str = "400") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="#111">{escape(value)}</text>'
    )


def _line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: str = "#333",
    width: float = 1.5,
    dash: str = "",
) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{color}" stroke-width="{width}"{dash_attr}/>'
    )


def _rect(
    rect: Rect,
    fill: str = "#f8f8f8",
    stroke: str = "#111",
    stroke_width: float = 1.5,
    dash: str = "",
) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<rect x="{rect.x:.1f}" y="{rect.y:.1f}" width="{rect.width:.1f}" '
        f'height="{rect.height:.1f}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{stroke_width}"{dash_attr}/>'
    )


def _title_block(
    config: MountainRetreatConfig,
    code: str,
    title: str,
    width: int,
    height: int,
) -> str:
    block = Rect(width - 290, height - 90, 270, 70)
    return "\n".join(
        (
            _rect(block, "#f5f7fa", "#111", 1.2),
            _text(block.x + 10, block.y + 18, config.project.project_name, 12, "700"),
            _text(block.x + 10, block.y + 36, f"{code} - {title}", 11, "700"),
            _text(block.x + 10, block.y + 52, "Scale: schematic / not for construction", 10),
            _text(block.x + 10, block.y + 66, f"Status: {config.project.status}", 10),
        )
    )


def _north_arrow(x: float, y: float) -> str:
    return "\n".join(
        (
            _line(x, y + 45, x, y + 5, "#111", 2.0, ""),
            f'<polygon points="{x:.1f},{y:.1f} {x - 6:.1f},{y + 14:.1f} '
            f'{x + 6:.1f},{y + 14:.1f}" fill="#111"/>',
            _text(x - 5, y + 62, "N", 12, "700"),
        )
    )


def _dimension(x1: float, y1: float, x2: float, y2: float, label: str) -> str:
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    return "\n".join(
        (
            _line(x1, y1, x2, y2, "#555", 1.0, "4 3"),
            _text(mid_x + 4, mid_y - 4, label, 10),
        )
    )


def _room_rects(
    rooms: list[Room],
    origin_x: float,
    origin_y: float,
    scale: float,
) -> list[tuple[Room, Rect]]:
    rects: list[tuple[Room, Rect]] = []
    current_x = origin_x
    current_y = origin_y
    row_height = 0.0
    max_width = 620.0
    gap = 12.0
    for room in rooms:
        width = max(room.width_m * scale, 55.0)
        height = max(room.length_m * scale, 42.0)
        if current_x + width > origin_x + max_width:
            current_x = origin_x
            current_y += row_height + gap
            row_height = 0.0
        rect = Rect(current_x, current_y, width, height)
        rects.append((room, rect))
        current_x += width + gap
        row_height = max(row_height, height)
    return rects


def _draw_room(room: Room, rect: Rect) -> str:
    window_y = rect.y + 6
    door_x = rect.x + rect.width - 20
    return "\n".join(
        (
            _rect(rect, "#fafafa", "#202020", 1.7),
            _text(rect.x + 6, rect.y + 17, room.name, 10, "700"),
            _text(rect.x + 6, rect.y + 32, f"{room.area_m2:g} m2", 9),
            _text(
                rect.x + 6,
                rect.y + rect.height - 8,
                f"{room.length_m:g} x {room.width_m:g} m",
                9,
            ),
            _line(
                rect.x + 8,
                window_y,
                rect.x + min(rect.width - 8, 54),
                window_y,
                "#2f80ed",
                3.0,
            ),
            f'<path d="M {door_x:.1f} {rect.y + rect.height:.1f} '
            f'A 20 20 0 0 0 {door_x + 20:.1f} {rect.y + rect.height - 20:.1f}" '
            'fill="none" stroke="#666" stroke-width="1.2"/>',
        )
    )


def _floor_plan(
    config: MountainRetreatConfig,
    code: str,
    title: str,
    rooms: list[Room],
    include_terrace: bool = False,
) -> str:
    width = 900
    height = 700
    scale = 26
    footprint = Rect(
        70,
        95,
        config.building.footprint_length_m * scale,
        config.building.footprint_width_m * scale,
    )
    parts = [
        _text(40, 40, title, 22, "700"),
        _text(40, 62, "Schematic planning drawing - not for construction", 12),
        _north_arrow(820, 55),
        _rect(footprint, "#fff", "#000", 2.4),
        _dimension(
            footprint.x,
            footprint.y - 18,
            footprint.x + footprint.width,
            footprint.y - 18,
            f"{config.building.footprint_length_m:g} m",
        ),
        _dimension(
            footprint.x - 18,
            footprint.y,
            footprint.x - 18,
            footprint.y + footprint.height,
            f"{config.building.footprint_width_m:g} m",
        ),
    ]
    for room, rect in _room_rects(rooms, 90, 115, scale):
        parts.append(_draw_room(room, rect))
    if include_terrace:
        terrace = Rect(footprint.x, footprint.y + footprint.height + 22, footprint.width, 120)
        parts.extend(
            (
                _rect(terrace, "#e8f4df", "#6a8f3a", 1.8, "8 4"),
                _text(
                    terrace.x + 10,
                    terrace.y + 22,
                    "Panoramic terrace / external deck zone",
                    12,
                    "700",
                ),
                _text(
                    terrace.x + 10,
                    terrace.y + 42,
                    f"{config.terrace.terrace_area_m2:g} m2 schematic",
                    10,
                ),
            )
        )
    parts.append(_title_block(config, code, title, width, height))
    return _svg(width, height, "\n".join(parts))


def _terrace_plan(config: MountainRetreatConfig) -> str:
    width = 900
    height = 520
    parts = [
        _text(40, 40, "Terrace Plan", 22, "700"),
        _text(40, 62, "Schematic terrace zoning - not for construction", 12),
        _north_arrow(820, 55),
    ]
    x = 70.0
    y = 125.0
    for zone in config.terrace.zones:
        zone_width = max(zone.area_m2 * 5.5, 70)
        rect = Rect(x, y, zone_width, 110)
        parts.extend(
            (
                _rect(rect, "#e8f4df", "#6a8f3a", 1.6),
                _text(rect.x + 8, rect.y + 22, zone.name, 10, "700"),
                _text(rect.x + 8, rect.y + 40, f"{zone.area_m2:g} m2", 9),
                _text(rect.x + 8, rect.y + 58, zone.function, 8),
            )
        )
        x += zone_width + 12
        if x > 760:
            x = 70
            y += 135
    parts.append(_title_block(config, "A103", "Terrace Plan", width, height))
    return _svg(width, height, "\n".join(parts))


def _site_plan(config: MountainRetreatConfig) -> str:
    width = 900
    height = 620
    cabin = Rect(320, 210, 260, 150)
    terrace = Rect(320, 370, 260, 120)
    parts = [
        _text(40, 40, "Site Plan", 22, "700"),
        _text(40, 62, "Schematic site plan - not for construction", 12),
        _north_arrow(805, 70),
        _rect(Rect(70, 95, 720, 430), "#f8fbf6", "#779966", 1.5),
        _line(105, 475, 300, 365, "#8b8b8b", 12),
        _text(100, 500, f"Access: {config.site.access_road_type}", 10),
        _rect(cabin, "#f7f7f7", "#111", 2.0),
        _rect(terrace, "#e8f4df", "#6a8f3a", 1.8, "8 4"),
        _text(cabin.x + 70, cabin.y + 75, "Cabin footprint", 12, "700"),
        _text(terrace.x + 70, terrace.y + 62, "Panoramic terrace", 12, "700"),
        _dimension(
            cabin.x,
            cabin.y - 20,
            cabin.x + cabin.width,
            cabin.y - 20,
            f"{config.building.footprint_length_m:g} m",
        ),
        _dimension(
            cabin.x - 18,
            cabin.y,
            cabin.x - 18,
            cabin.y + cabin.height,
            f"{config.building.footprint_width_m:g} m",
        ),
        _text(90, 120, f"Location: {config.site.location_name}", 11),
        _text(90, 140, f"Slope assumption: {config.site.slope_percent:g}%", 11),
        _text(90, 160, f"Drainage risk: {config.site.drainage_risk}", 11),
        _title_block(config, "A001", "Site Plan", width, height),
    ]
    return _svg(width, height, "\n".join(parts))


def _elevation(config: MountainRetreatConfig, code: str, title: str, side: bool = False) -> str:
    width = 900
    height = 520
    base = Rect(170, 300, 520 if not side else 340, 90)
    roof_peak_x = base.x + base.width / 2
    parts = [
        _text(40, 40, title, 22, "700"),
        _text(40, 62, "Schematic elevation - not for construction", 12),
        _rect(base, "#f9f9f9", "#111", 2),
        f'<polygon points="{base.x:.1f},{base.y:.1f} {roof_peak_x:.1f},{base.y - 115:.1f} '
        f'{base.x + base.width:.1f},{base.y:.1f}" fill="#f2f2f2" stroke="#111" stroke-width="2"/>',
        _line(base.x + 45, base.y + 20, base.x + 170, base.y + 20, "#2f80ed", 5),
        _line(
            base.x + 220,
            base.y + 20,
            base.x + 390 if not side else base.x + 300,
            base.y + 20,
            "#2f80ed",
            5,
        ),
        _text(base.x + 12, base.y + 72, config.building.facade_type, 10),
        _text(base.x + 12, base.y - 35, config.building.roof_type, 10),
        _dimension(
            base.x + base.width + 24,
            base.y,
            base.x + base.width + 24,
            base.y - 115,
            f"{config.building.max_height_m:g} m max",
        ),
        _title_block(config, code, title, width, height),
    ]
    return _svg(width, height, "\n".join(parts))


def _section(config: MountainRetreatConfig, code: str, title: str, cross: bool = False) -> str:
    width = 900
    height = 560
    slab_y = 390
    length = 560 if not cross else 360
    parts = [
        _text(40, 40, title, 22, "700"),
        _text(40, 62, "Schematic section - not for construction", 12),
        _line(150, slab_y, 150 + length, slab_y, "#111", 3),
        _line(150, slab_y, 230, 215, "#111", 2),
        _line(150 + length, slab_y, 230, 215, "#111", 2),
        _line(230, 215, 150 + length - 80, 215, "#111", 2),
        _line(150, slab_y - 120, 150 + length, slab_y - 120, "#777", 1.5, "5 4"),
        _text(165, slab_y - 135, "Gallery / upper zone", 11),
        _text(165, slab_y - 25, "Ground floor", 11),
        _text(165, slab_y + 28, "Foundation / frost protection concept", 11),
        _dimension(
            150 + length + 26,
            slab_y,
            150 + length + 26,
            215,
            f"{config.building.max_height_m:g} m max",
        ),
        _title_block(config, code, title, width, height),
    ]
    return _svg(width, height, "\n".join(parts))


def _foundation_concept(config: MountainRetreatConfig) -> str:
    width = 900
    height = 520
    parts = [
        _text(40, 40, "Foundation Concept", 22, "700"),
        _text(40, 62, "Schematic structural concept - not for construction", 12),
        _rect(Rect(170, 190, 520, 60), "#ddd", "#111", 2),
        _rect(Rect(190, 250, 80, 95), "#cfcfcf", "#111", 1.5),
        _rect(Rect(590, 250, 80, 95), "#cfcfcf", "#111", 1.5),
        _line(140, 345, 725, 345, "#8b6b3f", 4),
        _text(180, 220, "Reinforced concrete slab/beam placeholder", 12, "700"),
        _text(180, 380, config.site.soil_assumption, 10),
        _text(
            180,
            400,
            f"Frost depth placeholder: {config.site.frost_depth_placeholder_cm:g} cm",
            10,
        ),
        _title_block(config, "S101", "Foundation Concept", width, height),
    ]
    return _svg(width, height, "\n".join(parts))


def _box(x: float, y: float, w: float, h: float, label: str, fill: str = "#f7f7f7") -> str:
    return "\n".join(
        (
            _rect(Rect(x, y, w, h), fill, "#333", 1.5),
            _text(x + 10, y + 25, label, 11, "700"),
        )
    )


def _arrow(x1: float, y1: float, x2: float, y2: float) -> str:
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        'stroke="#333" stroke-width="1.6" marker-end="url(#arrow)"/>'
    )


def _system_diagram(
    config: MountainRetreatConfig,
    code: str,
    title: str,
    boxes: list[tuple[str, str]],
) -> str:
    width = 900
    height = 580
    parts = [
        _text(40, 40, title, 22, "700"),
        _text(40, 62, "Schematic system diagram - not for construction", 12),
    ]
    positions: list[Rect] = []
    x = 80.0
    y = 130.0
    for label, fill in boxes:
        rect = Rect(x, y, 170, 58)
        positions.append(rect)
        parts.append(_box(rect.x, rect.y, rect.width, rect.height, label, fill))
        x += 220
        if x > 660:
            x = 80
            y += 115
    for first, second in zip(positions, positions[1:], strict=False):
        parts.append(
            _arrow(
                first.x + first.width,
                first.y + first.height / 2,
                second.x,
                second.y + second.height / 2,
            )
        )
    parts.append(_title_block(config, code, title, width, height))
    return _svg(width, height, "\n".join(parts))


def _room_system_plan(
    config: MountainRetreatConfig,
    code: str,
    title: str,
    label_factory: Callable[[Room], str],
    color: str,
) -> str:
    width = 900
    height = 700
    parts = [
        _text(40, 40, title, 22, "700"),
        _text(40, 62, "Schematic zone drawing - not for construction", 12),
        _north_arrow(820, 55),
    ]
    rooms = [*config.rooms_ground_floor.rooms, *config.rooms_gallery.rooms]
    for room, rect in _room_rects(rooms, 70, 110, 22):
        parts.extend(
            (
                _rect(rect, "#fff", "#333", 1.2),
                _text(rect.x + 6, rect.y + 18, room.name, 9, "700"),
                _text(rect.x + 6, rect.y + 34, label_factory(room), 8),
                _line(
                    rect.x + 6,
                    rect.y + rect.height - 8,
                    rect.x + rect.width - 6,
                    rect.y + rect.height - 8,
                    color,
                    3,
                ),
            )
        )
    parts.append(_title_block(config, code, title, width, height))
    return _svg(width, height, "\n".join(parts))


def generate_svg_drawings(config: MountainRetreatConfig, output_dir: Path) -> list[Path]:
    """Generate all schematic SVG drawings and return their paths."""
    drawings_dir = output_dir / DRAWINGS_OUTPUT_DIR
    drawings_dir.mkdir(parents=True, exist_ok=True)

    ground_rooms = config.rooms_ground_floor.rooms
    gallery_rooms = config.rooms_gallery.rooms
    drawing_map = {
        "A001_site_plan.svg": _site_plan(config),
        "A101_ground_floor_plan.svg": _floor_plan(
            config, "A101", "Ground Floor Plan", ground_rooms, include_terrace=True
        ),
        "A102_gallery_plan.svg": _floor_plan(config, "A102", "Gallery Plan", gallery_rooms),
        "A103_terrace_plan.svg": _terrace_plan(config),
        "A201_front_elevation.svg": _elevation(config, "A201", "Front Elevation"),
        "A202_side_elevation.svg": _elevation(config, "A202", "Side Elevation", side=True),
        "A301_longitudinal_section.svg": _section(config, "A301", "Longitudinal Section"),
        "A302_cross_section.svg": _section(config, "A302", "Cross Section", cross=True),
        "S101_foundation_concept.svg": _foundation_concept(config),
        "E101_electrical_zones.svg": _room_system_plan(
            config,
            "E101",
            "Electrical Zones",
            lambda room: f"{room.socket_count} sockets / {room.light_point_count} lights",
            "#e0a000",
        ),
        "P101_plumbing_zones.svg": _room_system_plan(
            config,
            "P101",
            "Plumbing Zones",
            lambda room: ", ".join(room.plumbing_fixtures) or "no fixtures",
            "#2f80ed",
        ),
        "H101_heating_zones.svg": _room_system_plan(
            config,
            "H101",
            "Heating Zones",
            lambda room: room.heating_type,
            "#d84a38",
        ),
        "SM101_smart_home_zones.svg": _room_system_plan(
            config,
            "SM101",
            "Smart Home Zones",
            lambda room: f"{config.smart_home.platform} zone",
            "#7755aa",
        ),
        "OG101_off_grid_system_diagram.svg": _system_diagram(
            config,
            "OG101",
            "Off-Grid System Diagram",
            [
                ("Grid", "#f7f7f7"),
                (f"PV {config.off_grid.pv_kwp:g} kWp", "#fff4cc"),
                (f"Battery {config.off_grid.battery_kwh:g} kWh", "#e8f4df"),
                ("Inverter/charger", "#f7f7f7"),
                ("Generator", "#f7f7f7"),
                ("Main panel", "#f7f7f7"),
                ("Critical loads", "#e6f2ff"),
                ("Water systems", "#e6f2ff"),
            ],
        ),
    }

    paths: list[Path] = []
    for filename in DRAWING_FILES:
        path = drawings_dir / filename
        path.write_text(drawing_map[filename], encoding="utf-8")
        paths.append(path)
    return paths
