# Roadmap

## v1.0.0 Ready

- Python 3.12 package with Typer CLI
- Pydantic model layer and YAML config loader
- Serbian Latin and English localization
- deterministic calculators for areas, quantities, and costs
- Markdown volume generation
- PDF volume generation with fallbacks
- SVG schematic drawing generation
- Excel BOM, cost estimate, Gantt, QA/QC, and maintenance calendar generation
- large document mode
- final build manifest, index, assumptions summary, and ZIP package
- pytest, Ruff, and mypy QA gates

## Near-Term Hardening

- Add stricter safety-language checks across generated files.
- Add optional schema export for YAML editors.
- Add more localized Serbian Latin visible text in tables and specialized package bodies.
- Add checksum support to `BUILD_MANIFEST.json`.
- Add generated artifact snapshot tests for stable high-value outputs.

## Future Enhancements

- Better PDF table of contents when full WeasyPrint support is installed.
- Optional richer SVG drawing layouts.
- More detailed cost scenarios, still using static YAML assumptions only.
- More granular maintenance calendar exports.
- Additional localization files if project scope requires them.

## Non-Goals

- No fake permits.
- No fake stamps or signatures.
- No final structural calculations.
- No live price scraping.
- No claims of construction, code, or permitting approval.
