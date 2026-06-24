"""Preliminary quantity estimators."""

from mountain_retreat_x1.calculators import area
from mountain_retreat_x1.calculators.results import CalculatedQuantity, QuantityMap
from mountain_retreat_x1.config.loader import MountainRetreatConfig


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


def concrete_volume_estimate(config: MountainRetreatConfig) -> CalculatedQuantity:
    assumptions = config.calculator_assumptions
    footprint = config.building.footprint_length_m * config.building.footprint_width_m
    return _quantity(
        config,
        "qty.concrete.volume",
        "Concrete volume estimate",
        footprint * assumptions.foundation_coverage_factor * assumptions.foundation_depth_m,
        "m3",
        "footprint area x foundation_coverage_factor x foundation_depth_m.",
        (
            "building.footprint_length_m",
            "building.footprint_width_m",
            "calculator_assumptions.foundation_coverage_factor",
            "calculator_assumptions.foundation_depth_m",
        ),
    )


def rebar_estimate(config: MountainRetreatConfig) -> CalculatedQuantity:
    concrete = concrete_volume_estimate(config)
    return _quantity(
        config,
        "qty.rebar.mass",
        "Rebar estimate",
        concrete.value * config.calculator_assumptions.rebar_kg_per_m3,
        "kg",
        "concrete volume estimate x rebar_kg_per_m3.",
        ("qty.concrete.volume", "calculator_assumptions.rebar_kg_per_m3"),
    )


def gravel_tampon_estimate(config: MountainRetreatConfig) -> CalculatedQuantity:
    footprint = config.building.footprint_length_m * config.building.footprint_width_m
    return _quantity(
        config,
        "qty.gravel.volume",
        "Gravel/tampon estimate",
        footprint * config.calculator_assumptions.gravel_depth_m,
        "m3",
        "footprint area x gravel_depth_m.",
        (
            "building.footprint_length_m",
            "building.footprint_width_m",
            "calculator_assumptions.gravel_depth_m",
        ),
    )


def waterproofing_area(config: MountainRetreatConfig) -> CalculatedQuantity:
    footprint = config.building.footprint_length_m * config.building.footprint_width_m
    return _quantity(
        config,
        "qty.waterproofing.area",
        "Waterproofing area",
        footprint * config.calculator_assumptions.waterproofing_overlap_factor,
        "m2",
        "footprint area x waterproofing_overlap_factor.",
        (
            "building.footprint_length_m",
            "building.footprint_width_m",
            "calculator_assumptions.waterproofing_overlap_factor",
        ),
    )


def timber_framing_estimate_standard_hybrid(config: MountainRetreatConfig) -> CalculatedQuantity:
    return _quantity(
        config,
        "qty.timber.standard_hybrid",
        "Timber framing estimate for standard_hybrid",
        (
            config.building.gross_area_m2
            * config.calculator_assumptions.standard_hybrid_timber_m3_per_m2_gross
        ),
        "m3",
        "gross_area_m2 x standard_hybrid_timber_m3_per_m2_gross.",
        (
            "building.gross_area_m2",
            "calculator_assumptions.standard_hybrid_timber_m3_per_m2_gross",
        ),
    )


def clt_estimate_premium_clt(config: MountainRetreatConfig) -> CalculatedQuantity:
    return _quantity(
        config,
        "qty.clt.premium_clt",
        "CLT estimate for premium_clt",
        config.building.gross_area_m2 * config.calculator_assumptions.premium_clt_m3_per_m2_gross,
        "m3",
        "gross_area_m2 x premium_clt_m3_per_m2_gross.",
        ("building.gross_area_m2", "calculator_assumptions.premium_clt_m3_per_m2_gross"),
    )


def masonry_block_estimate_masonry_hybrid(config: MountainRetreatConfig) -> CalculatedQuantity:
    perimeter = 2 * (config.building.footprint_length_m + config.building.footprint_width_m)
    wall_area = perimeter * config.calculator_assumptions.masonry_wall_height_m
    return _quantity(
        config,
        "qty.masonry.blocks",
        "Masonry block estimate for masonry_hybrid",
        wall_area * config.calculator_assumptions.masonry_blocks_per_m2_wall,
        "pcs",
        "perimeter x masonry_wall_height_m x masonry_blocks_per_m2_wall.",
        (
            "building.footprint_length_m",
            "building.footprint_width_m",
            "calculator_assumptions.masonry_wall_height_m",
            "calculator_assumptions.masonry_blocks_per_m2_wall",
        ),
    )


