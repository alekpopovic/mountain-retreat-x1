from pathlib import Path

import pytest

from mountain_retreat_x1.config import ConfigLoadError, load_config, load_typed_yaml, load_yaml_file
from mountain_retreat_x1.models import ProjectConfig


def test_load_default_config_returns_typed_objects() -> None:
    config = load_config(Path("config"))

    assert config.project.project_name == "Mountain Retreat X1"
    assert config.project.currency == "EUR"
    assert config.project.status == "PRELIMINARY"
    assert config.building.gross_area_m2 == 180
    assert config.building.construction_variant == "standard_hybrid"
    assert len(config.rooms_ground_floor.rooms) == 10
    assert len(config.rooms_gallery.rooms) == 7
    assert config.smart_home.platform == "Home Assistant"
    assert config.off_grid.pv_kwp == 15
    assert config.localization.default_language == "sr-Latn"
    assert config.calculator_assumptions.rebar_kg_per_m3 == 95


def test_invalid_yaml_syntax_raises_clear_error(tmp_path: Path) -> None:
    invalid_file = tmp_path / "invalid.yaml"
    invalid_file.write_text("project_name: [not closed\n", encoding="utf-8")

    with pytest.raises(ConfigLoadError, match="Invalid YAML syntax"):
        load_yaml_file(invalid_file)


def test_invalid_project_yaml_raises_clear_validation_error(tmp_path: Path) -> None:
    invalid_file = tmp_path / "project.yaml"
    invalid_file.write_text(
        "\n".join(
            [
                "project_name: Mountain Retreat X1",
                "project_code: MRX1",
                "version: 0.1.0",
                "language: sr-Latn",
                "country: Serbia",
                "revision_date: 2026-06-24",
                "author: Test",
                "review_required_by: []",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigLoadError, match="disclaimer"):
        load_typed_yaml(invalid_file, ProjectConfig)
