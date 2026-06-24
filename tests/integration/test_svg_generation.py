from pathlib import Path

from typer.testing import CliRunner

from mountain_retreat_x1.cli import app
from mountain_retreat_x1.generators import DRAWING_FILES

runner = CliRunner()


def test_generate_drawings_creates_all_expected_svg_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "drawings", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    assert "Drawing generation completed" in result.output
    for filename in DRAWING_FILES:
        path = output_dir / "drawings" / filename
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "<svg" in text
        assert "Mountain Retreat X1" in text
        assert "schematic / not for construction" in text


def test_floor_plan_svg_contains_rooms_dimensions_and_terrace(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "drawings", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    text = (output_dir / "drawings" / "A101_ground_floor_plan.svg").read_text(
        encoding="utf-8"
    )
    assert "Kitchen" in text
    assert "Living room" in text
    assert "18 m" in text
    assert "10 m" in text
    assert "Panoramic terrace" in text
