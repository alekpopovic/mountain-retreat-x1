"""Composite configuration models loaded from YAML."""

from pydantic import Field

from mountain_retreat_x1.models.base import StrictModel
from mountain_retreat_x1.models.checklists import ChecklistItem
from mountain_retreat_x1.models.costs import CostItem
from mountain_retreat_x1.models.materials import MaterialItem
from mountain_retreat_x1.models.rooms import Room
from mountain_retreat_x1.models.schedule import ConstructionPhase


class RoomConfig(StrictModel):
    """Collection of room data sheets."""

    rooms: list[Room]


class MaterialConfig(StrictModel):
    """Collection of material items."""

    materials: list[MaterialItem]


class CostAssumptionsConfig(StrictModel):
    """Static planning cost assumptions."""

    country: str
    currency: str = "EUR"
    assumption_year: int
    status: str = "PRELIMINARY"
    source_policy: str
    vat_included: bool
    contingency_percent: float = Field(ge=0, le=100)
    regional_adjustment_note: str
    estimate_warning: str
    cost_items: list[CostItem]


class ConstructionPhasesConfig(StrictModel):
    """Collection of construction phases."""

    phases: list[ConstructionPhase]


class ChecklistSeedConfig(StrictModel):
    """Collection of QA/QC checklist seed items."""

    checklist_items: list[ChecklistItem]


class TerraceZone(StrictModel):
    """Planning zone on the panoramic terrace."""

    code: str
    name: str
    area_m2: float = Field(gt=0)
    function: str
    surface_finish: str
    guard_required: bool
    utility_requirements: list[str] = Field(default_factory=list)
    notes: str = ""


class TerraceConfig(StrictModel):
    """Panoramic terrace planning configuration."""

    terrace_area_m2: float = Field(gt=0)
    status: str = "PRELIMINARY"
    disclaimer: str
    zones: list[TerraceZone]


class SmartHomeConfig(StrictModel):
    """Smart-home planning configuration."""

    platform: str
    protocols: list[str]
    network_assumptions: dict[str, str]
    systems: list[str]
    notes: str


class OffGridConfig(StrictModel):
    """Optional off-grid package assumptions."""

    enabled_optional_package: bool
    pv_kwp: float = Field(ge=0)
    battery_kwh: float = Field(ge=0)
    generator: str
    water_tank_l: int = Field(ge=0)
    wastewater_options: list[str]
    limitations: list[str]


class LocalizedString(StrictModel):
    """Localized text variants."""

    en: str
    sr_latn: str = Field(alias="sr-Latn")
    sr_cyrl: str = Field(alias="sr-Cyrl")


class LocalizationConfig(StrictModel):
    """Localization configuration and safety strings."""

    default_language: str
    supported_languages: list[str]
    strings: dict[str, LocalizedString]


class CalculatorAssumptionsConfig(StrictModel):
    """YAML-backed assumptions used by quantity calculators."""

    status: str = "PRELIMINARY"
    warning: str
    foundation_depth_m: float = Field(gt=0)
    foundation_coverage_factor: float = Field(gt=0, le=1)
    rebar_kg_per_m3: float = Field(gt=0)
    gravel_depth_m: float = Field(gt=0)
    waterproofing_overlap_factor: float = Field(gt=0)
    standard_hybrid_timber_m3_per_m2_gross: float = Field(gt=0)
    premium_clt_m3_per_m2_gross: float = Field(gt=0)
    masonry_blocks_per_m2_wall: float = Field(gt=0)
    masonry_wall_height_m: float = Field(gt=0)
    roof_overhang_factor: float = Field(gt=0)
    facade_height_factor: float = Field(gt=0)
    facade_opening_reduction_factor: float = Field(ge=0, lt=1)
    facade_timber_share: float = Field(ge=0, le=1)
    facade_stone_share: float = Field(ge=0, le=1)
    terrace_decking_waste_factor: float = Field(gt=0)
    insulation_area_factor: float = Field(gt=0)
    vapor_barrier_area_factor: float = Field(gt=0)
    membrane_area_factor: float = Field(gt=0)
    wall_finish_opening_reduction_factor: float = Field(ge=0, lt=1)
