"""Building configuration models."""

from typing import Literal

from pydantic import Field

from mountain_retreat_x1.models.base import StrictModel

ConstructionVariant = Literal["standard_hybrid", "premium_clt", "masonry_hybrid"]


class BuildingConfig(StrictModel):
    """High-level building geometry and design assumptions."""

    gross_area_m2: float = Field(gt=0)
    net_area_m2: float = Field(gt=0)
    terrace_area_m2: float = Field(gt=0)
    footprint_length_m: float = Field(gt=0)
    footprint_width_m: float = Field(gt=0)
    floors: int = Field(gt=0)
    max_height_m: float = Field(gt=0)
    roof_pitch_deg: float = Field(ge=0, le=90)
    construction_variant: ConstructionVariant
    roof_type: str
    facade_type: str
    occupancy_people: int = Field(gt=0)
    design_life_years: int = Field(gt=0)

