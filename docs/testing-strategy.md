# Testing Strategy

Testing should focus on correctness, repeatability, and document-safety guarantees.

## Test Categories

### Configuration Tests

- YAML files load successfully.
- Required fields are present.
- Pydantic validation rejects malformed data.
- Assumptions are explicit.
- Professional review requirements are present.

### Disclaimer Tests

- Every generated Markdown file includes preliminary-document language.
- Every generated SVG includes not-for-construction language.
- Every Excel workbook contains an assumptions or limitations sheet.
- Every PDF volume includes a disclaimer section where text extraction is practical.

### Forbidden-Language Tests

Generated text artifacts must not include misleading phrases such as:

- approved for construction
- building permit issued
- sealed engineering calculation
- licensed approval
- code-compliant certification
- authorized construction documents
- permit-ready drawings

### Excel Tests

- Required workbooks are generated.
- Required sheets exist.
- Headers are stable.
- Assumptions are included.
- Cost rates come only from YAML data.

### SVG Tests

- SVG files parse as XML.
- Title blocks are present.
- Schematic labels are present.
- Approximate dimensions are labeled appropriately.
- No seal, stamp, permit, or approval language appears.

### PDF Tests

- Expected PDF files are generated.
- Files are non-empty.
- Disclaimer text is included where extraction tooling is stable.
- PDF generation failures are surfaced clearly.

### ZIP Package Tests

- Final ZIP exists.
- Required folders are present.
- Source YAML is included.
- Manifest is included.
- Package README includes limitations and review requirements.

### CLI Tests

- `validate` command succeeds on sample config.
- generation commands produce expected file groups.
- invalid config returns a non-zero exit code.
- output directory can be overridden.

## Tooling

Planned tooling:

- pytest for tests
- ruff for linting
- mypy where practical

