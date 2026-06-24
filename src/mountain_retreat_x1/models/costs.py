"""Cost estimate models."""

from pydantic import Field

from mountain_retreat_x1.models.base import StrictModel


class CostItem(StrictModel):
    """Cost line item with visible planning assumptions."""

    code: str
    phase: str
    category: str
    description: str
    quantity: float = Field(ge=0)
    unit: str
    material_unit_cost: float = Field(ge=0)
    labor_unit_cost: float = Field(ge=0)
    machinery_unit_cost: float = Field(ge=0)
    contingency_percent: float = Field(ge=0, le=100)
    notes: str = ""

