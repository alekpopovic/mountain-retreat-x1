# AGENTS.md

This file is the operating contract for Codex and any future coding agents working on Mountain Retreat X1.

Agents must read this file before making repository changes. When this file conflicts with older planning notes, this file wins.

## 1. Project Mission

Mountain Retreat X1 is a Python 3.12 system for generating preliminary planning documentation for a modern mountain cabin with a large panoramic terrace.

The system exists to organize planning assumptions, calculations, schedules, checklists, drawings, PDFs, spreadsheets, and ZIP packages. It must help users prepare for professional review without pretending to replace that review.

Primary outputs:

- PDF documentation volumes
- Excel bill of materials
- Excel cost estimate
- Excel Gantt schedule
- Excel QA/QC checklists
- SVG schematic drawings
- Markdown source documents
- YAML configuration files
- final ZIP package

## 2. Safety and Professional Limits

Mandatory rules:

- Never claim generated documents are legally approved.
- Never claim generated documents are approved for construction.
- Never claim generated structural calculations are final.
- Never generate stamped or signed engineering documents.
- Never generate fake permits, fake approvals, fake seals, or fake professional certifications.
- Always mark generated documents as preliminary.
- Always require review by appropriately licensed professionals and local authorities before real-world use.

Generated documents must clearly state that they are:

- preliminary planning documents
- not for construction
- not for permitting
- not for procurement reliance
- not legal advice
- not engineering approval
- not architectural approval

## 3. Code Style

Use the existing Python package structure and keep code simple, typed, and deterministic.

Required tooling and patterns:

- Python 3.12
- Typer for CLI commands
- Pydantic and pydantic-settings for schemas/settings
- Jinja2 for templates
- OpenPyXL for Excel files
- plain SVG generation for schematic drawings
- Rich for CLI output where useful
- pytest for tests
- ruff for linting
- mypy where practical

Code rules:

- Prefer explicit data models over unstructured dictionaries.
- Keep calculations out of templates.
- Do not hard-code quantities in templates if they can be calculated.
- Keep generators deterministic from config/data inputs.
- Keep public functions reasonably typed.
- Do not add broad abstractions before they remove real duplication or clarify a real boundary.

## 4. Testing Rules

Every generator must have tests.

Every public CLI command must have at least one smoke test.

Tests should cover:

- config loading
- schema validation
- assumption propagation
- safety disclaimers
- forbidden claims
- Markdown generation
- SVG generation
- Excel workbook structure and formulas
- PDF smoke generation
- ZIP package contents
- CLI behavior

Before finishing a coding task, run the most relevant checks. For broad changes, run:

```bash
pytest
ruff check .
mypy src
```

If a check cannot run, explain why in the final response.

## 5. Documentation Rules

Documentation must be accurate, useful, and honest about limits.

Do:

- document assumptions and where they come from
- document generated artifact purpose and limitations
- document CLI behavior
- document configuration fields when adding schemas
- update README or architecture docs when behavior changes

Do not:

- create meaningless filler just to increase page count
- make generated documents look more authoritative than they are
- bury disclaimers in obscure appendices only
- describe unimplemented features as complete

Large document mode must expand useful content only, such as:

- checklists
- room data sheets
- maintenance schedules
- step-by-step procedures
- inspection prompts
- assumption tables
- revision history
- professional review matrices

## 6. Generated Output Rules

All generated outputs must be deterministic and traceable to repository inputs.

Generated documents must include:

- preliminary-document disclaimer
- assumptions or references to assumptions
- revision history where the format supports it
- page numbers for PDFs
- clear generated date/version metadata

PDF requirements:

- include disclaimers
- include revision history
- include page numbers
- avoid fake stamps, seals, signatures, and permit marks

Excel requirements:

- include formulas where appropriate
- include assumptions sheets where practical
- include source notes for quantities and rates
- avoid hiding important calculations as static unexplained numbers

