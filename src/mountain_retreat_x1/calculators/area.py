"""Area and surface calculations."""

from math import cos, radians

from mountain_retreat_x1.calculators.results import CalculatedQuantity, QuantityMap
from mountain_retreat_x1.config.loader import MountainRetreatConfig
from mountain_retreat_x1.models import Room


def _quantity(
    config: MountainRetreatConfig,
    code: str,
    label: str,
    value: float,
    unit: str,
    formula_note: str,
    assumptions_used: tuple[str, ...],
) -> CalculatedQuantity:
    return CalculatedQuantity(
        code=code,
        label=label,
        value=round(value, 4),
        unit=unit,
        formula_note=formula_note,
        assumptions_used=assumptions_used,
        warning=config.calculator_assumptions.warning,
    )


def all_rooms(config: MountainRetreatConfig) -> list[Room]:
    """Return all configured rooms."""
    return [*config.rooms_ground_floor.rooms, *config.rooms_gallery.rooms]


def total_room_area_by_floor(config: MountainRetreatConfig) -> QuantityMap:
    """Calculate total configured room area by floor."""
    totals: dict[str, float] = {}
    for room in all_rooms(config):
        totals[room.floor] = totals.get(room.floor, 0) + room.area_m2

    return {
        floor: _quantity(
            config=config,
            code=f"area.rooms.{floor}",
            label=f"Room area - {floor}",
            value=area,
            unit="m2",
            formula_note="Sum of configured room area_m2 values for the floor.",
            assumptions_used=(f"rooms.{floor}[*].area_m2",),
        )
        for floor, area in totals.items()
    }


def total_net_area(config: MountainRetreatConfig) -> CalculatedQuantity:
    """Calculate total net area from room data sheets."""
    return _quantity(
        config=config,
        code="area.net.calculated",
        label="Calculated net area",
        value=sum(room.area_m2 for room in all_rooms(config)),
        unit="m2",
        formula_note="Sum of all configured room area_m2 values.",
        assumptions_used=("rooms_ground_floor.rooms[*].area_m2", "rooms_gallery.rooms[*].area_m2"),
    )


def net_area_difference(config: MountainRetreatConfig) -> CalculatedQuantity:
    """Calculate difference between room-derived net area and configured net area."""
    return _quantity(
        config=config,
        code="area.net.difference",
        label="Net area difference",
        value=total_net_area(config).value - config.building.net_area_m2,
        unit="m2",
        formula_note="Calculated net room area minus building.net_area_m2.",
        assumptions_used=("building.net_area_m2", "rooms.*.area_m2"),
    )


def terrace_area_by_zone(config: MountainRetreatConfig) -> QuantityMap:
    """Return terrace zone areas."""
    return {
        zone.code: _quantity(
            config=config,
            code=f"area.terrace.{zone.code}",
            label=zone.name,
            value=zone.area_m2,
            unit="m2",
            formula_note="Configured terrace zone area.",
            assumptions_used=(f"terrace.zones[{zone.code}].area_m2",),
        )
        for zone in config.terrace.zones
    }


def window_to_floor_ratio_by_room(config: MountainRetreatConfig) -> QuantityMap:
    """Calculate window-to-floor ratio by room."""
    return {
        room.code: _quantity(
            config=config,
            code=f"area.window_floor_ratio.{room.code}",
            label=f"Window-to-floor ratio - {room.name}",
            value=room.window_area_m2 / room.area_m2,
            unit="ratio",
            formula_note="room.window_area_m2 / room.area_m2.",
            assumptions_used=(f"rooms[{room.code}].window_area_m2", f"rooms[{room.code}].area_m2"),
        )
        for room in all_rooms(config)
    }


