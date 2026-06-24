import json
from pathlib import Path
from zipfile import ZipFile

from typer.testing import CliRunner

from mountain_retreat_x1.cli import app

runner = CliRunner()


def test_generate_all_final_pipeline_creates_manifest_and_zip(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(
        app,
        [
            "generate",
            "all",
            "--project",
            "config/project.yaml",
            "--output",
            str(output_dir),
            "--lang",
            "sr-Latn",
            "--large",
        ],
    )

    assert result.exit_code == 0
    assert "Generate-all completed" in result.output

    manifest_path = output_dir / "BUILD_MANIFEST.json"
    package_path = (
        output_dir
        / "zip"
        / "Mountain_Retreat_X1_Professional_Documentation_Package.zip"
    )
    assert manifest_path.exists()
    assert package_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["project_name"] == "Mountain Retreat X1"
    assert manifest["language"] == "sr-Latn"
    assert manifest["large_mode"] is True
    assert "markdown/01_project_charter.md" in manifest["files"]
    assert "pdf/01_Project_Charter.pdf" in manifest["files"]
    assert "excel/Mountain_Retreat_X1_BOM.xlsx" in manifest["files"]
    assert "drawings/A001_site_plan.svg" in manifest["files"]
    assert "config/project.yaml" in manifest["files"]
    assert "BUILD_MANIFEST.json" in manifest["files"]
    assert manifest["professional_review_required"]

    with ZipFile(package_path) as archive:
        names = set(archive.namelist())

    expected_names = {
        "pdf/01_Project_Charter.pdf",
        "excel/Mountain_Retreat_X1_BOM.xlsx",
        "excel/Mountain_Retreat_X1_QA_QC_Checklists.xlsx",
        "drawings/A001_site_plan.svg",
        "markdown/01_project_charter.md",
        "config/project.yaml",
        "README.md",
        "LEGAL_AND_PROFESSIONAL_LIMITS.md",
        "ASSUMPTIONS_SUMMARY.md",
        "INDEX.md",
        "BUILD_MANIFEST.json",
    }
    assert expected_names.issubset(names)