Quantity requirements:

- generated quantities must include formula notes or assumption references
- calculated quantities should be reproducible from config and catalog data
- template text must not invent quantities

SVG drawing requirements:

- mark drawings as schematic/preliminary
- mark drawings as not for construction
- avoid professional stamps, seals, signatures, or approval blocks
- label approximate dimensions as approximate

## 7. Construction and Engineering Limitations

Mountain Retreat X1 may generate planning aids, but must not generate final professional work products.

The system must not claim to provide:

- final structural design
- final structural calculations
- final load paths
- final foundation design
- code compliance certification
- electrical engineering approval
- mechanical engineering approval
- architectural approval
- permit approval
- construction authorization

Any structural, envelope, terrace, electrical, mechanical, plumbing, fire, snow-load, wind-load, slope, drainage, geotechnical, or jurisdictional content must be framed as preliminary and subject to licensed review.

## 8. File Organization

Use this repository layout:

```text
config/                  YAML project configuration and examples
data/catalogs/           static catalogs; no scraped live prices
data/localization/       localization resources
docs/                    repository and generated-document planning docs
docs/volumes/            volume planning notes
docs/templates/          document template notes
docs/legal/              legal/professional-limit notes
output/                  generated artifacts; do not commit generated files
src/mountain_retreat_x1/ Python package
tests/                   unit and integration tests
.codex/                  Codex context files
```

Generated files belong under `output/` and should remain ignored unless the user explicitly asks to commit a generated sample.

## 9. Commit and Diff Summary Expectations

After every user prompt that changes repository files, run:

1. `git add` for changed files
2. `git commit` with a concise message
3. `git push`

If push is not possible because no remote is configured, network access fails, or authentication is unavailable, report the blocker clearly.

Final responses after repository changes should include:

- what changed
- which checks ran
- any checks that could not run
- commit hash
- push status

Do not hide uncommitted changes.

## 10. How to Handle Assumptions

Always store assumptions in config files, preferably YAML under `config/`.

Do not hard-code project assumptions in:

- templates
- generators
- renderers
- tests, except as local test fixtures
- documentation output logic

Generated outputs must surface assumptions in human-readable form.

When adding a new calculation or generated section:

- identify required assumptions
- add or extend config schema
- validate required values
- include assumption references in generated output
- add tests proving assumptions are propagated

## 11. How to Handle Prices

Do not scrape live prices.

Do not imply static prices are current market quotes.

Cost data must come from:

- YAML config
- static catalogs committed under `data/catalogs/`
- explicit user-provided inputs

Cost outputs must include:

- currency
- rate source note
- date or version of the assumption set
- contingency assumptions where used
- exclusions
- warning that estimates are preliminary planning estimates

When generating Excel cost estimates, include formulas where appropriate and keep line-item math visible.

## 12. How to Handle Serbian Localization

The project may support Serbian localization for generated documents and CLI/user-facing text.

Rules:

- Store localization strings under `data/localization/` or a dedicated localization config file.
- Do not hard-code Serbian translations inside generators or templates when a localization layer exists.
- Preserve professional-limit disclaimers in Serbian outputs.
- Serbian text must not soften or remove legal/professional warnings.
- Prefer clear Serbian wording over literal translation when safety meaning is better preserved.
- If both Serbian Latin and Serbian Cyrillic are supported, keep them as explicit locale variants.
- Tests should verify that localized outputs still include preliminary-document warnings.

Suggested locale identifiers:

- `sr-Latn-RS`
- `sr-Cyrl-RS`

## Codex Context Files

Before substantial future work, review the files in `.codex/`, especially:

- `.codex/project-brief.md`
- `.codex/safety-rules.md`
- `.codex/implementation-roadmap.md`
- `.codex/repository-contract.md`
- `.codex/validation-checklist.md`
- `.codex/output-manifest.md`
- `.codex/git-workflow.md`

