# Mountain Retreat X1

Mountain Retreat X1 is a Python 3.12 documentation-generation system for preliminary planning of a modern mountain cabin with a large panoramic terrace.

The project is designed to generate a coordinated planning package from structured YAML assumptions and templates:

- PDF documentation volumes
- Excel bill of materials
- Excel cost estimate
- Excel Gantt schedule
- Excel QA/QC checklists
- SVG schematic drawings
- Markdown source documents
- YAML configuration files
- final ZIP package

## Professional Limits

Mountain Retreat X1 does not replace licensed architects, structural engineers, electrical engineers, mechanical engineers, contractors, cost estimators, surveyors, code consultants, or local permitting authorities.

All generated materials must be treated as preliminary planning documents only. They are not for construction, permitting, procurement, financing, legal reliance, or professional approval.

The system must not generate:

- fake legal permits
- fake signed or sealed engineering calculations
- fake professional stamps
- legally binding construction approvals
- claims that drawings are approved for construction

All assumptions must be stored in YAML and surfaced in generated documents.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
mrx1 --help
pytest
ruff check .
```

## CLI

Placeholder commands are available while the repository structure is being established:

```bash
mrx1 validate
mrx1 generate all
mrx1 generate pdf
mrx1 generate excel
mrx1 generate drawings
mrx1 clean
```

## Repository Layout

```text
config/                  YAML project configuration and examples
data/                    static catalogs and localization data
docs/                    architecture, limits, templates, and volume docs
output/                  generated artifacts, ignored by Git
src/mountain_retreat_x1/ Python package
tests/                   unit and integration tests
.codex/                  Codex project context
```

## Agent Guidance

Future Codex and coding-agent tasks must follow [AGENTS.md](AGENTS.md). That file defines the project mission, safety limits, testing expectations, generated-output rules, pricing policy, assumption handling, Serbian localization rules, and required commit/push workflow.

## Status

This is an initial production-grade scaffold. The CLI commands are placeholders and intentionally do not yet generate construction documentation.
