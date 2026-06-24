# Architecture

Mountain Retreat X1 follows a deterministic document-generation pipeline.

## Pipeline

1. Load YAML configuration from `config/`.
2. Validate structured data with Pydantic models.
3. Normalize assumptions and project metadata.
4. Render Markdown and template-driven source documents.
5. Generate plain SVG schematic drawings.
6. Export Excel workbooks with OpenPyXL.
7. Render PDF volumes.
8. Assemble a final ZIP package.

## Package Areas

- `cli`: Typer command surface
- `config`: configuration loading and settings
- `models`: Pydantic domain models
- `calculators`: deterministic quantity, cost, and schedule calculations
- `generators`: artifact-specific orchestration
- `exporters`: file format writers
- `renderers`: template and PDF rendering support
- `localization`: future locale and language helpers
- `validation`: safety and data validation

Generated content must remain preliminary and auditable.

