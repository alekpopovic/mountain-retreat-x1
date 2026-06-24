# Codex Implementation Roadmap

## Stage 0: Planning and Scaffolding

Status: active.

Allowed:

- documentation
- planning files
- YAML placeholder assumptions
- repository metadata
- empty directories
- Codex instruction files

Not allowed unless explicitly requested:

- application Python code
- template rendering code
- generators
- tests that imply implementation already exists

## Stage 1: Configuration and Schemas

When approved, implement:

- Pydantic schema models
- YAML loader
- validation command
- assumption normalization
- manifest generation

Expected outputs:

- `output/manifest.json`
- `output/markdown/00_assumptions.md`

## Stage 2: Markdown Generation

When approved, implement:

- Jinja2 Markdown templates
- Markdown rendering command
- disclaimer enforcement
- assumption injection

Expected outputs:

- project overview
- design intent
- preliminary scope
- materials summary
- construction sequence
- review requirements
- limitations and disclaimers

## Stage 3: SVG Generation

When approved, implement:

- plain SVG helpers
- schematic floor plan
- terrace layout
- site orientation
- roof concept
- section concept
- envelope concept

Each SVG must be labeled schematic and not for construction.

## Stage 4: Excel Generation

When approved, implement:

- BOM workbook
- cost estimate workbook
- Gantt schedule workbook
- QA/QC checklist workbook

Every workbook must include assumptions and limitations.

## Stage 5: PDF Generation

When approved, implement PDF generation with either WeasyPrint or ReportLab.

Expected volumes:

- project brief
- design and scope
- materials and BOM
- cost estimate
- schedule
- QA/QC checklists
- drawings appendix

## Stage 6: Packaging

When approved, implement:

- package directory assembly
- source YAML copy
- package README
- manifest
- final ZIP

## Stage 7: Quality Gate

When approved, enforce:

- pytest
- ruff
- mypy where practical
- forbidden-language scans
- artifact completeness checks
- assumption propagation checks

