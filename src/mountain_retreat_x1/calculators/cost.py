"""Cost calculations for static planning assumptions."""

from collections import defaultdict

from mountain_retreat_x1.calculators.results import CalculatedQuantity, QuantityMap
from mountain_retreat_x1.config.loader import MountainRetreatConfig
from mountain_retreat_x1.models import CostItem


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
        warning=config.cost_assumptions_serbia_2026.estimate_warning,
    )


def item_material_subtotal(item: CostItem) -> float:
    """Calculate line-item material subtotal."""
    return item.quantity * item.material_unit_cost


def item_labor_subtotal(item: CostItem) -> float:
    """Calculate line-item labor subtotal."""
    return item.quantity * item.labor_unit_cost


def item_machinery_subtotal(item: CostItem) -> float:
    """Calculate line-item machinery subtotal."""
    return item.quantity * item.machinery_unit_cost


def item_subtotal(item: CostItem) -> float:
    """Calculate line-item subtotal before contingency."""
    return (
        item_material_subtotal(item)
        + item_labor_subtotal(item)
        + item_machinery_subtotal(item)
    )


def item_contingency(item: CostItem) -> float:
    """Calculate line-item contingency."""
    return item_subtotal(item) * item.contingency_percent / 100


def item_total(item: CostItem) -> float:
    """Calculate line-item total including contingency."""
    return item_subtotal(item) + item_contingency(item)


def item_cost_breakdown(
    item: CostItem,
    currency: str,
    warning: str,
) -> QuantityMap:
    """Return traceable line-item cost quantities."""
    return {
        "material_subtotal": CalculatedQuantity(
            code=f"cost.item.{item.code}.material",
            label=f"{item.code} material subtotal",
            value=round(item_material_subtotal(item), 4),
            unit=currency,
            formula_note="quantity x material_unit_cost.",
            assumptions_used=(
                f"cost_items[{item.code}].quantity",
                f"cost_items[{item.code}].material_unit_cost",
            ),
            warning=warning,
        ),
        "labor_subtotal": CalculatedQuantity(
            code=f"cost.item.{item.code}.labor",
            label=f"{item.code} labor subtotal",
            value=round(item_labor_subtotal(item), 4),
            unit=currency,
            formula_note="quantity x labor_unit_cost.",
            assumptions_used=(
                f"cost_items[{item.code}].quantity",
                f"cost_items[{item.code}].labor_unit_cost",
            ),
            warning=warning,
        ),
        "machinery_subtotal": CalculatedQuantity(
            code=f"cost.item.{item.code}.machinery",
            label=f"{item.code} machinery subtotal",
            value=round(item_machinery_subtotal(item), 4),
            unit=currency,
            formula_note="quantity x machinery_unit_cost.",
            assumptions_used=(
                f"cost_items[{item.code}].quantity",
                f"cost_items[{item.code}].machinery_unit_cost",
            ),
            warning=warning,
        ),
        "item_subtotal": CalculatedQuantity(
            code=f"cost.item.{item.code}.subtotal",
            label=f"{item.code} item subtotal",
            value=round(item_subtotal(item), 4),
            unit=currency,
            formula_note="material subtotal + labor subtotal + machinery subtotal.",
            assumptions_used=(f"cost_items[{item.code}]",),
            warning=warning,
        ),
        "contingency": CalculatedQuantity(
            code=f"cost.item.{item.code}.contingency",
            label=f"{item.code} contingency",
            value=round(item_contingency(item), 4),
            unit=currency,
            formula_note="item subtotal x contingency_percent.",
            assumptions_used=(f"cost_items[{item.code}].contingency_percent",),
            warning=warning,
        ),
    }


def material_subtotal(config: MountainRetreatConfig) -> CalculatedQuantity:
    return _quantity(
        config,
        "cost.material.subtotal",
        "Material subtotal",
        sum(
            item_material_subtotal(item)
            for item in config.cost_assumptions_serbia_2026.cost_items
        ),
        config.project.currency,
        "Sum of cost_items.quantity x cost_items.material_unit_cost.",
        ("cost_assumptions_serbia_2026.cost_items",),
    )


