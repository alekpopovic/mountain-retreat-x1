# Mountain Retreat X1 Implementation Plan

## 1. Project Goal

Build a Python-based documentation generation system for a modern mountain cabin with a large panoramic terrace.

The system must generate:

1. PDF documentation volumes
2. Excel bill of materials
3. Excel cost estimate
4. Excel Gantt schedule
5. Excel QA/QC checklists
6. SVG schematic drawings
7. Markdown source documents
8. YAML configuration files
9. Final ZIP package

## 2. Project Philosophy

Mountain Retreat X1 must produce preliminary planning documentation only.

It must not pretend to replace:

- licensed architects
- structural engineers
- electrical engineers
- mechanical engineers
- local permitting authorities

All generated documents must clearly state that they are preliminary planning documents and require professional review before use in design, permitting, procurement, or construction.

## 3. Core Architecture

The future implementation should follow this pipeline:

1. Load YAML source configuration.
2. Validate all inputs with Pydantic schemas.
3. Normalize the project model.
4. Render Markdown source documents with Jinja2.
5. Generate schematic SVG drawings.
6. Generate Excel workbooks with OpenPyXL.
7. Generate PDF volumes with WeasyPrint or ReportLab.
8. Copy source YAML and generated artifacts into a package directory.
9. Generate a manifest.
10. Create a final ZIP package.

## 4. Staged Plan

### Stage 0: Repository and Tooling Setup

Purpose:

Create the project foundation without implementation code.

Deliverables:

- repository documentation
- planned package layout
- tooling metadata
- placeholder directories
- planning YAML templates

Completion criteria:

- no implementation code exists
- project plan is documented
- safety constraints are visible from the repository root

### Stage 1: Configuration and Schemas

Purpose:

Create the structured source of truth.

Future generated outputs:

- validated YAML configuration
- normalized in-memory project model
- assumptions report
- initial manifest

Implementation tasks:

- define Pydantic models
- implement YAML loading
- validate required fields
- validate professional-review requirements
- validate that assumptions are explicit

### Stage 2: Markdown Documentation

Purpose:

Generate human-readable source documents from templates.

Future generated outputs:

- `output/markdown/00_assumptions.md`
- `output/markdown/01_project_overview.md`
- `output/markdown/02_design_intent.md`
- `output/markdown/03_preliminary_scope.md`
- `output/markdown/04_materials_summary.md`
- `output/markdown/05_construction_sequence.md`
- `output/markdown/06_review_requirements.md`
- `output/markdown/07_limitations_and_disclaimers.md`

Implementation tasks:

- create Jinja2 Markdown templates
- inject project metadata
- inject assumptions
- inject disclaimers
- add forbidden-language tests

### Stage 3: SVG Schematic Drawings

Purpose:

Generate simple schematic drawings using plain SVG.

Future generated outputs:

- `output/svg/site_orientation.svg`
- `output/svg/concept_floor_plan.svg`
- `output/svg/panoramic_terrace_layout.svg`
- `output/svg/roof_concept.svg`
- `output/svg/section_concept.svg`
- `output/svg/envelope_concept.svg`

Implementation tasks:

- create SVG helpers
- add title blocks
- add approximate dimensions
- add schematic and not-for-construction labels
- avoid stamps, seals, permit marks, or approval language

### Stage 4: Excel Workbooks

Purpose:

Generate structured planning spreadsheets.

Future generated outputs:

- `output/excel/bom.xlsx`
- `output/excel/cost_estimate.xlsx`
- `output/excel/gantt_schedule.xlsx`
- `output/excel/qaqc_checklists.xlsx`

Implementation tasks:

- create workbook utilities
- generate BOM sheets
- generate cost estimate sheets
- generate schedule and Gantt sheets
- generate QA/QC checklist sheets
- include assumptions and disclaimers in every workbook

### Stage 5: PDF Volumes

Purpose:

Produce final readable PDF volumes for preliminary planning review.

Future generated outputs:

- `output/pdf/volume_01_project_brief.pdf`
- `output/pdf/volume_02_design_and_scope.pdf`
- `output/pdf/volume_03_materials_and_bom.pdf`
- `output/pdf/volume_04_cost_estimate.pdf`
- `output/pdf/volume_05_schedule.pdf`
- `output/pdf/volume_06_qaqc_checklists.pdf`
- `output/pdf/volume_07_drawings_appendix.pdf`

Implementation tasks:

- choose WeasyPrint or ReportLab
- render title pages
- include disclaimers
- include assumptions
- include review requirements
- include generated tables and drawings where practical

### Stage 6: Final Package

Purpose:

Collect all generated artifacts and source configuration into one auditable ZIP package.

Future generated output:

- `output/mountain_retreat_x1_package.zip`

Package contents:

- `markdown/`
- `pdf/`
- `excel/`
- `svg/`
- `yaml/`
- `manifest.json`
- `README_PACKAGE.md`

Implementation tasks:

- copy generated files
- copy source YAML
- generate package README
- generate manifest
- create ZIP archive
- optionally include checksums

### Stage 7: Quality Gate

Purpose:

Verify safety, correctness, and repeatability.

Checks:

- pytest passes
- ruff passes
- mypy runs where practical
- generated package contains required files
- every generated artifact includes preliminary disclaimers where technically practical
- forbidden legal or professional-approval language is absent

## 5. Definition of Done

The project is implementation-ready when:

- staged implementation plan exists
- risks are identified
- repository structure is defined
- testing strategy is defined
- phase outputs are defined
- no implementation code has been written

