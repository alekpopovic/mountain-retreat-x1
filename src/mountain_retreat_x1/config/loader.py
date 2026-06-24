"""YAML configuration loading and validation."""

from dataclasses import dataclass
from dataclasses import replace as dataclass_replace
from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

from mountain_retreat_x1.models import (
    BuildingConfig,
    CalculatorAssumptionsConfig,
    ChecklistSeedConfig,
    ConstructionPhasesConfig,
    ConstructionVariant,
    CostAssumptionsConfig,
    LocalizationConfig,
    MaterialConfig,
    OffGridConfig,
    ProjectConfig,
    RoomConfig,
    SiteConfig,
    SmartHomeConfig,
    TerraceConfig,
    VariantConfig,
)

SUPPORTED_VARIANTS: tuple[ConstructionVariant, ...] = (
    "standard_hybrid",
    "premium_clt",
    "masonry_hybrid",
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
    calculator_assumptions: CalculatorAssumptionsConfig
    variants: dict[str, VariantConfig]
    variant: VariantConfig


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


def load_variants(root: Path) -> dict[str, VariantConfig]:
    """Load all construction variant YAML files."""
    variants_dir = root / "variants"
    variants: dict[str, VariantConfig] = {}
    for variant_code in SUPPORTED_VARIANTS:
        variant = load_typed_yaml(variants_dir / f"{variant_code}.yaml", VariantConfig)
        if variant.code != variant_code:
            raise ConfigLoadError(
                f"Variant file {variant_code}.yaml declares code {variant.code!r}."
            )
        variants[variant.code] = variant
    return variants


def load_config(config_dir: Path | str = Path("config")) -> MountainRetreatConfig:
    """Load and validate the complete Mountain Retreat X1 configuration."""
    root = Path(config_dir)
    building = load_typed_yaml(root / "building.yaml", BuildingConfig)
    variants = load_variants(root)
    variant = variants.get(building.construction_variant)
    if variant is None:
        raise ConfigLoadError(
            f"Missing variant configuration for {building.construction_variant!r}."
        )

    return MountainRetreatConfig(
        project=load_typed_yaml(root / "project.yaml", ProjectConfig),
        site=load_typed_yaml(root / "site.yaml", SiteConfig),
        building=building,
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
        calculator_assumptions=load_typed_yaml(
            root / "calculator_assumptions.yaml",
            CalculatorAssumptionsConfig,
        ),
        variants=variants,
        variant=variant,
    )


def with_variant(
    config: MountainRetreatConfig,
    variant_code: str | None,
) -> MountainRetreatConfig:
    """Return a config bundle with the active construction variant overridden."""
    if variant_code is None:
        return config
    if variant_code not in SUPPORTED_VARIANTS:
        supported = ", ".join(SUPPORTED_VARIANTS)
        raise ConfigLoadError(
            f"Unsupported construction variant '{variant_code}'. Supported: {supported}."
        )
    variant = config.variants[variant_code]
    building = config.building.model_copy(update={"construction_variant": variant_code})
    return dataclass_replace(config, building=building, variant=variant)
