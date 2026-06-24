"""QA/QC checklist models."""

from pydantic import Field

from mountain_retreat_x1.models.base import StrictModel


class ChecklistItem(StrictModel):
    """Inspection and quality checklist item."""

    id: str
    phase: str
    discipline: str
    inspection_item: str
    acceptance_criteria: str
    responsible_party: str
    required_photo: bool
    required_document: bool
    status_options: list[str] = Field(default_factory=list)
    notes: str = ""

