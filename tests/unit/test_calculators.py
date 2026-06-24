from math import cos, radians

import pytest

from mountain_retreat_x1.calculators import area, cost, quantity
from mountain_retreat_x1.calculators.results import CalculatedQuantity
from mountain_retreat_x1.config import load_config


@pytest.fixture
def config():
    return load_config("config")


def assert_traceable(result: CalculatedQuantity, expected_warning: str | None = None) -> None:
    assert result.formula_note
    assert result.assumptions_used
    assert result.approximate is True
    assert result.warning
    if expected_warning is not None:
        assert result.warning == expected_warning


def test_total_room_area_by_floor(config) -> None:
    totals = area.total_room_area_by_floor(config)

    assert totals["ground_floor"].value == pytest.approx(113.4)
    assert totals["gallery"].value == pytest.approx(75.0)
    assert_traceable(totals["ground_floor"], config.calculator_assumptions.warning)


def test_total_net_area_and_difference(config) -> None:
    net_area = area.total_net_area(config)
    difference = area.net_area_difference(config)

    assert net_area.value == pytest.approx(188.4)
    assert difference.value == pytest.approx(43.4)
    assert_traceable(net_area, config.calculator_assumptions.warning)
    assert_traceable(difference, config.calculator_assumptions.warning)


def test_roof_rough_area_formula(config) -> None:
    expected = (
        config.building.footprint_length_m
        * config.building.footprint_width_m
        * (1 / cos(radians(config.building.roof_pitch_deg)))
        * config.calculator_assumptions.roof_overhang_factor
    )

    result = area.roof_rough_area_estimate(config)

    assert result.value == pytest.approx(expected)
    assert result.unit == "m2"
    assert_traceable(result, config.calculator_assumptions.warning)


def test_wall_finish_area_formula(config) -> None:
    raw_area = sum(
        2 * (room.length_m + room.width_m) * room.clear_height_m
        for room in area.all_rooms(config)
    )
    expected = raw_area * (1 - config.calculator_assumptions.wall_finish_opening_reduction_factor)

    result = area.wall_finish_area_estimate(config)

    assert result.value == pytest.approx(expected)
    assert_traceable(result, config.calculator_assumptions.warning)


def test_concrete_rebar_and_gravel_formulas(config) -> None:
    footprint = config.building.footprint_length_m * config.building.footprint_width_m
    concrete_expected = (
        footprint
        * config.calculator_assumptions.foundation_coverage_factor
        * config.calculator_assumptions.foundation_depth_m
    )
    gravel_expected = footprint * config.calculator_assumptions.gravel_depth_m

    concrete = quantity.concrete_volume_estimate(config)
    rebar = quantity.rebar_estimate(config)
    gravel = quantity.gravel_tampon_estimate(config)

    assert concrete.value == pytest.approx(concrete_expected)
    assert rebar.value == pytest.approx(
        concrete.value * config.calculator_assumptions.rebar_kg_per_m3
    )
    assert gravel.value == pytest.approx(gravel_expected)
    assert_traceable(concrete, config.calculator_assumptions.warning)
    assert_traceable(rebar, config.calculator_assumptions.warning)
    assert_traceable(gravel, config.calculator_assumptions.warning)


def test_variant_quantity_formulas(config) -> None:
    timber = quantity.timber_framing_estimate_standard_hybrid(config)
    clt = quantity.clt_estimate_premium_clt(config)
    masonry = quantity.masonry_block_estimate_masonry_hybrid(config)
    perimeter = 2 * (config.building.footprint_length_m + config.building.footprint_width_m)

    assert timber.value == pytest.approx(
        config.building.gross_area_m2
        * config.calculator_assumptions.standard_hybrid_timber_m3_per_m2_gross
    )
    assert clt.value == pytest.approx(
        config.building.gross_area_m2
        * config.calculator_assumptions.premium_clt_m3_per_m2_gross
    )
    assert masonry.value == pytest.approx(
        perimeter
        * config.calculator_assumptions.masonry_wall_height_m
        * config.calculator_assumptions.masonry_blocks_per_m2_wall
    )


def test_envelope_and_terrace_quantity_formulas(config) -> None:
    facade = area.facade_rough_area_estimate(config)
    roof = area.roof_rough_area_estimate(config)

    assert quantity.roof_covering_area(config).value == pytest.approx(roof.value)
    assert quantity.facade_timber_area(config).value == pytest.approx(
        facade.value * config.calculator_assumptions.facade_timber_share
    )
    assert quantity.facade_stone_area(config).value == pytest.approx(
        facade.value * config.calculator_assumptions.facade_stone_share
    )
    assert quantity.terrace_decking_area(config).value == pytest.approx(
        config.terrace.terrace_area_m2
        * config.calculator_assumptions.terrace_decking_waste_factor
    )


def test_cost_line_item_formulas(config) -> None:
    item = config.cost_assumptions_serbia_2026.cost_items[0]

    assert cost.item_material_subtotal(item) == pytest.approx(
        item.quantity * item.material_unit_cost
    )
    assert cost.item_labor_subtotal(item) == pytest.approx(item.quantity * item.labor_unit_cost)
    assert cost.item_machinery_subtotal(item) == pytest.approx(
        item.quantity * item.machinery_unit_cost
    )
    assert cost.item_subtotal(item) == pytest.approx(
        item.quantity
        * (item.material_unit_cost + item.labor_unit_cost + item.machinery_unit_cost)
    )
    assert cost.item_contingency(item) == pytest.approx(
        cost.item_subtotal(item) * item.contingency_percent / 100
    )
    breakdown = cost.item_cost_breakdown(
        item,
        config.project.currency,
        config.cost_assumptions_serbia_2026.estimate_warning,
    )

    assert breakdown["item_subtotal"].value == pytest.approx(cost.item_subtotal(item))
    assert breakdown["contingency"].value == pytest.approx(cost.item_contingency(item))
    assert_traceable(
        breakdown["item_subtotal"],
        config.cost_assumptions_serbia_2026.estimate_warning,
    )


def test_cost_totals_by_phase_and_category(config) -> None:
    phase_totals = cost.total_by_phase(config)
    category_totals = cost.total_by_category(config)

    assert phase_totals["foundations"].value == pytest.approx(
        cost.item_total(config.cost_assumptions_serbia_2026.cost_items[0])
    )
    assert category_totals["structure"].value == pytest.approx(
        sum(
            cost.item_total(item)
            for item in config.cost_assumptions_serbia_2026.cost_items
            if item.category == "structure"
        )
    )


def test_cost_summary_formulas(config) -> None:
    expected_total = sum(
        cost.item_total(item) for item in config.cost_assumptions_serbia_2026.cost_items
    )

    total = cost.total_cost(config)
    gross = cost.cost_per_m2_gross(config)
    net = cost.cost_per_m2_net(config)

    assert total.value == pytest.approx(expected_total)
    assert gross.value == pytest.approx(expected_total / config.building.gross_area_m2)
    assert net.value == pytest.approx(expected_total / config.building.net_area_m2)
    assert_traceable(total, config.cost_assumptions_serbia_2026.estimate_warning)
    assert_traceable(gross, config.cost_assumptions_serbia_2026.estimate_warning)
    assert_traceable(net, config.cost_assumptions_serbia_2026.estimate_warning)
