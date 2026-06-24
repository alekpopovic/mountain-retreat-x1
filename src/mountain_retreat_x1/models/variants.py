"""Construction variant planning models."""

from pydantic import Field

from mountain_retreat_x1.models.base import StrictModel
from mountain_retreat_x1.models.building import ConstructionVariant
from mountain_retreat_x1.models.costs import CostItem
from mountain_retreat_x1.models.materials import MaterialItem


class VariantRisk(StrictModel):
    """Visible risk register entry for a construction variant."""

    id: str
    risk: str
    level: str
    mitigation: str
    professional_review_required: str


class VariantConfig(StrictModel):
    """Config-backed assumptions for one construction variant."""

    code: ConstructionVariant
    name: str
    status: str = "PRELIMINARY"
    description: str
    structural_concept_note: str
    quantity_reference: str
    quantity_multiplier: float = Field(gt=0)
    procurement_complexity: str
    self_build_difficulty: str
    self_build_warnings: list[str]
    risk_register: list[VariantRisk]
    material_items: list[MaterialItem]
    cost_items: list[CostItem]
    comparison_notes: list[str]