def roof_covering_area(config: MountainRetreatConfig) -> CalculatedQuantity:
    roof = area.roof_rough_area_estimate(config)
    return _quantity(
        config,
        "qty.roof.covering",
        "Roof covering area",
        roof.value,
        "m2",
        "Uses rough roof area estimate.",
        ("area.roof.rough",),
    )


def facade_timber_area(config: MountainRetreatConfig) -> CalculatedQuantity:
    facade = area.facade_rough_area_estimate(config)
    return _quantity(
        config,
        "qty.facade.timber",
        "Facade timber area",
        facade.value * config.calculator_assumptions.facade_timber_share,
        "m2",
        "rough facade area x facade_timber_share.",
        ("area.facade.rough", "calculator_assumptions.facade_timber_share"),
    )


def facade_stone_area(config: MountainRetreatConfig) -> CalculatedQuantity:
    facade = area.facade_rough_area_estimate(config)
    return _quantity(
        config,
        "qty.facade.stone",
        "Facade stone area",
        facade.value * config.calculator_assumptions.facade_stone_share,
        "m2",
        "rough facade area x facade_stone_share.",
        ("area.facade.rough", "calculator_assumptions.facade_stone_share"),
    )


def terrace_decking_area(config: MountainRetreatConfig) -> CalculatedQuantity:
    return _quantity(
        config,
        "qty.terrace.decking",
        "Terrace decking area",
        config.terrace.terrace_area_m2 * config.calculator_assumptions.terrace_decking_waste_factor,
        "m2",
        "terrace_area_m2 x terrace_decking_waste_factor.",
        ("terrace.terrace_area_m2", "calculator_assumptions.terrace_decking_waste_factor"),
    )


def insulation_area(config: MountainRetreatConfig) -> CalculatedQuantity:
    envelope_area = (
        area.facade_rough_area_estimate(config).value + area.roof_rough_area_estimate(config).value
    )
    return _quantity(
        config,
        "qty.insulation.area",
        "Insulation area",
        envelope_area * config.calculator_assumptions.insulation_area_factor,
        "m2",
        "(rough facade area + rough roof area) x insulation_area_factor.",
        (
            "area.facade.rough",
            "area.roof.rough",
            "calculator_assumptions.insulation_area_factor",
        ),
    )


def vapor_barrier_area(config: MountainRetreatConfig) -> CalculatedQuantity:
    return _quantity(
        config,
        "qty.vapor_barrier.area",
        "Vapor barrier area",
        insulation_area(config).value * config.calculator_assumptions.vapor_barrier_area_factor,
        "m2",
        "insulation area x vapor_barrier_area_factor.",
        ("qty.insulation.area", "calculator_assumptions.vapor_barrier_area_factor"),
    )


def membrane_area(config: MountainRetreatConfig) -> CalculatedQuantity:
    return _quantity(
        config,
        "qty.membrane.area",
        "Membrane area",
        roof_covering_area(config).value * config.calculator_assumptions.membrane_area_factor,
        "m2",
        "roof covering area x membrane_area_factor.",
        ("qty.roof.covering", "calculator_assumptions.membrane_area_factor"),
    )


def quantity_summary(config: MountainRetreatConfig) -> QuantityMap:
    """Return key preliminary quantity estimates."""
    quantities = [
        concrete_volume_estimate(config),
        rebar_estimate(config),
        gravel_tampon_estimate(config),
        waterproofing_area(config),
        timber_framing_estimate_standard_hybrid(config),
        clt_estimate_premium_clt(config),
        masonry_block_estimate_masonry_hybrid(config),
        roof_covering_area(config),
        facade_timber_area(config),
        facade_stone_area(config),
        terrace_decking_area(config),
        insulation_area(config),
        vapor_barrier_area(config),
        membrane_area(config),
    ]
    return {quantity.code: quantity for quantity in quantities}
