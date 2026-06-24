# Repository Contract

## Source of Truth

YAML files in `config/` are the source of truth for assumptions, project metadata, placeholder rates, spaces, materials, schedule inputs, checklist sections, and drawing settings.

Markdown source files in `docs_src/` provide human-authored narrative inputs.

Generated files belong under `output/` and should not be committed except for `.gitkeep`, unless explicitly requested.

## Planned Package Layout

Future implementation code should live under:

```text
src/mountain_retreat_x1/
```

Planned subpackages:

- `config/`
- `schemas/`
- `documents/`
- `generators/`
- `templates/`
- `utils/`

Tests should live under:

```text
tests/
```

## CLI Contract

Future Typer commands should include:

- `validate`
- `generate markdown`
- `generate svg`
- `generate excel`
- `generate pdf`
- `generate all`
- `package`
- `clean`

## Generated Artifact Contract

All generated artifacts must be deterministic from repository inputs and must include visible preliminary-document limitations wherever technically practical.

