"""Site configuration models."""

from pydantic import Field

from mountain_retreat_x1.models.base import StrictModel


class SiteConfig(StrictModel):
    """Planning assumptions for the project site."""

    location_name: str
    country: str
    climate_zone: str
    altitude_m: float = Field(ge=0)
    slope_percent: float = Field(ge=0)
    access_road_type: str
    soil_assumption: str
    geotechnical_report_required: bool
    snow_load_placeholder_kn_m2: float = Field(gt=0)
    wind_load_placeholder_kn_m2: float = Field(gt=0)
    seismic_zone_placeholder: str
    drainage_risk: str
    frost_depth_placeholder_cm: float = Field(ge=0)