def labor_subtotal(config: MountainRetreatConfig) -> CalculatedQuantity:
    return _quantity(
        config,
        "cost.labor.subtotal",
        "Labor subtotal",
        sum(
            item_labor_subtotal(item)
            for item in config.cost_assumptions_serbia_2026.cost_items
        ),
        config.project.currency,
        "Sum of cost_items.quantity x cost_items.labor_unit_cost.",
        ("cost_assumptions_serbia_2026.cost_items",),
    )


def machinery_subtotal(config: MountainRetreatConfig) -> CalculatedQuantity:
    return _quantity(
        config,
        "cost.machinery.subtotal",
        "Machinery subtotal",
        sum(
            item_machinery_subtotal(item)
            for item in config.cost_assumptions_serbia_2026.cost_items
        ),
        config.project.currency,
        "Sum of cost_items.quantity x cost_items.machinery_unit_cost.",
        ("cost_assumptions_serbia_2026.cost_items",),
    )


def contingency(config: MountainRetreatConfig) -> CalculatedQuantity:
    return _quantity(
        config,
        "cost.contingency",
        "Contingency",
        sum(
            item_contingency(item)
            for item in config.cost_assumptions_serbia_2026.cost_items
        ),
        config.project.currency,
        "Sum of line-item subtotal x contingency_percent.",
        ("cost_assumptions_serbia_2026.cost_items[*].contingency_percent",),
    )


def total_by_phase(config: MountainRetreatConfig) -> QuantityMap:
    totals: defaultdict[str, float] = defaultdict(float)
    for item in config.cost_assumptions_serbia_2026.cost_items:
        totals[item.phase] += item_total(item)

    return {
        phase: _quantity(
            config,
            f"cost.phase.{phase}",
            f"Total by phase - {phase}",
            value,
            config.project.currency,
            "Sum of line-item totals for phase.",
            ("cost_assumptions_serbia_2026.cost_items[*].phase",),
        )
        for phase, value in totals.items()
    }


def total_by_category(config: MountainRetreatConfig) -> QuantityMap:
    totals: defaultdict[str, float] = defaultdict(float)
    for item in config.cost_assumptions_serbia_2026.cost_items:
        totals[item.category] += item_total(item)

    return {
        category: _quantity(
            config,
            f"cost.category.{category}",
            f"Total by category - {category}",
            value,
            config.project.currency,
            "Sum of line-item totals for category.",
            ("cost_assumptions_serbia_2026.cost_items[*].category",),
        )
        for category, value in totals.items()
    }


def total_cost(config: MountainRetreatConfig) -> CalculatedQuantity:
    return _quantity(
        config,
        "cost.total",
        "Total preliminary cost",
        sum(item_total(item) for item in config.cost_assumptions_serbia_2026.cost_items),
        config.project.currency,
        "Sum of all line-item totals including contingency.",
        ("cost_assumptions_serbia_2026.cost_items",),
    )


def cost_per_m2_gross(config: MountainRetreatConfig) -> CalculatedQuantity:
    return _quantity(
        config,
        "cost.per_m2.gross",
        "Cost per m2 gross",
        total_cost(config).value / config.building.gross_area_m2,
        f"{config.project.currency}/m2",
        "total preliminary cost / building.gross_area_m2.",
        ("cost.total", "building.gross_area_m2"),
    )


def cost_per_m2_net(config: MountainRetreatConfig) -> CalculatedQuantity:
    return _quantity(
        config,
        "cost.per_m2.net",
        "Cost per m2 net",
        total_cost(config).value / config.building.net_area_m2,
        f"{config.project.currency}/m2",
        "total preliminary cost / building.net_area_m2.",
        ("cost.total", "building.net_area_m2"),
    )


def cost_summary(config: MountainRetreatConfig) -> QuantityMap:
    """Return key cost calculations."""
    quantities = [
        material_subtotal(config),
        labor_subtotal(config),
        machinery_subtotal(config),
        contingency(config),
        total_cost(config),
        cost_per_m2_gross(config),
        cost_per_m2_net(config),
    ]
    return {quantity.code: quantity for quantity in quantities}
