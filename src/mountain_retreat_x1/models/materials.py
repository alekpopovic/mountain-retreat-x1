"""Material catalog models."""

from pydantic import Field

from mountain_retreat_x1.models.base import StrictModel


class MaterialItem(StrictModel):
    """Material quantity, pricing, and assumption reference."""

    code: str
    category: str
    subcategory: str
    name: str
    specification: str
    unit: str
    base_quantity: float = Field(ge=0)
    waste_percent: float = Field(ge=0, le=100)
    unit_price_low: float = Field(ge=0)
    unit_price_standard: float = Field(ge=0)
    unit_price_premium: float = Field(ge=0)
    supplier_placeholder: str
    formula_note: str
    assumption_ref: str
    notes: str = ""

