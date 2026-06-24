"""Construction phase and schedule models."""

from pydantic import Field

from mountain_retreat_x1.models.base import StrictModel


class ConstructionPhase(StrictModel):
    """Work breakdown structure phase for preliminary scheduling."""

    wbs: str
    name: str
    description: str
    duration_days: int = Field(gt=0)
    dependencies: list[str] = Field(default_factory=list)
    responsible_party: str
    required_tools: list[str] = Field(default_factory=list)
    required_machinery: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    qa_checklist_refs: list[str] = Field(default_factory=list)
    inspection_required: bool

