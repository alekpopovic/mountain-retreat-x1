"""Shared Pydantic model configuration."""

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Base class for repository data models."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

