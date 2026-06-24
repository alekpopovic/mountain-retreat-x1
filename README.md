# Mountain Retreat X1

Mountain Retreat X1 is a Python 3.12 documentation generation system for preliminary planning of a modern mountain cabin with a large panoramic terrace. It builds a coordinated planning binder from YAML assumptions, Pydantic schemas, Jinja2 templates, OpenPyXL workbooks, SVG schematics, PDF volumes, and a final ZIP package.

All generated documents are preliminary planning documents only. They are not construction documents, permit documents, signed engineering calculations, professional approvals, procurement instructions, or legal approvals.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Optional WeasyPrint PDF support:

```bash
pip install -e ".[dev,pdf]"
```

The PDF generator uses WeasyPrint when available, ReportLab as a fallback, and a minimal built-in PDF fallback for development environments.

## Quick Start

```bash
mrx1 validate
mrx1 summary
mrx1 generate all --project config/project.yaml --output output --lang sr-Latn --large
```

The final command validates configuration, generates all source and output artifacts, writes `output/BUILD_MANIFEST.json`, writes `output/INDEX.md`, and creates:

```text
output/zip/Mountain_Retreat_X1_Professional_Documentation_Package.zip
```

## Example Commands

```bash
mrx1 validate
mrx1 generate markdown --lang sr-Latn
mrx1 generate markdown --lang en --large
mrx1 generate drawings
mrx1 generate pdf
mrx1 generate excel
mrx1 generate excel --bom --large
mrx1 generate excel --cost
mrx1 generate excel --gantt
mrx1 generate excel --qa --large
mrx1 generate excel --maintenance
mrx1 generate all --lang sr-Latn
mrx1 generate all --lang sr-Latn --large --clean
mrx1 generate all --variant standard_hybrid
mrx1 generate all --variant premium_clt
mrx1 generate all --variant masonry_hybrid
```

All generation commands accept `--output` or `--output-dir`. `mrx1 generate excel`
with no workbook selector generates all Excel workbooks; selectors such as `--bom`
or `--cost` limit the command to specific workbooks.

## Generated Outputs

The build pipeline creates:

- `output/markdown/`: Markdown source volumes
- `output/pdf/`: PDF documentation volumes
- `output/excel/`: BOM, cost estimate, Gantt, QA/QC, and maintenance workbooks
- `output/drawings/`: schematic SVG drawings
- `output/INDEX.md`: package index
- `output/ASSUMPTIONS_SUMMARY.md`: key YAML and calculated assumptions
- `output/BUILD_MANIFEST.json`: generated package manifest
- `output/zip/`: final professional documentation ZIP package

Large mode expands the planning binder with deeper room data sheets, 300+ self-build steps, 1000+ QA/QC rows, a 30-year maintenance calendar, expanded BOM line items, and construction management registers.

## Editing YAML Assumptions

Project assumptions live in `config/*.yaml`. Edit YAML files first, then regenerate outputs.

Important files:

- `config/project.yaml`: project name, version, language, disclaimer, review requirements
- `config/site.yaml`: climate, altitude, slope, soil, snow/wind/seismic placeholders
- `config/building.yaml`: area, footprint, roof, facade, construction variant
- `config/rooms_ground_floor.yaml` and `config/rooms_gallery.yaml`: room data sheets
- `config/terrace.yaml`: terrace zones and utility assumptions
- `config/materials_core.yaml` and `config/materials_mep.yaml`: BOM seed items
- `config/cost_assumptions_serbia_2026.yaml`: static planning prices and warnings
- `config/variants/*.yaml`: construction variant assumptions, risks, BOM rows, and cost rows

After edits:

```bash
mrx1 validate
mrx1 generate all --project config/project.yaml --output output --lang sr-Latn --large --clean
```

## Construction Variants

The default construction variant is `standard_hybrid`. The final pipeline can
generate the same package for each supported preliminary variant:

```bash
mrx1 generate all --variant standard_hybrid
mrx1 generate all --variant premium_clt
mrx1 generate all --variant masonry_hybrid
```

Variant files live under `config/variants/` and affect structural concept text,
active structural quantity calculations, BOM rows, cost rows, self-build warnings,
procurement complexity, and construction-management risk registers. Variant
comparison appears in the Project Charter. No variant is claimed to be
structurally approved.

## Localization

Default visible output language is Serbian Latin (`sr-Latn`). English (`en`) is also supported. Filenames remain English for compatibility.

```bash
mrx1 generate all --lang sr-Latn
mrx1 generate all --lang en
```

Package-level files, PDF source regeneration, workbook safety assumptions, and
manifest warnings use the requested language where supported. Technical file
names and internal codes remain stable.

## Deterministic Builds

Generated manifests use the project revision date as the build timestamp, and ZIP
entries use stable metadata. Static price assumptions, scenario factors,
contingency sensitivity rates, and off-grid add-ons are stored in YAML rather
than scraped or hidden in live lookups.

## Project Limitations

Mountain Retreat X1 does not replace:

- licensed architects
- licensed structural engineers
- licensed electrical engineers
- licensed mechanical or plumbing engineers
- fire-safety professionals
- geotechnical engineers
- surveyors
- contractors and cost estimators
- utility providers
- local permitting authorities

The system must not generate fake permits, fake stamps, fake signatures, fake signed calculations, legally binding approvals, or claims that documents are approved for construction.

## Professional Review Requirements

Before any real-world use, generated materials must be reviewed, corrected, and replaced as needed by appropriately licensed professionals and local authorities. This applies especially to structural design, foundations, terrace structure, snow/wind/seismic design, electrical systems, HVAC, plumbing, wastewater, fire safety, off-grid systems, and code/permitting requirements.

## Development QA

```bash
pytest
ruff check .
mypy src
mrx1 validate
mrx1 generate all --lang sr-Latn
mrx1 generate all --lang sr-Latn --large
```

## Agent Guidance

Future Codex and coding-agent tasks must follow [AGENTS.md](AGENTS.md). It defines the project mission, safety limits, testing expectations, generated-output rules, pricing policy, assumption handling, Serbian localization rules, and required commit/push workflow.
