from pathlib import Path

from typer.testing import CliRunner

from mountain_retreat_x1.cli import app
from mountain_retreat_x1.generators import PDF_FILES

runner = CliRunner()


def test_generate_pdf_creates_all_expected_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "pdf", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    assert "PDF generation completed" in result.output
    for filename in PDF_FILES.values():
        path = output_dir / "pdf" / filename
        assert path.exists()
        assert path.stat().st_size > 1000


def test_generate_pdf_command_exits_successfully_with_existing_markdown(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"

    markdown_result = runner.invoke(
        app,
        ["generate", "markdown", "--output-dir", str(output_dir)],
    )
    pdf_result = runner.invoke(app, ["generate", "pdf", "--output-dir", str(output_dir)])

    assert markdown_result.exit_code == 0
    assert pdf_result.exit_code == 0
    assert (output_dir / "pdf" / "01_Project_Charter.pdf").exists()


def test_generate_pdf_regenerates_markdown_for_requested_language(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"

    markdown_result = runner.invoke(
        app,
        ["generate", "markdown", "--lang", "en", "--output-dir", str(output_dir)],
    )
    pdf_result = runner.invoke(
        app,
        ["generate", "pdf", "--lang", "sr-Latn", "--output-dir", str(output_dir)],
    )

    assert markdown_result.exit_code == 0
    assert pdf_result.exit_code == 0
    markdown_text = (output_dir / "markdown" / "01_project_charter.md").read_text(
        encoding="utf-8"
    )
    assert "PRELIMINARNI planski dokument" in markdown_text
    assert "Obavezna napomena" in markdown_text
