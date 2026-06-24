from pathlib import Path

from typer.testing import CliRunner

from mountain_retreat_x1.cli import app

EXPECTED_MARKDOWN_FILES = (
    "01_project_charter.md",
    "02_architectural_package.md",
    "03_structural_concept.md",
    "04_electrical_package.md",
    "05_plumbing_wastewater.md",
    "06_hvac_package.md",
    "07_smart_home_security.md",
    "08_off_grid_package.md",
    "09_bom_summary.md",
    "10_cost_estimate_summary.md",
    "11_construction_management.md",
    "12_maintenance_manual.md",
    "13_self_build_guide.md",
    "14_legal_and_professional_limits.md",
)

runner = CliRunner()


def test_generate_markdown_creates_all_expected_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    assert "Markdown generation completed" in result.output
    for filename in EXPECTED_MARKDOWN_FILES:
        assert (output_dir / "markdown" / filename).exists()


def test_generated_markdown_contains_required_safety_language(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    for filename in EXPECTED_MARKDOWN_FILES:
        text = (output_dir / "markdown" / filename).read_text(encoding="utf-8")
        assert "PRELIMINARY" in text
        assert "Required Professional Review" in text
        assert "licensed professionals" in text.lower() or "licensed" in text.lower()
        assert "not for construction" in text.lower()
        assert "## Assumptions" in text
        assert "## Limitations" in text

