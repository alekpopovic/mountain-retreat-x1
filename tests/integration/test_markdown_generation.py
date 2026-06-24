from pathlib import Path

from typer.testing import CliRunner

from mountain_retreat_x1.cli import app
from mountain_retreat_x1.config import load_config

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


def _self_build_step_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.startswith("### Step "))


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


def test_maintenance_manual_contains_year_based_sections(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    text = (output_dir / "markdown" / "12_maintenance_manual.md").read_text(encoding="utf-8")
    for section in (
        "## 6. 5-year maintenance",
        "## 7. 10-year maintenance",
        "## 8. 20-year maintenance",
        "## 9. 30-year renewal planning",
    ):
        assert section in text
    assert "Planning horizon:** 30 years" in text
    assert "| Task | Frequency | Responsible person | Estimated effort |" in text
    assert "PRELIMINARY" in text
    assert "not for construction" in text.lower()


def test_self_build_guide_contains_at_least_100_normal_steps(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    text = (output_dir / "markdown" / "13_self_build_guide.md").read_text(encoding="utf-8")
    assert _self_build_step_count(text) >= 100
    assert "Stop point requiring professional review" in text
    assert "Licensed structural engineer" in text
    assert "not for construction" in text.lower()


def test_self_build_guide_large_mode_contains_at_least_300_steps(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(
        app,
        ["generate", "markdown", "--large", "--output-dir", str(output_dir)],
    )

    assert result.exit_code == 0
    text = (output_dir / "markdown" / "13_self_build_guide.md").read_text(encoding="utf-8")
    assert _self_build_step_count(text) >= 300
    assert "Large step-by-step planning mode" in text
    assert "Stop point requiring professional review" in text


def test_architectural_package_contains_all_room_names(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    config = load_config("config")
    room_names = [
        room.name for room in [*config.rooms_ground_floor.rooms, *config.rooms_gallery.rooms]
    ]

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    text = (output_dir / "markdown" / "02_architectural_package.md").read_text(encoding="utf-8")
    for room_name in room_names:
        assert room_name in text


def test_architectural_package_contains_required_sections_and_schedules(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    text = (output_dir / "markdown" / "02_architectural_package.md").read_text(encoding="utf-8")
    for section in (
        "## 1. Design Intent",
        "## 2. Mountain Cabin Concept",
        "## 3. Site Orientation Assumptions",
        "## 4. Functional Zoning",
        "## 5. Ground Floor Plan Narrative",
        "## 6. Gallery Plan Narrative",
        "## 7. Terrace Design Narrative",
        "## 8. Room Data Sheets",
        "## 9. Door and Window Schedule",
        "## 10. Facade Concept",
        "## 11. Roof Concept",
        "## 12. Material Palette",
        "## 13. Daylight and Views",
        "## 14. Natural Ventilation Strategy",
        "## 15. Accessibility Considerations",
        "## 16. Fire Safety Concept Placeholders",
        "## 17. Drawing Index",
        "## 18. Architect Review Checklist",
    ):
        assert section in text

    assert "Preliminary planning document only" in text
    assert "Required Professional Review" in text
    assert "W-GF-LIV" in text
    assert "D-GF-ENT" in text


def test_structural_concept_contains_required_sections_and_review_language(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    text = (output_dir / "markdown" / "03_structural_concept.md").read_text(encoding="utf-8")
    for section in (
        "## 1. Structural Design Philosophy",
        "## 2. Required Geotechnical Investigation",
        "## 3. Site Risks for Mountain Terrain",
        "## 4. Foundation Concept",
        "## 5. Frost Protection Concept",
        "## 6. Drainage Strategy",
        "## 7. Ground Slab Concept",
        "## 8. Structural Variant A: standard timber hybrid",
        "## 9. Structural Variant B: premium CLT/glulam",
        "## 10. Structural Variant C: masonry hybrid",
        "## 11. Roof Structure Concept",
        "## 12. Terrace Structure Concept",
        "## 13. Snow Load Placeholder",
        "## 14. Wind Load Placeholder",
        "## 15. Seismic Placeholder",
        "## 16. Connection Concept",
        "## 17. Moisture and Condensation Risks",
        "## 18. Durability Strategy",
        "## 19. Preliminary Quantity Summary",
        "## 20. Structural Engineer Review Checklist",
    ):
        assert section in text

    assert "Licensed structural engineer" in text
    assert "not a final structural calculation" in text
    assert "not a reinforcement drawing set" in text
    assert "not a safety-compliance certificate" in text
    assert "No final beam" in text
    assert "Must Be Engineered by Licensed Professional" in text


def test_electrical_package_contains_required_sections_and_placeholder_language(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    text = (output_dir / "markdown" / "04_electrical_package.md").read_text(encoding="utf-8")
    for section in (
        "## 1. Electrical Design Concept",
        "## 2. Grid Connection Assumptions",
        "## 3. Main Distribution Board Concept",
        "## 4. Circuit Schedule",
        "## 5. Lighting Concept",
        "## 6. Socket and Appliance Concept",
        "## 7. Kitchen Electrical Concept",
        "## 8. Bathroom Electrical Concept",
        "## 9. Technical Room Electrical Concept",
        "## 10. Terrace Electrical Concept",
        "## 11. Exterior Lighting",
        "## 12. Grounding and Bonding Placeholder",
        "## 13. Surge Protection Concept",
        "## 14. Backup Generator Concept",
        "## 15. Solar PV Integration Concept",
        "## 16. Battery Integration Concept",
        "## 17. Smart Home Wiring Concept",
        "## 18. Testing and Commissioning Checklist",
        "## 19. Licensed Electrician Review Checklist",
    ):
        assert section in text

    assert "Circuit code" in text
    assert "Breaker TBD by licensed electrician" in text
    assert "Cable size TBD by licensed electrician" in text
    assert "does not claim compliance" in text
    assert "Licensed electrician" in text


def test_electrical_package_covers_major_rooms(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    major_rooms = (
        "Technical room",
        "Guest bathroom",
        "Kitchen",
        "Dining",
        "Living room",
        "Fireplace zone",
        "Master bathroom",
        "Bathroom 2",
        "Terrace",
    )

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    text = (output_dir / "markdown" / "04_electrical_package.md").read_text(encoding="utf-8")
    for room_name in major_rooms:
        assert room_name in text


def test_plumbing_package_contains_required_sections_fixture_schedule_and_warnings(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    text = (output_dir / "markdown" / "05_plumbing_wastewater.md").read_text(encoding="utf-8")
    for section in (
        "## 1. Water Supply Concept",
        "## 2. Mains Water Option",
        "## 3. Water Tank Option",
        "## 4. Pump and Pressure Concept",
        "## 5. Cold Water Distribution",
        "## 6. Hot Water Distribution",
        "## 7. Domestic Hot Water Source",
        "## 8. Kitchen Plumbing",
        "## 9. Bathroom Plumbing",
        "## 10. Laundry/Utility Plumbing",
        "## 11. Exterior Taps",
        "## 12. Freeze Protection",
        "## 13. Wastewater Concept",
        "## 14. Septic Tank Option",
        "## 15. Biological Treatment Plant Option",
        "## 16. Vent Pipe Concept",
        "## 17. Rainwater Drainage",
        "## 18. Terrace Drainage",
        "## 19. Foundation Drainage",
        "## 20. Maintenance Checklist",
        "## 21. Licensed Plumbing/Mechanical Review Checklist",
    ):
        assert section in text

    assert "Fixture code" in text
    assert "not final pipe sizing" in text
    assert "does not claim local wastewater approval" in text
    assert "No local wastewater approval" in text
    assert "frost" in text.lower()
    assert "slope" in text.lower()
    assert "maintenance access" in text.lower()


def test_plumbing_package_includes_all_configured_wet_rooms(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    config = load_config("config")
    wet_room_names = [
        room.name
        for room in [*config.rooms_ground_floor.rooms, *config.rooms_gallery.rooms]
        if room.plumbing_fixtures
    ]

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    text = (output_dir / "markdown" / "05_plumbing_wastewater.md").read_text(encoding="utf-8")
    for room_name in wet_room_names:
        assert room_name in text

    assert "Terrace" in text
    assert "outdoor sink placeholder" in text
    assert "jacuzzi/spa water and drain placeholder" in text


def test_hvac_package_contains_required_sections_tables_and_review_language(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    text = (output_dir / "markdown" / "06_hvac_package.md").read_text(encoding="utf-8")
    for section in (
        "## 1. Heating and Cooling Concept",
        "## 2. Mountain Climate Assumptions",
        "## 3. Air-to-Water Heat Pump Concept",
        "## 4. Underfloor Heating Concept",
        "## 5. Heating Zones",
        "## 6. Fireplace Concept",
        "## 7. Domestic Hot Water Integration",
        "## 8. Mechanical Ventilation Concept",
        "## 9. Heat Recovery Ventilation Option",
        "## 10. Bathroom Extraction",
        "## 11. Technical Room Layout",
        "## 12. Pipe Insulation",
        "## 13. Winterization",
        "## 14. Commissioning Checklist",
        "## 15. Maintenance Schedule",
        "## 16. Licensed Mechanical Engineer Review Checklist",
    ):
        assert section in text

    assert "Zone code" in text
    assert "Design temperature placeholder" in text
    assert "Floor heating loop placeholder" in text
    assert "HVAC Equipment Table" in text
    assert "Power/capacity placeholder" in text
    assert "does not produce a final heat loss calculation" in text
    assert "Licensed mechanical engineer" in text
    assert "Commissioning Checklist" in text


def test_hvac_package_includes_all_rooms_in_zone_considerations(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    config = load_config("config")
    room_names = [
        room.name for room in [*config.rooms_ground_floor.rooms, *config.rooms_gallery.rooms]
    ]

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    text = (output_dir / "markdown" / "06_hvac_package.md").read_text(encoding="utf-8")
    for room_name in room_names:
        assert room_name in text


def test_smart_home_package_contains_required_sections_tables_and_warnings(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    text = (output_dir / "markdown" / "07_smart_home_security.md").read_text(encoding="utf-8")
    for section in (
        "## 1. Smart Home Architecture",
        "## 2. Local-First Control Philosophy",
        "## 3. Network Topology",
        "## 4. VLAN/Security Concept",
        "## 5. Device Schedule",
        "## 6. Sensor Schedule",
        "## 7. Automation List",
        "## 8. Security System",
        "## 9. CCTV Concept",
        "## 10. Access Control",
        "## 11. Water Leak Protection",
        "## 12. Fire/CO Detection",
        "## 13. Solar and Battery Monitoring",
        "## 14. Remote Access",
        "## 15. Backup and Restore",
        "## 16. Cybersecurity Checklist",
        "## 17. Maintenance Checklist",
    ):
        assert section in text

    assert "Device code" in text
    assert "Sensor code" in text
    assert "Home Assistant" in text
    assert "Zigbee" in text
    assert "Matter" in text
    assert "MQTT" in text
    assert "PoE camera set" in text
    assert "Smart lock" in text
    assert "UPS for network equipment" in text
    assert "does not certify cybersecurity" in text
    assert "must not be the primary approved detection system" in text
    assert "local legal/privacy review" in text


def test_smart_home_package_contains_required_automation_examples(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    text = (output_dir / "markdown" / "07_smart_home_security.md").read_text(encoding="utf-8")
    for automation in (
        "Winter freeze protection",
        "Water leak shutoff",
        "Away mode",
        "Night security mode",
        "Terrace lighting scene",
        "Low battery warning",
        "Generator alert",
        "Solar production notification",
    ):
        assert automation in text


def test_off_grid_package_contains_required_sections_tables_and_warnings(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    text = (output_dir / "markdown" / "08_off_grid_package.md").read_text(encoding="utf-8")
    for section in (
        "## 1. Off-grid Design Philosophy",
        "## 2. Grid-connected Versus Off-grid Modes",
        "## 3. Solar PV Concept",
        "## 4. Battery Concept",
        "## 5. Inverter/Charger Concept",
        "## 6. Backup Generator Concept",
        "## 7. Critical Loads",
        "## 8. Non-critical Loads",
        "## 9. Load Estimate Table",
        "## 10. Winter Solar Risk",
        "## 11. Generator Runtime Concept",
        "## 12. Water Storage",
        "## 13. Wastewater Independence",
        "## 14. Internet Connectivity",
        "## 15. Emergency Modes",
        "## 16. Maintenance Schedule",
        "## 17. Failure Scenario Table",
        "## 18. Licensed Electrical/Mechanical Review Checklist",
    ):
        assert section in text

    assert "Load code" in text
    assert "Power W placeholder" in text
    assert "Daily kWh placeholder" in text
    assert "Failure Scenario Table" in text
    assert "does not promise full off-grid autonomy" in text
    assert "All energy values are planning assumptions" in text
    assert "Winter performance is the major risk" in text
    assert "Extended snow cover on PV array" in text


def test_off_grid_package_contains_loads_and_failure_scenarios(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"

    result = runner.invoke(app, ["generate", "markdown", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    text = (output_dir / "markdown" / "08_off_grid_package.md").read_text(encoding="utf-8")
    for expected in (
        "Heating controls and circulation pumps",
        "Network, router, Home Assistant, and sensors",
        "Water pump / pressure system",
        "PoE cameras and security devices",
        "Domestic hot water backup element",
        "EV charging placeholder",
        "Backup generator fails to start",
        "Inverter/charger fault",
        "Internet outage",
    ):
        assert expected in text
