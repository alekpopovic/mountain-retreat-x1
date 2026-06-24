"""Project-level configuration models."""

from datetime import date

from pydantic import Field

from mountain_retreat_x1.models.base import StrictModel


class ProjectConfig(StrictModel):
    """Top-level project metadata and professional-limit notice."""

    project_name: str
    project_code: str
    version: str
    language: str
    country: str
    currency: str = "EUR"
    status: str = "PRELIMINARY"
    disclaimer: str
    revision_date: date
    author: str
    review_required_by: list[str] = Field(default_factory=list)

