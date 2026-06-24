# Release Notes

## v1.0.0

Mountain Retreat X1 is ready as a preliminary planning documentation generator.

### Added

- Final build pipeline via `mrx1 generate all`
- `--project`, `--output`, `--lang`, `--large`, and `--clean` support for final builds
- `BUILD_MANIFEST.json`, `INDEX.md`, and `ASSUMPTIONS_SUMMARY.md`
- Final ZIP package assembly
- Markdown documentation volumes
- PDF documentation volumes
- Excel BOM, cost estimate, Gantt schedule, QA/QC checklist, and maintenance calendar
- SVG schematic drawings
- Serbian Latin and English localization support
- Large document mode with expanded room sheets, QA/QC rows, self-build guide, BOM, maintenance planning, and construction-management registers
- Integration tests for final ZIP and manifest generation

### QA Status

Final QA command set:

- `pytest`
- `ruff check .`
- `mypy src`
- `mrx1 validate`
- `mrx1 generate all --lang sr-Latn`
- `mrx1 generate all --lang sr-Latn --large`

### Professional Limits

All generated outputs remain preliminary planning documents only. They are not for construction, permitting, procurement, financing, or legal reliance. Licensed professionals and local authorities must review and replace generated planning materials before real-world use.

### Known Limitations

- PDF rendering uses fallbacks when WeasyPrint is not installed.
- SVG drawings are schematic, not CAD.
- Costs are static YAML assumptions, not live market quotes.
- Engineering values are placeholders and are not final calculations.
- Localization currently supports Serbian Latin and English.
