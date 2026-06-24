# Codex Project Brief

## Project

Mountain Retreat X1 is a Python-based documentation generation system for preliminary planning of a modern mountain cabin with a large panoramic terrace.

## Goal

Generate a complete preliminary planning package from YAML assumptions and Markdown/Jinja source material.

The future system must produce:

- PDF documentation volumes
- Excel bill of materials
- Excel cost estimate
- Excel Gantt schedule
- Excel QA/QC checklists
- SVG schematic drawings
- Markdown source documents
- YAML configuration files
- final ZIP package

## Philosophy

This project helps organize planning information. It does not replace licensed design professionals or local authorities.

Every output must be visibly marked as preliminary and must surface assumptions from YAML.

## Technical Constraints

- Python 3.12
- Pydantic for schemas
- Typer for CLI
- Jinja2 for templates
- WeasyPrint or ReportLab for PDFs
- OpenPyXL for Excel workbooks
- plain SVG generation for schematic drawings
- pytest for tests
- ruff for linting
- mypy where practical

## Current Repository State

The repository is in planning/scaffolding mode. Do not add implementation code until explicitly requested.

