from datetime import date

import pytest
from pydantic import ValidationError

from mountain_retreat_x1.models import (
    BuildingConfig,
    ChecklistItem,
    ConstructionPhase,
    CostItem,
    Drawing,
    MaterialItem,
    ProjectConfig,
    Room,
    SiteConfig,
)


def valid_project_data() -> dict[str, object]:
    return {
        "project_name": "Mountain Retreat X1",
        "project_code": "MRX1",
        "version": "0.1.0",
        "language": "en",
        "country": "RS",
        "disclaimer": "Preliminary planning document only.",
        "revision_date": "2026-06-24",
        "author": "Mountain Retreat X1",
        "review_required_by": ["licensed architect", "licensed structural engineer"],
    }


def valid_site_data() -> dict[str, object]:
    return {
        "location_name": "Mountain site",
        "country": "RS",
        "climate_zone": "mountain",
        "altitude_m": 950,
        "slope_percent": 12,
        "access_road_type": "gravel",
        "soil_assumption": "To be verified by geotechnical report.",
        "geotechnical_report_required": True,
        "snow_load_placeholder_kn_m2": 2.5,
        "wind_load_placeholder_kn_m2": 0.8,
        "seismic_zone_placeholder": "To be confirmed",
        "drainage_risk": "medium",
        "frost_depth_placeholder_cm": 90,
    }


def valid_building_data() -> dict[str, object]:
    return {
        "gross_area_m2": 120,
        "net_area_m2": 96,
        "terrace_area_m2": 48,
        "footprint_length_m": 14,
        "footprint_width_m": 9,
        "floors": 2,
        "max_height_m": 7.5,
        "roof_pitch_deg": 28,
        "construction_variant": "standard_hybrid",
        "roof_type": "pitched",
        "facade_type": "timber and fiber cement",
        "occupancy_people": 6,
        "design_life_years": 50,
    }


def valid_room_data() -> dict[str, object]:
    return {
        "code": "LIV-01",
        "name": "Living Room",
        "floor": "ground",
        "zone": "day",
        "length_m": 6,
        "width_m": 5,
        "area_m2": 30,
        "clear_height_m": 2.8,
        "function": "living",
        "floor_finish": "engineered wood",
        "wall_finish": "painted gypsum board",
        "ceiling_finish": "painted gypsum board",
        "heating_type": "radiant floor",
        "ventilation_type": "natural plus mechanical extract",
        "window_area_m2": 10,
        "door_count": 2,
        "socket_count": 8,
        "light_point_count": 4,
        "plumbing_fixtures": [],
        "notes": "Preliminary room data sheet.",
    }


def valid_material_data() -> dict[str, object]:
    return {
        "code": "MAT-001",
        "category": "structure",
        "subcategory": "timber",
        "name": "Glulam beam",
        "specification": "Placeholder specification; engineer review required.",
        "unit": "m3",
        "base_quantity": 4.2,
        "waste_percent": 10,
        "unit_price_low": 700,
        "unit_price_standard": 950,
        "unit_price_premium": 1250,
        "supplier_placeholder": "TBD",
        "formula_note": "Length x section area from preliminary framing assumptions.",
        "assumption_ref": "assumptions.structural",
        "notes": "Preliminary only.",
    }


def valid_cost_data() -> dict[str, object]:
    return {
        "code": "COST-001",
        "phase": "structure",
        "category": "materials",
        "description": "Structural timber placeholder",
        "quantity": 4.2,
        "unit": "m3",
        "material_unit_cost": 950,
        "labor_unit_cost": 120,
        "machinery_unit_cost": 60,
        "contingency_percent": 20,
        "notes": "Static planning rate only.",
    }


def valid_phase_data() -> dict[str, object]:
    return {
        "wbs": "1.1",
        "name": "Site review",
        "description": "Preliminary site investigation and professional review.",
        "duration_days": 5,
        "dependencies": [],
        "responsible_party": "licensed professionals",
        "required_tools": ["survey equipment"],
        "required_machinery": [],
        "safety_notes": ["Confirm access and slope hazards."],
        "qa_checklist_refs": ["QA-SITE-001"],
        "inspection_required": True,
    }


def valid_checklist_data() -> dict[str, object]:
    return {
        "id": "QA-SITE-001",
        "phase": "site review",
        "discipline": "site",
        "inspection_item": "Confirm site access assumptions.",
        "acceptance_criteria": "Reviewed by qualified professional.",
        "responsible_party": "project reviewer",
        "required_photo": True,
        "required_document": True,
        "status_options": ["open", "reviewed", "blocked"],
        "notes": "Preliminary checklist item.",
    }


def valid_drawing_data() -> dict[str, object]:
    return {
        "code": "A-001",
        "title": "Concept Floor Plan",
        "discipline": "architecture",
        "scale": "schematic",
        "output_file": "output/drawings/concept_floor_plan.svg",
        "status": "PRELIMINARY",
        "notes": "Not for construction.",
    }


def test_project_config_defaults_currency_and_status() -> None:
    project = ProjectConfig.model_validate(valid_project_data())

    assert project.currency == "EUR"
    assert project.status == "PRELIMINARY"
    assert project.revision_date == date(2026, 6, 24)


def test_all_models_accept_valid_values() -> None:
    assert SiteConfig.model_validate(valid_site_data()).location_name == "Mountain site"
    building = BuildingConfig.model_validate(valid_building_data())

    assert building.construction_variant == "standard_hybrid"
    assert Room.model_validate(valid_room_data()).area_m2 == 30
    assert MaterialItem.model_validate(valid_material_data()).waste_percent == 10
    assert CostItem.model_validate(valid_cost_data()).contingency_percent == 20
    assert ConstructionPhase.model_validate(valid_phase_data()).duration_days == 5
    assert ChecklistItem.model_validate(valid_checklist_data()).required_photo is True
    assert Drawing.model_validate(valid_drawing_data()).status == "PRELIMINARY"


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("gross_area_m2", 0),
        ("net_area_m2", -1),
        ("terrace_area_m2", -10),
    ],
)
def test_building_areas_must_be_positive(field_name: str, invalid_value: float) -> None:
    data = valid_building_data()
    data[field_name] = invalid_value

    with pytest.raises(ValidationError, match=field_name):
        BuildingConfig.model_validate(data)


def test_room_area_must_be_positive() -> None:
    data = valid_room_data()
    data["area_m2"] = 0

    with pytest.raises(ValidationError, match="area_m2"):
        Room.model_validate(data)


@pytest.mark.parametrize("waste_percent", [-0.1, 100.1])
def test_material_waste_percent_must_be_between_0_and_100(waste_percent: float) -> None:
    data = valid_material_data()
    data["waste_percent"] = waste_percent

    with pytest.raises(ValidationError, match="waste_percent"):
        MaterialItem.model_validate(data)


def test_construction_variant_must_be_allowed_value() -> None:
    data = valid_building_data()
    data["construction_variant"] = "unsupported_variant"

    with pytest.raises(ValidationError, match="construction_variant"):
        BuildingConfig.model_validate(data)


def test_unknown_fields_are_rejected() -> None:
    data = valid_project_data()
    data["approval_stamp"] = "fake seal"

    with pytest.raises(ValidationError, match="approval_stamp"):
        ProjectConfig.model_validate(data)
