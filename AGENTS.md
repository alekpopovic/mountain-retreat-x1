# Codex Project Guidance

This repository is for Mountain Retreat X1, a preliminary planning-document generation system.

## Current Constraint

Do not write implementation code until the planning phase is explicitly complete and approved.

Planning artifacts, configuration templates, repository documentation, empty directories, and tooling metadata are allowed.

## Codex Context Files

Before substantial future work, review the files in `.codex/`, especially:

- `.codex/project-brief.md`
- `.codex/safety-rules.md`
- `.codex/implementation-roadmap.md`
- `.codex/repository-contract.md`
- `.codex/validation-checklist.md`
- `.codex/output-manifest.md`
- `.codex/git-workflow.md`

## Required Git Workflow

After every user prompt that results in repository changes, run:

1. `git add` for the changed files
2. `git commit` with a concise message
3. `git push`

If push is not possible because no remote is configured or authentication is unavailable, report that clearly in the final response.

## Non-Negotiable Safety Rules

Generated documents must never claim to be:

- permits
- signed or sealed engineering calculations
- construction-ready drawings
- code-compliance certifications
- legal approvals
- replacements for licensed professional review

Every generated artifact must surface the project assumptions and include preliminary-document disclaimers.

## Implementation Preferences

When coding begins:

- use Python 3.12
- keep structured data in YAML
- validate inputs with Pydantic
- expose operations through Typer
- render text documents with Jinja2 templates
- generate Excel files with OpenPyXL
- generate drawings as plain SVG
- use pytest, ruff, and mypy where practical

Keep the system deterministic and auditable. Do not use live price scraping.