def facade_rough_area_estimate(config: MountainRetreatConfig) -> CalculatedQuantity:
    """Estimate facade area from footprint, height factor, and opening reduction."""
    assumptions = config.calculator_assumptions
    perimeter = 2 * (config.building.footprint_length_m + config.building.footprint_width_m)
    gross_facade = perimeter * config.building.max_height_m * assumptions.facade_height_factor
    net_facade = gross_facade * (1 - assumptions.facade_opening_reduction_factor)
    return _quantity(
        config=config,
        code="area.facade.rough",
        label="Rough facade area",
        value=net_facade,
        unit="m2",
        formula_note=(
            "2 x (footprint_length_m + footprint_width_m) x max_height_m x "
            "facade_height_factor x (1 - facade_opening_reduction_factor)."
        ),
        assumptions_used=(
            "building.footprint_length_m",
            "building.footprint_width_m",
            "building.max_height_m",
            "calculator_assumptions.facade_height_factor",
            "calculator_assumptions.facade_opening_reduction_factor",
        ),
    )


def roof_rough_area_estimate(config: MountainRetreatConfig) -> CalculatedQuantity:
    """Estimate roof area from footprint and roof pitch."""
    assumptions = config.calculator_assumptions
    plan_area = config.building.footprint_length_m * config.building.footprint_width_m
    pitch_factor = 1 / cos(radians(config.building.roof_pitch_deg))
    return _quantity(
        config=config,
        code="area.roof.rough",
        label="Rough roof area",
        value=plan_area * pitch_factor * assumptions.roof_overhang_factor,
        unit="m2",
        formula_note=(
            "footprint_length_m x footprint_width_m x pitch factor x roof_overhang_factor."
        ),
        assumptions_used=(
            "building.footprint_length_m",
            "building.footprint_width_m",
            "building.roof_pitch_deg",
            "calculator_assumptions.roof_overhang_factor",
        ),
    )


def floor_finish_area(config: MountainRetreatConfig) -> CalculatedQuantity:
    """Estimate floor finish area from configured room areas."""
    return _quantity(
        config=config,
        code="area.finish.floor",
        label="Floor finish area",
        value=total_net_area(config).value,
        unit="m2",
        formula_note="Sum of all room area_m2 values.",
        assumptions_used=("rooms.*.area_m2",),
    )


def wall_finish_area_estimate(config: MountainRetreatConfig) -> CalculatedQuantity:
    """Estimate wall finish area from room perimeters and clear heights."""
    reduction = config.calculator_assumptions.wall_finish_opening_reduction_factor
    area = sum(
        2 * (room.length_m + room.width_m) * room.clear_height_m
        for room in all_rooms(config)
    )
    return _quantity(
        config=config,
        code="area.finish.wall",
        label="Wall finish area estimate",
        value=area * (1 - reduction),
        unit="m2",
        formula_note=(
            "Sum of 2 x (room.length_m + room.width_m) x room.clear_height_m, "
            "reduced by wall_finish_opening_reduction_factor."
        ),
        assumptions_used=(
            "rooms.*.length_m",
            "rooms.*.width_m",
            "rooms.*.clear_height_m",
            "calculator_assumptions.wall_finish_opening_reduction_factor",
        ),
    )


def ceiling_finish_area(config: MountainRetreatConfig) -> CalculatedQuantity:
    """Estimate ceiling finish area from configured room areas."""
    return _quantity(
        config=config,
        code="area.finish.ceiling",
        label="Ceiling finish area",
        value=total_net_area(config).value,
        unit="m2",
        formula_note="Sum of all room area_m2 values.",
        assumptions_used=("rooms.*.area_m2",),
    )


def area_summary(config: MountainRetreatConfig) -> QuantityMap:
    """Return a compact set of key area calculations."""
    return {
        "calculated_net_area": total_net_area(config),
        "net_area_difference": net_area_difference(config),
        "facade_rough_area": facade_rough_area_estimate(config),
        "roof_rough_area": roof_rough_area_estimate(config),
        "floor_finish_area": floor_finish_area(config),
        "wall_finish_area": wall_finish_area_estimate(config),
        "ceiling_finish_area": ceiling_finish_area(config),
    }
