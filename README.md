# Mountain Retreat X1

Mountain Retreat X1 is a planned Python-based documentation generation system for a modern mountain cabin with a large panoramic terrace.

The project will generate preliminary planning artifacts including PDF documentation volumes, Excel workbooks, SVG schematic drawings, Markdown source documents, YAML configuration files, construction checklists, a Gantt schedule, cost estimates, and a final ZIP package.

## Safety Position

This repository must never present generated materials as construction-ready, legally binding, permitted, signed, sealed, or professionally approved documents.

All generated artifacts must be clearly marked as:

- preliminary planning documents
- schematic and approximate where applicable
- subject to review by licensed architects, structural engineers, electrical engineers, mechanical engineers, and local permitting authorities

The system must not:

- scrape live prices
- generate fake legal permits
- generate fake signed engineering calculations
- invent legally binding construction approvals
- imply that drawings are approved for construction

## Current Status

This repository is initialized as a planning-first Codex project. No implementation code has been written yet.

Start with:

- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- [docs/repository-structure.md](docs/repository-structure.md)
- [docs/testing-strategy.md](docs/testing-strategy.md)
- [docs/risk-register.md](docs/risk-register.md)
- [docs/generation-safety.md](docs/generation-safety.md)

## Planned Technology

- Python 3.12
- Pydantic for schemas
- Typer for CLI
- Jinja2 for templates
- WeasyPrint or ReportLab for PDFs
- OpenPyXL for Excel files
- plain SVG generation for schematic drawings
- pytest for tests
- ruff for linting
- mypy where practical

