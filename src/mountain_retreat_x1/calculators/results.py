"""Shared calculation result types."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CalculatedQuantity:
    """Traceable calculated value used in summaries and generated documents."""

    code: str
    label: str
    value: float
    unit: str
    formula_note: str
    assumptions_used: tuple[str, ...]
    approximate: bool = True
    warning: str = "Preliminary planning estimate; requires professional review."


QuantityMap = dict[str, CalculatedQuantity]

