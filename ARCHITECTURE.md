# Architecture

Mountain Retreat X1 is a deterministic document-generation pipeline. It converts YAML assumptions into preliminary Markdown, PDF, Excel, SVG, manifest, and ZIP artifacts.

## Pipeline

1. Load YAML configuration from `config/` or from `--project config/project.yaml`.
2. Validate configuration with Pydantic models.
3. Run deterministic area, quantity, and cost calculators.
4. Render Markdown source volumes with Jinja2.
5. Generate plain SVG schematic drawings.
6. Export Excel workbooks with OpenPyXL.
7. Render PDF volumes from Markdown.
8. Generate `INDEX.md`, `ASSUMPTIONS_SUMMARY.md`, and `BUILD_MANIFEST.json`.
9. Assemble the final ZIP package.

## Main Packages

- `cli`: Typer command surface and final build orchestration
- `config`: YAML loading and typed config bundles
- `models`: Pydantic domain schemas
- `calculators`: deterministic area, quantity, and cost results
- `generators`: Markdown, PDF, and SVG generation
- `exporters`: Excel workbook generation
- `localization`: Serbian Latin and English visible-text support
- `validation`: validation namespace for future safety checks

## Data Flow

YAML files are the source of truth. Templates and exporters must not hide assumptions or invent final approvals. Calculated quantities include formula notes and assumption references where practical. Generated outputs repeat the preliminary status and professional review requirements.

## Large Mode

Large mode is deterministic and expands useful planning content:

- architectural room data coordination rows
- self-build guide with 300+ phase-specific steps
- QA/QC workbook with 1000+ useful checklist rows
- expanded BOM line items by room and terrace zone
- 30-year maintenance calendar
- construction management risk, procurement, inspection, and document registers

## Final Package

The final pipeline writes:

- `output/INDEX.md`
- `output/ASSUMPTIONS_SUMMARY.md`
- `output/BUILD_MANIFEST.json`
- `output/zip/Mountain_Retreat_X1_Professional_Documentation_Package.zip`

The ZIP includes generated artifacts, YAML configs, README, legal limits, assumptions summary, index, and manifest.
