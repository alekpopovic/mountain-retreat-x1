from pathlib import Path
from shutil import copytree

from typer.testing import CliRunner

from mountain_retreat_x1.cli import app

runner = CliRunner()


def test_validate_cli_reports_invalid_yaml_config(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    copytree("config", config_dir)
    building_file = config_dir / "building.yaml"
    invalid_building = building_file.read_text(encoding="utf-8").replace(
        "gross_area_m2: 180",
        "gross_area_m2: -1",
    )
    building_file.write_text(
        invalid_building,
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", "--config-dir", str(config_dir)])

    assert result.exit_code == 1
    assert "Configuration validation failed" in result.output
    assert "gross_area_m2" in result.output


def test_summary_cli_prints_development_summary() -> None:
    result = runner.invoke(app, ["summary"])

    assert result.exit_code == 0
    assert "Mountain Retreat X1" in result.output
    assert "Gross area" in result.output
    assert "ground_floor" in result.output
    assert "Smart home" in result.output


def test_generate_all_creates_output_folders(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "all", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    assert "Planned Generators" in result.output
    for subdir in ("pdf", "excel", "drawings", "zip"):
        assert (output_dir / subdir).is_dir()


def test_generate_specific_placeholders_create_output_folders(tmp_path: Path) -> None:
    for command in ("excel", "pdf", "drawings"):
        output_dir = tmp_path / command
        result = runner.invoke(app, ["generate", command, "--output-dir", str(output_dir)])

        assert result.exit_code == 0
        assert "placeholder completed" in result.output
        for subdir in ("pdf", "excel", "drawings", "zip"):
            assert (output_dir / subdir).is_dir()


def test_clean_preserves_gitkeep_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    generated_pdf = output_dir / "pdf" / "volume.pdf"
    keep_file = output_dir / "pdf" / ".gitkeep"
    generated_pdf.parent.mkdir(parents=True)
    generated_pdf.write_text("generated", encoding="utf-8")
    keep_file.write_text("", encoding="utf-8")

    result = runner.invoke(app, ["clean", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    assert "Clean completed" in result.output
    assert keep_file.exists()
    assert not generated_pdf.exists()
    for subdir in ("pdf", "excel", "drawings", "zip"):
        assert (output_dir / subdir / ".gitkeep").exists()
