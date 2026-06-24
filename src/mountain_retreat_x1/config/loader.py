"""YAML configuration loading and validation."""

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

from mountain_retreat_x1.models import (
    BuildingConfig,
    ChecklistSeedConfig,
    ConstructionPhasesConfig,
    CostAssumptionsConfig,
    LocalizationConfig,
    MaterialConfig,
    OffGridConfig,
    ProjectConfig,
    RoomConfig,
    SiteConfig,
    SmartHomeConfig,
    TerraceConfig,
)


class ConfigLoadError(ValueError):
    """Raised when YAML configuration cannot be loaded or validated."""


@dataclass(frozen=True)
class MountainRetreatConfig:
    """Typed repository configuration bundle."""

    project: ProjectConfig
    site: SiteConfig
    building: BuildingConfig
    rooms_ground_floor: RoomConfig
    rooms_gallery: RoomConfig
    terrace: TerraceConfig
    materials_core: MaterialConfig
    materials_mep: MaterialConfig
    cost_assumptions_serbia_2026: CostAssumptionsConfig
    construction_phases: ConstructionPhasesConfig
    checklists_seed: ChecklistSeedConfig
    smart_home: SmartHomeConfig
    off_grid: OffGridConfig
    localization: LocalizationConfig


def load_yaml_file(path: Path) -> object:
    """Load a YAML file and return its parsed data."""
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except FileNotFoundError as exc:
        raise ConfigLoadError(f"Missing configuration file: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigLoadError(f"Invalid YAML syntax in {path}: {exc}") from exc

    if data is None:
        raise ConfigLoadError(f"Configuration file is empty: {path}")

    return data


def load_typed_yaml[ModelT: BaseModel](path: Path, model_type: type[ModelT]) -> ModelT:
    """Load one YAML file and validate it with a Pydantic model."""
    data = load_yaml_file(path)
    try:
        return model_type.model_validate(data)
    except ValidationError as exc:
        raise ConfigLoadError(f"Validation failed for {path}:\n{exc}") from exc


def load_config(config_dir: Path | str = Path("config")) -> MountainRetreatConfig:
    """Load and validate the complete Mountain Retreat X1 configuration."""
    root = Path(config_dir)

    return MountainRetreatConfig(
        project=load_typed_yaml(root / "project.yaml", ProjectConfig),
        site=load_typed_yaml(root / "site.yaml", SiteConfig),
        building=load_typed_yaml(root / "building.yaml", BuildingConfig),
        rooms_ground_floor=load_typed_yaml(root / "rooms_ground_floor.yaml", RoomConfig),
        rooms_gallery=load_typed_yaml(root / "rooms_gallery.yaml", RoomConfig),
        terrace=load_typed_yaml(root / "terrace.yaml", TerraceConfig),
        materials_core=load_typed_yaml(root / "materials_core.yaml", MaterialConfig),
        materials_mep=load_typed_yaml(root / "materials_mep.yaml", MaterialConfig),
        cost_assumptions_serbia_2026=load_typed_yaml(
            root / "cost_assumptions_serbia_2026.yaml",
            CostAssumptionsConfig,
        ),
        construction_phases=load_typed_yaml(
            root / "construction_phases.yaml",
            ConstructionPhasesConfig,
        ),
        checklists_seed=load_typed_yaml(root / "checklists_seed.yaml", ChecklistSeedConfig),
        smart_home=load_typed_yaml(root / "smart_home.yaml", SmartHomeConfig),
        off_grid=load_typed_yaml(root / "off_grid.yaml", OffGridConfig),
        localization=load_typed_yaml(root / "localization.yaml", LocalizationConfig),
    )
