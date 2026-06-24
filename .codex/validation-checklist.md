# Validation Checklist

Use this checklist before considering any implementation phase complete.

## Planning Safety

- [ ] No generated artifact claims permit approval.
- [ ] No generated artifact claims construction approval.
- [ ] No generated artifact includes fake stamps, seals, or signatures.
- [ ] No generated artifact claims signed engineering calculations.
- [ ] No live price scraping is used.
- [ ] Assumptions are stored in YAML.
- [ ] Assumptions are surfaced in generated outputs.

## Tooling

- [ ] Python target is 3.12.
- [ ] Pydantic validates structured inputs.
- [ ] Typer exposes CLI commands.
- [ ] Jinja2 renders text templates.
- [ ] OpenPyXL writes Excel workbooks.
- [ ] PDF engine is selected and isolated.
- [ ] SVG generation uses plain SVG.
- [ ] pytest covers core generation.
- [ ] ruff passes.
- [ ] mypy runs where practical.

## Artifacts

- [ ] Markdown outputs exist.
- [ ] SVG outputs exist.
- [ ] Excel outputs exist.
- [ ] PDF outputs exist.
- [ ] source YAML is copied into the final package.
- [ ] manifest exists.
- [ ] final ZIP exists.

## Git Workflow

- [ ] Changed files are staged.
- [ ] Commit is created with a concise message.
- [ ] Commit is pushed to the configured remote.

