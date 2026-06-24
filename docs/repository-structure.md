# Repository Structure

The planned implementation structure is:

```text
mountain-retreat-x1/
├── pyproject.toml
├── README.md
├── AGENTS.md
├── IMPLEMENTATION_PLAN.md
├── .gitignore
│
├── src/
│   └── mountain_retreat_x1/
│       ├── __init__.py
│       ├── cli.py
│       ├── config/
│       ├── schemas/
│       ├── documents/
│       ├── generators/
│       ├── templates/
│       └── utils/
│
├── config/
│   ├── project.yaml
│   ├── assumptions.yaml
│   ├── spaces.yaml
│   ├── materials.yaml
│   ├── cost_rates.yaml
│   ├── schedule.yaml
│   ├── checklists.yaml
│   └── drawing_settings.yaml
│
├── docs/
│   ├── repository-structure.md
│   ├── testing-strategy.md
│   ├── risk-register.md
│   ├── phase-deliverables.md
│   └── generation-safety.md
│
├── docs_src/
│   ├── overview.md
│   ├── design_intent.md
│   ├── construction_notes.md
│   ├── safety_notes.md
│   └── review_requirements.md
│
├── output/
│   └── .gitkeep
│
├── tests/
│   └── .gitkeep
│
└── examples/
    └── mountain_cabin_sample/
```

During the planning phase, source package directories may exist only as placeholders. Python implementation files should be added only after planning approval.

